from argparse import ArgumentParser
from pylatex import Document, Package, Command, Enumerate, Tabular
from pylatex.section import Chapter, Section
from pylatex.utils import escape_latex, NoEscape, bold
import os
import utils
from github_fetcher import GitHubFetcher
from jira_parser import JiraParser
from typing import Tuple, List


class ReportGenerator:
    def __init__(self, project: str, issue_key: str, github_repository: str = None, bots: List[str] = None,
                 exclude: List[str] = None):
        self.project = project
        self.issue_key = issue_key
        self.github_repository = github_repository

        if bots:
            self.bots = bots
        else:
            self.bots = []

        if exclude:
            self.exclude = exclude
        else:
            self.exclude = []

        self.data = self.__load_issue()
        self.commits = None
        if self.github_repository:
            self.commits = self.__load_commits()

        self.doc = Document(documentclass="report")
        self.__setup_packages()
        self.__setup_preamble()

    @staticmethod
    def __hyperlink(url, description):
        description = escape_latex(description)
        return NoEscape(r"\href{" + url + "}{" + description + "}")

    def __load_issue(self) -> Tuple[dict, List[dict]]:
        parser = JiraParser(self.project)
        issue = parser.load_issue(self.issue_key)
        issue["comments"] = list(
            filter(
                lambda comment: not comment["author"] in self.bots,
                issue["comments"]
            )
        )
        for comment in issue["comments"]:
            comment["body"] = comment["body"].replace('\r', '\n')

        connected_issues_keys = [connected_issue["issue_key"] for connected_issue in issue["issuelinks"]]
        connected_issues = [parser.load_issue(key) for key in connected_issues_keys]
        for connected_issue in connected_issues:
            connected_issue["comments"] = list(
                filter(
                    lambda comment: not comment["author"] in self.bots,
                    connected_issue["comments"]
                )
            )
            for comment in connected_issue["comments"]:
                comment["body"] = comment["body"].replace('\r', '\n')

        return issue, connected_issues

    def __load_commits(self):
        print("{}: loading commits".format(self.issue_key))
        issue, connected_issues = self.data
        issue_keys = [issue["issue_key"]] + [connected_issue["issue_key"] for connected_issue in connected_issues]

        fetcher = GitHubFetcher(self.project, self.github_repository.replace("https://github.com/", ""))
        commits = dict()
        for key in issue_keys:
            commits[key] = fetcher.get_commits(key)
        print("{}: successfully loaded commits".format(self.project))
        return commits

    def __setup_packages(self):
        packages = self.doc.packages
        packages.append(Package("a4wide"))
        packages.append(Package("listings"))
        packages.append(Package("xcolor"))
        packages.append(Package("courier"))
        packages.append(Package("tabularx"))
        packages.append(Package("hyperref"))
        packages.append(Package("spverbatim"))

    def __setup_preamble(self):
        preamble = self.doc.preamble
        issue = self.data[0]
        preamble.append(NoEscape(r"\UseRawInputEncoding"))
        preamble.append(Command("title", issue["issue_key"]))
        preamble.append(Command("author", issue["author"]))
        preamble.append(Command("date", issue["created"].split("T")[0]))
        preamble.append(Command("lstset", NoEscape("tabsize = 4,"
                                                   r"showstringspaces = false,"
                                                   r"numbers = left,"
                                                   r"commentstyle = \color{darkgreen} \ttfamily,"
                                                   r"keywordstyle = \color{blue} \ttfamily,"
                                                   r"stringstyle = \color{red} \ttfamily,"
                                                   r"rulecolor = \color{black} \ttfamily,"
                                                   r"basicstyle = \footnotesize \ttfamily,"
                                                   r"frame = single,"
                                                   r"breaklines = true,"
                                                   r"numberstyle = \tiny")))
        preamble.append(NoEscape(r"\definecolor{darkgreen}{rgb}{0,0.6,0}"))

    def __add_comments(self, issue):
        doc = self.doc
        with doc.create(Enumerate()) as enum:
            for comment in issue["comments"]:
                comment_body = utils.escape_with_listings(comment["body"])
                enum.add_item(bold(comment["author"] + ": ") + comment_body)

    def __describe_issue(self, issue, root_issue: bool = False):
        doc = self.doc
        chapter_title = ("Root issue " if root_issue else "Connected issue ") + issue["issue_key"]
        with doc.create(Chapter(chapter_title)):
            if "summary" not in self.exclude:
                with doc.create(Section("Summary")):
                    summary = utils.escape_with_listings(issue["summary"])
                    doc.append(summary)

            if "description" not in self.exclude:
                with doc.create(Section("Description")):
                    description = utils.escape_with_listings(issue["summary"])
                    doc.append(description)

            if "attachments" not in self.exclude:
                with doc.create(Section("Attachments")):
                    with doc.create(Enumerate()) as enum:
                        attachments = issue["attachments"]
                        if not attachments:
                            doc.append("No attachments")
                        else:
                            for attachment in issue["attachments"]:
                                enum.add_item(self.__hyperlink(attachment["content"], attachment["filename"]))

            if "commits" not in self.exclude:
                with doc.create(Section("Commits")):
                    commits = self.commits
                    if not commits:
                        doc.append("No related commits")
                    else:
                        with doc.create(Enumerate()) as enum:
                            for commit in commits[issue["issue_key"]]:
                                enum.add_item(NoEscape("Commit {} by {} ({}): {}".format(
                                    bold(commit["short_sha"]),
                                    bold(escape_latex(commit["author"])),
                                    escape_latex(commit["date"]),
                                    escape_latex(commit["message"])
                                )))
            if "comments" not in self.exclude:
                with doc.create(Section("Comments")):
                    self.__add_comments(issue)

    def generate_report(self):
        doc = self.doc
        issue, connected_issues = self.data
        filename = issue["issue_key"]
        doc.append(NoEscape(r"\maketitle"))

        self.__describe_issue(issue, root_issue=True)

        if "other_issues" not in self.exclude:
            for issue in connected_issues:
                self.__describe_issue(issue)

        doc.generate_pdf(filename, clean_tex=True)
        print("Report for {} is successfully created".format(filename))
