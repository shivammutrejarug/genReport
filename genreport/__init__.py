from argparse import ArgumentParser
from pylatex import Document, Section, Subsection, Package, Command, Enumerate, Tabular
from pylatex.utils import escape_latex, NoEscape, bold
import utils
import os
from parser import JiraParser
from typing import Tuple, List
import re


def __parse_arguments() -> ArgumentParser:
    arg_parser = ArgumentParser()
    arg_parser.add_argument("-g", "--github", help="Target Jira project's GitHub repository")
    arg_parser.add_argument("-b", "--bots", help="List of bots to exclude from report, separated by comma")
    arg_parser.add_argument("-i", "--issues", help="Issues to generate reports for, separated by comma and/or"
                                                   "defined as ranges. For example, \"124,136-152,174\"")
    arg_parser.add_argument("-e", "--exclude", help="Sections to skip when generating report, separated by comma."
                                                    "Sections are: [summary, description, attachments,"
                                                    "comments, other_issues]")
    return arg_parser


class ReportGenerator:
    def __init__(self, project: str, issue: str, github_repository: str = None, bots: List[str] = None,
                 exclude: List[str] = None):
        self.project = project
        self.issue = issue
        self.github_repository = github_repository
        self.bots = bots
        self.exclude = exclude

        self.data = self.__load_issue()

        self.doc = Document(document_options="article")
        self.__setup_packages()
        self.__setup_preamble()

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
        preamble.append(NoEscape(r"\lstset{tabsize = 4,"
                                 r"showstringspaces = false,"
                                 r"numbers = left,"
                                 r"commentstyle = \color{darkgreen} \ttfamily,"
                                 r"keywordstyle = \color{blue} \ttfamily,"
                                 r"stringstyle = \color{red} \ttfamily,"
                                 r"rulecolor = \color{black} \ttfamily,"
                                 r"basicstyle = \footnotesize \ttfamily,"
                                 r"frame = single,"
                                 r"breaklines = true,"
                                 r"numberstyle = \tiny}"))
        preamble.append(NoEscape(r"\definecolor{darkgreen}{rgb}{0,0.6,0}"))

    def __load_issue(self) -> Tuple[dict, List[dict]]:
        parser = JiraParser(self.project)
        issue = parser.load_issue(self.issue)
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

    @staticmethod
    def __hyperlink(url, description):
        description = escape_latex(description)
        return NoEscape(r"\href{" + url + "}{" + description + "}")

    @staticmethod
    def define_issues(issues_arg: str) -> List[str]:
        issues = []
        for issues_entry in issues_arg.split(','):
            if issues_entry.isdecimal():  # If it is a single issue
                issues.append(issues_entry)
            else:
                issues_range = issues_entry.split('-')
                if len(issues_range) != 2 or not issues_range[0].isdecimal() or not issues_range[1].isdecimal():
                    print("Invalid issues list format")
                    return []

                first_issue = int(issues_range[0])
                last_issue = int(issues_range[1])
                if last_issue < first_issue:
                    print("The range should be from smaller to bigger")
                    return []

                for issue in range(first_issue, last_issue + 1):
                    issues.append(issue)
        return issues

    def __describe_connected_issue(self, issue: dict, index: int) -> None:
        doc = self.doc
        with doc.create(Section("Connected issue {}: {}".format(index, issue["issue_key"]))):
            with doc.create(Subsection("Issue key")):
                doc.append(issue["issue_key"])

            with doc.create(Subsection("Summary")):
                summary = utils.escape_with_listings(issue["summary"])
                doc.append(summary)

            with doc.create(Subsection("Description")):
                description = utils.escape_with_listings(issue["summary"])
                doc.append(description)

            with doc.create(Subsection("Attachments")):
                with doc.create(Enumerate()) as enum:
                    for attachment in issue["attachments"]:
                        enum.add_item(self.__hyperlink(attachment["content"], attachment["filename"]))

            with doc.create(Subsection("Comments")):
                self.__add_comments(issue)

    def __add_comments(self, issue):
        doc = self.doc
        with doc.create(Enumerate()) as enum:
            for comment in issue["comments"]:
                comment_body = utils.escape_with_listings(comment["body"])
                enum.add_item(bold(comment["author"] + ": ") + comment_body)

    def generate_report(self):
        doc = self.doc
        issue, connected_issues = self.data
        filename = issue["issue_key"]
        doc.append(NoEscape(r"\maketitle"))

        with doc.create(Section("Summary")):
            summary = utils.escape_with_listings(issue["summary"])
            doc.append(summary)

        with doc.create(Section("Description")):
            description = utils.escape_with_listings(issue["summary"])
            doc.append(description)

        with doc.create(Section("Attachments")):
            with doc.create(Enumerate()) as enum:
                for attachment in issue["attachments"]:
                    enum.add_item(self.__hyperlink(attachment["content"], attachment["filename"]))

        with doc.create(Section("Comments")):
            self.__add_comments(issue)

        for index, issue in enumerate(connected_issues, start=1):
            self.__describe_connected_issue(issue, index)

        doc.generate_pdf(filename, clean_tex=True)
