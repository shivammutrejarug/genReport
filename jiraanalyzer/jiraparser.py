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
                                                                             validate_query=True)]
            if len(fetched_issues) == 0:
                break
            block_index += 1
            issues.extend(fetched_issues)
            for issue in issues:
                issue["remote_links"] = []
                try:
                    remote_links = self.jira.remote_links(issue["key"])
                    issue["remote_links"] = [link.raw for link in remote_links]
                except:
                    print("An error occurred while trying to retrieve remote links for issue {}".format(issue["key"]))
                    traceback.print_exc()
            print("{}: Fetched {} issues".format(self.project, len(issues)))
            if save:
                first_issue = len(issues) - len(fetched_issues) + 1
                last_issue = len(issues)
                self.__save_issues(fetched_issues, first_issue, last_issue)
        print("{}: Finished fetching{} issues! Totally fetched: {}".format(self.project,
                                                                           " and saving" if save else "",
                                                                           len(issues)))
        return issues

    def __save_issues(self, issues: List[dict], first_issue: int, last_issue: int) -> None:
        directory = os.path.join("Projects", self.project, "Issues_raw")
        utils.create_dir_if_necessary(directory)
        for issue in issues:
            filename = issue["key"] + ".json"
            path = os.path.join(directory, filename)
            utils.save_as_json(issue, path)
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

    def fetch_comments(self):
        issues_dir = os.path.join("Projects", self.project, "Issues_raw")
        if not os.path.exists(issues_dir):
            return
        files = os.listdir(issues_dir)

        comments_dir = os.path.join("Projects", self.project, "Comments")
        utils.create_dir_if_necessary(comments_dir)
        count = 1
        for filename in files:
            path = os.path.join(comments_dir, filename)
            issue_key = os.path.splitext(filename)[0]
            comments = [comment.raw for comment in self.jira.comments(issue_key)]
            comments_dict = dict()
            comments_dict["issue_key"] = issue_key
            comments_dict["comments"] = []
            for comment in comments:
                comment_dict = dict()
                comment_dict["author"] = comment["author"]["name"]
                comment_dict["created"] = comment["created"]
                comment_dict["updated"] = comment["updated"]
                comment_dict["body"] = comment["body"]
                comments_dict["comments"].append(comment_dict)
            utils.save_as_json(comments_dict, path)
            print("{}: Fetched comments for {}. Total: {}".format(self.project, issue_key, count))
            count += 1

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

    def __prepare_json_object(self, issue: dict) -> dict:
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
        json_object["issue_key"] = issue["key"]
        fields = issue["fields"]
        json_object["status"] = fields["status"]["name"]
        json_object["created"] = fields["created"]
        json_object["updated"] = fields["updated"]

        json_object["issue_links"] = []
        issue_links = json_object["issue_links"]
        for link in fields["issuelinks"]:
            link_dict = dict()
            link_dict["type"] = link["type"]["name"]
            if "outwardIssue" in link:
                link_dict["type"] = "Outward Issue"
                link_dict["outward_issue"] = link["outwardIssue"]["key"]
            elif "inwardIssue" in link:
                link_dict["type"] = "Inward Issue"
                link_dict["inward_issue"] = link["inwardIssue"]["key"]
            issue_links.append(link_dict)

        json_object["remote_links"] = []
        remote_links = json_object["remote_links"]
        for link in issue["remote_links"]:
            link_dict = dict()
            link_dict["title"] = link["object"]["title"]
            link_dict["url"] = link["object"]["url"]
            remote_links.append(link_dict)

        json_object["comments"] = []
        comments = json_object["comments"]
        comments_dir = os.path.join("Projects", self.project, "Comments")
        path = os.path.join(comments_dir, issue["key"] + ".json")
        if os.path.exists(path):
            loaded_comments = utils.load_json(path)["comments"]
            for comment in loaded_comments:
                comment_dict = dict()
                comment_dict["author"] = comment["author"]
                comment_dict["created"] = comment["created"]
                comment_dict["updated"] = comment["updated"]
                comment_dict["body"] = comment["body"]
                comments.append(comment_dict)

        return json_object
