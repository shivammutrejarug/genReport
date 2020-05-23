import errno
import os

from jira.client import JIRA
from jira.resources import Issue
from typing import List

import utils

PROJECTS = ["PDFBOX"]
APACHE_JIRA_SERVER = "https://issues.apache.org/jira/"


class JiraParser:
    def __init__(self, jira_project: str):
        self.jira = JIRA(server=APACHE_JIRA_SERVER)
        self.project = jira_project

    def fetch_issues(self, block_index: int = 0, save: bool = True) -> List[Issue]:
        """
        Fetch all issues from the project and store them in the self.issues list
        """
        issues = []
        block_size = 100
        while True:
            start_index = block_index * block_size
            fetched_issues = self.jira.search_issues("project={}".format(self.project), startAt=start_index,
                                                     maxResults=block_size, validate_query=True)
            if len(fetched_issues) == 0:
                break
            block_index += 1
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

    def __save_issues(self, issues: List[Issue], first_issue: int, last_issue: int) -> None:
        print("\t{}: Saving issues from {} to {}".format(self.project, first_issue, last_issue))
        directory = os.path.join("Projects", self.project, "Issues_raw")
        utils.create_dir_if_necessary(directory)
        for issue in issues:
            filename = issue.raw["key"] + ".json"
            path = os.path.join(directory, filename)
            utils.save_as_json(issue.raw, path)
        print("\t{}: Saved issues from {} to {}".format(self.project, first_issue, last_issue))

    def read_issues(self) -> List[dict]:
        directory = os.path.join("Projects", self.project, "Issues_raw")
        if not os.path.exists(directory):
            return []
        issues = []
        files = os.listdir(directory)
        for filename in files:
            path = os.path.join(directory, filename)
            issues.append(utils.load_json(path))
        return issues

    def fetch_and_save_comments(self, issues: List[Issue]):
        """
        For each issue stored in the JiraParser object,
        fetch all comments and create a JSON file containing necessary information:
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
            filename = issue.raw["key"] + ".json"
            path = os.path.join(directory, filename)
            json_object = self.__prepare_json_object(issue)
            utils.save_as_json(json_object, path)

            if count % 100 == 0:
                print("{}: Saved {} issues and their comments".format(self.project, count))
        print("{}: Finished saving issues! Totally saved: {}".format(self.project, count))

    def __prepare_json_object(self, issue: Issue) -> dict:
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
        json_object["issue_key"] = issue.raw["key"]
        json_object["status"] = issue.raw["fields"]["status"]["name"]
        json_object["created"] = issue.raw["fields"]["created"]
        json_object["updated"] = issue.raw["fields"]["updated"]
        json_object["comments"] = []

        comments = json_object["comments"]

        for comment in self.jira.comments(issue):
            comment_dict = dict()
            comment_dict["author"] = comment.raw["author"]["name"]
            comment_dict["created"] = comment.raw["created"]
            comment_dict["updated"] = comment.raw["updated"]
            comment_dict["body"] = comment.raw["body"]
            comments.append(comment_dict)

        return json_object
