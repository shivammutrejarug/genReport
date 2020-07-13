import argparse
from pylatex import Document, Section, Subsection, Package, Command, Enumerate, Tabular
from pylatex.utils import escape_latex, NoEscape, bold
import utils
import os
from parser import JiraParser
from typing import Tuple, List
import re


def __parse_arguments():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-g", "--github", help="Target Jira project's GitHub repository")


class ReportGenerator:
    def __init__(self, project: str, issue: str, github_repository: str = None, bots: List[str] = None):
        self.project = project
        self.issue = issue
        self.github_repository = github_repository
        self.bots = bots
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

    def __setup_preamble(self):
        preamble = self.doc.preamble
        issue = self.data[0]
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
            # comment["body"] = re.sub(r"[\r\n]+]", "\n", comment["body"])
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
                # comment["body"] = re.sub(r"[\r\n]+]", "\n", comment["body"])
                comment["body"] = comment["body"].replace('\r', '\n')

        return issue, connected_issues

    @staticmethod
    def __hyperlink(url, description):
        description = escape_latex(description)
        return NoEscape(r"\href{" + url + "}{" + description + "}")

    def __describe_connected_issue(self, issue: dict, index: int) -> None:
        doc = self.doc
        with doc.create(Section("Connected issue {}: {}".format(index, issue["issue_key"]))):
            with doc.create(Subsection("Issue key")):
                doc.append(issue["issue_key"])

            with doc.create(Subsection("Summary")):
                doc.append(issue["summary"])

            with doc.create(Subsection("Description")):
                doc.append(issue["description"])

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
                enum.add_item(bold(comment["author"] + ": ") + escape_latex(comment["body"]))

    def generate_report(self):
        doc = self.doc
        issue, connected_issues = self.data
        doc.append(NoEscape(r"\maketitle"))

        with doc.create(Section("Summary")):
            doc.append(escape_latex(issue["summary"]))

        with doc.create(Section("Description")):
            description = utils.atlassian_code_format_to_listing(issue["description"])
            doc.append(escape_latex(description))

        with doc.create(Section("Attachments")):
            with doc.create(Enumerate()) as enum:
                for attachment in issue["attachments"]:
                    enum.add_item(self.__hyperlink(attachment["content"], attachment["filename"]))

        with doc.create(Section("Comments")):
            self.__add_comments(issue)

        for index, issue in enumerate(connected_issues, start=1):
            self.__describe_connected_issue(issue, index)

        doc.generate_pdf(issue["issue_key"], clean_tex=True)
