from jira import Issue
from pylatex import Document, Section, Subsection, Package, Hyperref, Command, Enumerate
from pylatex.utils import escape_latex, NoEscape
import utils
import os


class ReportGenerator:
    def __init__(self, project, issue, github_repository: str = None):
        self.project = project
        self.issue = issue
        self.github_repository = github_repository
        self.data = self.__load_issue()
        self.doc = Document(document_options="article")
        packages = self.doc.packages
        packages.append(Package("a4wide"))
        packages.append(Package("listings"))
        packages.append(Package("xcolor"))
        packages.append(Package("courier"))
        packages.append(Package("tabularx"))
        packages.append(Package("hyperref"))

        preamble = self.doc.preamble
        preamble.append(Command("title", self.data["issue_key"]))
        preamble.append(Command("author", self.data["author"]))
        preamble.append(Command("date", self.data["created"].split("T")[0]))
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

        self.other_issues = []

    def __load_issue(self):
        path = os.path.join("Projects", self.project, "Issues", self.issue + ".json")
        return utils.load_json(path)

    @staticmethod
    def __hyperlink(url, description):
        description = escape_latex(description)
        return NoEscape(r"\href{" + url + "}{" + description + "}")

    def generate_report(self):
        doc = self.doc
        data = self.data
        doc.append(NoEscape(r"\maketitle"))

        with doc.create(Section("Summary")):
            doc.append(NoEscape(data["summary"]))

        with doc.create(Section("Description")):
            description = utils.atlassian_code_format_to_listing(data["description"])
            doc.append(NoEscape(description))

        with doc.create(Section("Attachments")):
            attachments = data["attachments"]
            with doc.create(Enumerate()) as enum:
                for attachment in attachments:
                    enum.add_item(self.__hyperlink(attachment["content"], attachment["filename"]))

        doc.generate_pdf(data["issue_key"], clean_tex=True)
