import os
import traceback

from jira.client import JIRA
from typing import List

import utils

PROJECTS = ["PDFBOX"]
APACHE_JIRA_SERVER = "https://issues.apache.org/jira/"


class JiraParser:
    def __init__(self, jira_project: str):
        self.jira = JIRA(server=APACHE_JIRA_SERVER)
        self.project = jira_project
        self.fields = "comment,attachment,issuelinks,status,issuetype,summary,description,created,updated,project,creator"

    def fetch_issues(self, block_index: int = 0, save: bool = True) -> List[dict]:
        """
        Fetch all issues from the project and store them in the self.issues list
        """
        issues = []
        block_size = 100
        while True:
            start_index = block_index * block_size
            fetched_issues = [issue.raw for issue in self.jira.search_issues("project={}".format(self.project),
                                                                             startAt=start_index,
                                                                             maxResults=block_size,
                                                                             validate_query=True,
                                                                             fields=self.fields)]
            if len(fetched_issues) == 0:
                break
            block_index += 1
            for issue in fetched_issues:
                issue["remotelinks"] = []
                try:
                    remote_links = self.jira.remote_links(issue["key"])
                    issue["remotelinks"] = [link.raw for link in remote_links]
                except:
                    print("An error occurred while trying to retrieve remote links for issue {}".format(issue["key"]))
                    traceback.print_exc()
            issues.extend(fetched_issues)
            print("{}: Fetched {} issues".format(self.project, len(issues)))
            if save:
                first_issue = len(issues) - len(fetched_issues) + 1
                last_issue = len(issues)
                self.__save_issues(fetched_issues, first_issue, last_issue)
        print("{}: Finished fetching{} issues! Totally fetched: {}".format(self.project,
                                                                           " and saving" if save else "",
                                                                           len(issues)))
        return issues

    def fetch_issue(self, issue_key: str, save: bool = True):
        issue = self.jira.issue(issue_key, self.fields).raw
        if save:
            self.__save_issues([issue])
        return issue

    def __save_issues(self, issues: List[dict], first_issue: int = None, last_issue: int = None) -> None:
        directory = os.path.join("Projects", self.project, "Issues_raw")
        utils.create_dir_if_necessary(directory)
        for issue in issues:
            filename = issue["key"] + ".json"
            path = os.path.join(directory, filename)
            utils.save_as_json(issue, path)
        if first_issue and last_issue:
            print("\t{}: Saved issues from {} to {}".format(self.project, first_issue, last_issue))

    def load_issues(self) -> List[dict]:
        directory = os.path.join("Projects", self.project, "Issues_raw")
        if not os.path.exists(directory):
            return []
        issues = []
        files = os.listdir(directory)
        for filename in files:
            path = os.path.join(directory, filename)
            issues.append(utils.load_json(path))
        return issues

    def parse_issues(self, issues: List[dict]):
        """
        For each issue, create a JSON file containing necessary information:
        1. Issue key
        2. Date of its creation
        3. Date of its update
        4. List of comments related to the issue:
            4.1. Author of the comment
            4.2. Date of posting the comment
            4.3. Date of updating the comment
            4.4. Body of the comment
        All the data is stored in a file "Projects/<project_name>/Issues/<issue_key>.json"
        """
        count = 0
        directory = os.path.join("Projects", self.project, "Issues")
        utils.create_dir_if_necessary(directory)
        for count, issue in enumerate(issues, start=1):
            filename = issue["key"] + ".json"
            path = os.path.join(directory, filename)
            json_object = self.__prepare_json_object(issue)
            utils.save_as_json(json_object, path)

            if count % 100 == 0:
                print("{}: Saved {} issues and their comments".format(self.project, count))
        print("{}: Finished saving issues! Totally saved: {}".format(self.project, count))

    @staticmethod
    def __prepare_json_object(issue: dict) -> dict:
        """
        Prepare a dictionary containing the following data:
        {
          issue_key: <project name>
          created: <date & time>
          updated: <date & time>
          comments:
          [
            author: <author name>
            created: <date & time>
            updated: <date & time>
            body: <content of comment>
          ]
        }
        :param issue: Issue to retrieve data from
        :return: Dictionary ready to be converted to JSON
        """
        json_object = dict()
        fields = issue["fields"]
        creator = fields["creator"]

        json_object["issue_key"] = issue["key"]
        json_object["project"] = dict()
        project = json_object["project"]
        project["key"] = fields["project"]["key"]
        project["name"] = fields["project"]["name"]
        json_object["author"] = creator["name"] if creator else None
        json_object["created"] = fields["created"]
        json_object["updated"] = fields["updated"]
        json_object["status"] = fields["status"]["name"]

        json_object["summary"] = fields["summary"]
        json_object["description"] = fields["description"]

        json_object["attachments"] = list()
        attachments = json_object["attachments"]
        for attachment in fields["attachment"]:
            attachment_dict = dict()
            attachment_dict["filename"] = attachment["filename"]
            attachment_dict["content"] = attachment["content"]
            attachments.append(attachment_dict)

        json_object["issuelinks"] = []
        issue_links = json_object["issuelinks"]
        for link in fields["issuelinks"]:
            link_dict = dict()
            link_dict["type"] = link["type"]["name"]
            if "outwardIssue" in link:
                link_dict["issue_key"] = link["outwardIssue"]["key"]
            elif "inwardIssue" in link:
                link_dict["issue_key"] = link["inwardIssue"]["key"]
            issue_links.append(link_dict)

        json_object["remotelinks"] = []
        remote_links = json_object["remotelinks"]
        for link in issue["remotelinks"]:
            link_dict = dict()
            link_dict["title"] = link["object"]["title"]
            link_dict["url"] = link["object"]["url"]
            remote_links.append(link_dict)

        json_object["comments"] = []
        comments = json_object["comments"]

        for comment in fields["comment"]["comments"]:
            comment_dict = dict()
            comment_dict["author"] = comment["author"]["name"]
            comment_dict["created"] = comment["created"]
            comment_dict["updated"] = comment["updated"]
            comment_dict["body"] = comment["body"]
            comments.append(comment_dict)

        return json_object
