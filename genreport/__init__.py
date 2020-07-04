from pylatex import Document, Section, Subsection, Package, Hyperref
from pylatex.utils import escape_latex, NoEscape
import utils
import os

from genreport.issueretriever import IssueRetriever


class ReportGenerator:
    def __init__(self, project, issue, github_repository=None):
        self.project = project
        self.issue = issue
        self.github_repository = github_repository
        self.data = self.__load_issue()
        self.doc = Document()
        self.doc.packages.append(Package("a4wide"))

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
        with doc.create(Section(self.issue)):
            doc.append("Status: {}\n".format(data["status"]))
            doc.append("Created: {}\n".format(data["created"]))
            doc.append("Updated: {}\n".format(data["updated"]))
            with doc.create(Subsection("Attachments")):
                doc.append()


