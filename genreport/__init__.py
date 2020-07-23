from pylatex import Document, Package, Command, Enumerate, Subsection
from pylatex.section import Chapter, Section
from pylatex.utils import escape_latex, NoEscape, bold
from github.GithubException import UnknownObjectException, BadCredentialsException
import os
import utils
from github_fetcher import GitHubFetcher
from jira_parser import JiraParser
from typing import Tuple, List


class ReportGenerator:
    def __init__(self, project: str, issue_key: str, github_repository: str = None,
                 github_credentials: Tuple[str, str] = None, bots: List[str] = None,
                 exclude: List[str] = None):
        self.project = project
        self.issue_key = issue_key
        self.github_repository = github_repository
        self.credentials = github_credentials

        if bots:
            self.bots = bots
        else:
            self.bots = []

        if exclude:
            self.exclude = exclude
        else:
            self.exclude = []

        self.data = self.__load_issue()
        self.commits, self.pull_requests = None, None
        if self.github_repository:
            try:
                self.commits = self.__load_commits()
                self.pull_requests = self.__load_pull_requests()
            except UnknownObjectException:
                print("Invalid GitHub repository. Aborting...")
                exit(-1)
            except BadCredentialsException:
                print("Invalid GitHub credentials. Aborting...")
                exit(-1)

        self.doc = Document(documentclass="report")
        self.__setup_packages()
        self.__setup_preamble()

    @staticmethod
    def __hyperlink(url, description):
        """
        Construct a LaTeX hyperref from the URL and its description provided.
        :param url: URL address
        :param description: URL description
        :return: Raw string representing hyperref
        """
        description = escape_latex(description)
        return NoEscape(r"\href{" + url + r"}{\underline{" + description + "}}")

    def __load_issue(self) -> Tuple[dict, List[dict]]:
        """
        Load the issue specified by the field "issue_key" and a list of connected issues. For each issue, comments
        left by bots are filtered out and all '\r' symbols are replaced with '\n' to prevent LaTeX errors of
        empty newlines.
        :return: Tuple representing:
            1. Issue specified by the field "issue_key"
            2. List of connected issues
        """
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

    def __load_commits(self) -> dict:
        """
        Load commits for the issue specified by the field "issue_key". Loaded commits represent
        a dictionary, where the key is an issue key and value is a list of related commits.
        :return: Dictionary of lists of commits accessible by an issue key
        """
        print("\t{}: loading commits".format(self.issue_key))
        issue, connected_issues = self.data
        issue_keys = [issue["issue_key"]] + [connected_issue["issue_key"] for connected_issue in connected_issues]

        fetcher = GitHubFetcher(self.project, self.github_repository.replace("https://github.com/", ""),
                                self.credentials)
        commits = dict()
        for key in issue_keys:
            commits[key] = fetcher.get_commits(key)
        print("\t{}: successfully loaded commits".format(self.issue_key))
        return commits

    def __load_pull_requests(self) -> dict:
        """
        Load pull requests for the issue specified by the field "issue_key". Loaded pull requests represent
        a dictionary, where the key is an issue key and value is a list of related pull requests.
        :return: Dictionary of lists of pull requests accessible by an issue key
        """
        print("\t{}: loading pull requests".format(self.issue_key))
        issue, connected_issues = self.data
        issue_keys = [issue["issue_key"]] + [connected_issue["issue_key"] for connected_issue in connected_issues]

        fetcher = GitHubFetcher(self.project, self.github_repository.replace("https://github.com/", ""),
                                self.credentials)
        pull_requests = dict()
        for key in issue_keys:
            pull_requests[key] = fetcher.get_pull_requests(key)
        print("\t{}: successfully loaded pull requests".format(self.issue_key))
        return pull_requests

    def __setup_packages(self) -> None:
        """
        Setup required LaTeX packages.
        :return: None
        """
        packages = self.doc.packages
        packages.append(Package("a4wide"))
        packages.append(Package("listings"))
        packages.append(Package("xcolor"))
        packages.append(Package("courier"))
        packages.append(Package("tabularx"))
        packages.append(Package("hyperref"))
        packages.append(Package("spverbatim"))

    def __setup_preamble(self) -> None:
        """
        Setup preamble of the LaTeX document.
        :return: None
        """
        preamble = self.doc.preamble
        issue = self.data[0]
        preamble.append(NoEscape(r"\UseRawInputEncoding"))
        preamble.append(Command("title", issue["issue_key"]))
        author = issue["author"] if issue["author"] else "no author"
        preamble.append(Command("author", author))
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

    def __add_comments(self, issue: dict) -> None:
        """
        Add comments for the specified issue. Each comment has the author and the body.
        :param issue: Issue represented as dictionary
        :return: None
        """
        doc = self.doc
        filtered_comments = [comment for comment in issue["comments"] if comment["author"] not in self.bots]
        if not filtered_comments:
            doc.append("No comments")
        else:
            with doc.create(Enumerate()) as enum:
                for comment in filtered_comments:
                    comment_body = utils.escape_with_listings(comment["body"])
                    enum.add_item(bold(comment["author"] + ": ") + comment_body)

    def __describe_issue(self, issue, root_issue: bool = False) -> None:
        """
        Describe the issue passed in the following form:
            1. Summary
            2. Description
            3. Attachments
            4. Commits
            5. Comments
            6. Pull requests
        :param issue: Issue represented as a dictionary
        :param root_issue: Whether the issue passed is the root (not a connected) issue of the document
        :return: None
        """
        doc = self.doc
        chapter_title = ("Root issue " if root_issue else "Connected issue ") + issue["issue_key"]
        with doc.create(Chapter(chapter_title)):
            if "summary" not in self.exclude:
                with doc.create(Section("Summary")):
                    summary = utils.escape_with_listings(issue["summary"])
                    doc.append(summary)

            if "description" not in self.exclude:
                with doc.create(Section("Description")):
                    description = utils.escape_with_listings(issue["description"])
                    doc.append(description)

            if "attachments" not in self.exclude:
                with doc.create(Section("Attachments")):
                    attachments = issue["attachments"]
                    if not attachments:
                        doc.append("No attachments")
                    else:
                        with doc.create(Enumerate()) as enum:
                            for attachment in issue["attachments"]:
                                enum.add_item(self.__hyperlink(attachment["content"], attachment["filename"]))

            # Each commit is described in the following way:
            # "Commit <short_SHA> by <author> (<date>): <commit_message>"
            if self.commits and "commits" not in self.exclude:
                with doc.create(Section("Commits")):
                    issue_key = issue["issue_key"]
                    commits = self.commits
                    if not commits[issue_key]:
                        doc.append("No related commits")
                    else:
                        with doc.create(Enumerate()) as enum:
                            for commit in commits[issue_key]:
                                enum.add_item(NoEscape("Commit {} by {} ({}): {}".format(
                                    bold(commit["short_sha"]),
                                    bold(escape_latex(commit["author"])),
                                    escape_latex(commit["date"]),
                                    escape_latex(commit["message"])
                                )))

            if "comments" not in self.exclude:
                with doc.create(Section("Comments")):
                    self.__add_comments(issue)

            # Each pull request is described in the following way:
            # Title: <pr_title>
            # Author: <pr_author>
            # Date: <pr_date>
            # Status: <pr_status>
            # Comments: [
            #   <comment_author> (<comment_date>): <comment_body>
            #   ...
            # ]
            if self.pull_requests and "pull_requests" not in self.exclude:
                with doc.create(Section("Pull requests")):
                    issue_key = issue["issue_key"]
                    pull_requests = self.pull_requests
                    if not pull_requests[issue_key]:
                        doc.append("No pull requests")
                    else:
                        for pr in pull_requests[issue_key]:
                            with doc.create(Subsection("Pull request {}".format(pr["number"]))):
                                doc.append(NoEscape(r"{}: {}\\".format(bold("Title"), pr["title"])))
                                doc.append(NoEscape(r"{}: {}\\".format(bold("Author"), pr["author"])))
                                doc.append(NoEscape(r"{}: {}\\".format(bold("Date"), pr["date"])))
                                doc.append(NoEscape(r"{}: {}\\".format(bold("Status"), pr["status"])))
                                doc.append(NoEscape(r"{}: ".format(bold("Comments"))))
                                if not pr["comments"]:
                                    doc.append("No comments")
                                else:
                                    with doc.create(Enumerate()) as enum:
                                        for comment in pr["comments"]:
                                            enum.add_item(NoEscape("{} ({}): {}".format(
                                                bold(comment["author"]),
                                                comment["date"],
                                                escape_latex(comment["body"].replace('\r', '\n')))
                                            ))

    def generate_report(self) -> None:
        """
        Generate PDF report for the issue specified by the field "issue_key".
        :return: None
        """
        doc = self.doc
        root_issue, connected_issues = self.data
        filename = root_issue["issue_key"]
        doc.append(NoEscape(r"\maketitle"))
        doc.append(NoEscape(r"\tableofcontents"))

        self.__describe_issue(root_issue, root_issue=True)

        if "other_issues" not in self.exclude:
            for issue in connected_issues:
                self.__describe_issue(issue)

        utils.create_dir_if_necessary("Reports")
        doc.generate_pdf(os.path.join("Reports", filename), clean_tex=True)

        print("{}: report is successfully created\n".format(root_issue["issue_key"]))
