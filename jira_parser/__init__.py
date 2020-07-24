import os
import traceback
from jira.client import JIRA
from typing import List, Tuple, Optional
import utils

from github_fetcher import GitHubFetcher

APACHE_JIRA_SERVER = "https://issues.apache.org/jira/"


class JiraParser:
    def __init__(self, jira_project: str, github_repository: str = None, github_credentials: Tuple[str, str] = None):
        self.jira = JIRA(server=APACHE_JIRA_SERVER)
        self.project = jira_project
        self.project_dir = os.path.join("Projects", self.project)
        self.issues_raw_dir = os.path.join(self.project_dir, "Issues_raw")
        self.issues_dir = os.path.join(self.project_dir, "Issues")
        self.fields = "comment," \
                      "attachment," \
                      "issuelinks," \
                      "status," \
                      "issuetype," \
                      "summary," \
                      "description," \
                      "created," \
                      "updated," \
                      "project," \
                      "creator"
        self.github = None
        if github_repository and github_credentials:
            self.github = GitHubFetcher(jira_project, github_repository.replace("https://github.com/", ""),
                                        github_credentials)

    def fetch_issues_raw(self, block_index: int = 0, save: bool = True) -> List[dict]:
        """
        Fetch all issues in their raw (unparsed) form from the project
        and return them as a list of dictionaries (decoded JSON form). Each issue will additionally have a key
        "remotelinks" which stores a list of remote links found in the issue (remote links cannot be fetched alongside
        other fields).
        :param block_index: Issues are fetched in blocks of 100 issues each, so this variable shows which block should
        the program start with
        :param save: Whether to persist issues in JSON format
        :return: List of issues as dictionaries
        """
        print("{}: fetching issues. This may take a while".format(self.project))
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
                self.__save_issues_raw(fetched_issues)
        print("{}: Finished fetching {} issues! Totally fetched: {}".format(self.project,
                                                                            " and saving" if save else "",
                                                                            len(issues)))
        return issues

    def fetch_issue_raw(self, issue_key: str, save: bool = True) -> dict:
        """
        Fetch a specific issue by its key and return it as an unparsed dictionary.
        :param issue_key: Key of the issue to fetch
        :param save: Whether to persist the issue in JSON format
        :return: Issue as a dictionary
        """
        issue = self.jira.issue(issue_key, self.fields).raw
        try:
            remote_links = self.jira.remote_links(issue["key"])
            issue["remotelinks"] = [link.raw for link in remote_links]
        except:
            print("An error occurred while trying to retrieve remote links for issue {}".format(issue["key"]))
            traceback.print_exc()
        if save:
            self.__save_issues_raw([issue])
        return issue

    def __save_issues_raw(self, issues: List[dict]) -> None:
        """
        Persist raw issues in the corresponding folder.
        :param issues: List of dictionaries describing unparsed issues
        :return: None
        """
        directory = self.issues_raw_dir
        utils.create_dir_if_necessary(directory)
        print("\t{}: Successfully saved!".format(self.project))
        for issue in issues:
            key = issue["key"]
            filename = key + ".json"
            path = os.path.join(directory, filename)
            utils.save_as_json(issue, path)

    def load_issues_raw(self) -> List[dict]:
        """
        Load unparsed issues stored in the folder "Issues_raw" and return them as a list of dictionaries.
        :return: List of issues represented as dictionaries
        """
        directory = self.issues_raw_dir
        if not os.path.exists(directory):
            return []
        issues = []
        files = os.listdir(directory)
        for filename in files:
            path = os.path.join(directory, filename)
            issue = utils.load_json(path)
            issues.append(issue)
        return issues

    def load_issue_raw(self, issue_key: str) -> Optional[dict]:
        """
        Load a raw issue with the specified issue key. If it is not found in the "Issues_raw" directory,
        then None is returned.
        :param issue_key: Key of the issue to load from the "Issues_raw" directory
        :return: Loaded issue represented as a dictionary or None
        """
        path = os.path.join(self.issues_raw_dir, issue_key + ".json")
        if not os.path.isfile(path):
            return None
        return utils.load_json(path)

    def parse_issues(self, issues_raw: List[dict] = None) -> List[dict]:
        """
        For each raw issue, create a JSON file containing necessary information:
        1. Issue key
        2. Project information
            2.1 Project key
            2.2 Project name
        3. Author
        4. Date of creation
        5. Date of update
        6. Current status
        7. Summary
        8. Description
        9. List of attachments
            9.1 File name
            9.2 URL to attachment
        10. List of issue links
            10.1 Type of link
            10.2 Issue key
        11. List of remote links
            11.1 Title of link
            11.2 URL
        12. List of comments
            12.1 Author
            12.2 Date of creation
            12.3 Date of update
            12.4 Comment body

        The parsed data for each file is stored in "Projects/<project_name>/Issues/<issue_key>.json
        :param issues_raw: List of dictionaries representing raw issues. If none is specified, then they are
        loaded from the cache
        :return: List of dictionaries of parsed issues
        """
        print("{}: parsing issues. This may take a while".format(self.project))
        count = 0
        issues_dir = self.issues_dir
        utils.create_dir_if_necessary(issues_dir)

        if not issues_raw:
            issues_raw = self.load_issues_raw()

        issues = []
        for count, issue in enumerate(issues_raw, start=1):
            filename = issue["key"] + ".json"
            path = os.path.join(issues_dir, filename)
            json_object = self.__prepare_json_object(issue)
            utils.save_as_json(json_object, path)
            issues.append(json_object)

            if count % 100 == 0:
                print("{}: Parsed {} issues".format(self.project, count))
        print("{}: Finished parsing issues! Totally parsed: {}".format(self.project, count))
        return issues

    def parse_issue(self, issue_key: str) -> dict:
        """
        Parse a raw issue and store it in "Projects/<project_name>/Issues/<issue_key>.json.
        If the issue is not cached, then it is fetched first.
        :param issue_key: Key of the issue to parse
        :return: Dictionary representing the issue
        """
        filename = issue_key + ".json"
        utils.create_dir_if_necessary(self.issues_dir)
        path_raw = os.path.join(self.issues_raw_dir, filename)
        if not os.path.isfile(path_raw):
            issue_raw = self.fetch_issue_raw(issue_key, save=True)
        else:
            issue_raw = utils.load_json(path_raw)
        json_object = self.__prepare_json_object(issue_raw)

        path = os.path.join(self.issues_dir, filename)
        utils.save_as_json(json_object, path)
        return json_object

    def load_issue(self, issue_key: str) -> dict:
        filename = issue_key + ".json"
        path = os.path.join(self.issues_dir, filename)
        if not os.path.isfile(path):
            issue = self.parse_issue(issue_key)
        else:
            issue = utils.load_json(path)
        return issue

    def __prepare_json_object(self, issue: dict) -> dict:
        """
        Prepare a dictionary containing the following data:
        {
          "issue_key": <issue key>,
          "project": {
            "key": <project key>,
            "name": <project name>,
          },
          "author": "author's name",
          "created": <date & time>,
          "updated": <date & time>,
          "status": <current status (Opened, Closed, etc.),
          "summary": <summary>,
          "description": <description>,
          "attachments": [
            {
              "filename": <file name>,
              "content": <url to attachment>
            },
            ...
          ],
          "issuelinks": [
            {
              "type": <type of issue, e.g. "duplicate">,
              "issue_key": <issue key>
            },
            ...
          ],
          "remotelinks:" [
            {
              "title": <url title>,
              "url": <url link>
            },
            ...
          ],
          "comments": [
            {
              "author": <author name>,
              "created": <date & time>,
              "updated": <date & time>,
              "body": <content of comment>,
            },
            ...
          ]
        }
        :param issue: Issue to retrieve data from
        :return: Dictionary ready to be converted to JSON
        """
        json_object = dict()
        fields = issue["fields"]

        # Issue key
        json_object["issue_key"] = issue["key"]

        # Project
        json_object["project"] = {
            "key": fields["project"]["key"],
            "name": fields["project"]["name"]
        }

        # Technical details
        author = fields["creator"]
        json_object["author"] = author["name"] if author else None
        json_object["created"] = fields["created"]
        json_object["updated"] = fields["updated"]
        json_object["status"] = fields["status"]["name"]

        # Summary and description
        json_object["summary"] = fields["summary"]
        description = fields["description"]  # It was found that there can be no description.
        json_object["description"] = description if description else ""

        # Attachments
        json_object["attachments"] = [
            {
                "filename": attachment["filename"],
                "content": attachment["content"]
            }
            for attachment in fields["attachment"]
        ]

        # Issue links
        json_object["issuelinks"] = [
            {
                "type": link["type"]["name"],
                "issue_key": link["inwardIssue"]["key"] if "inwardIssue" in link else link["outwardIssue"]["key"]
            }
            for link in fields["issuelinks"]
        ]

        # Remote links
        json_object["remotelinks"] = [
            {
                "title": link["object"]["title"],
                "url": link["object"]["url"]
            }
            for link in issue["remotelinks"]
        ]

        # Comments
        json_object["comments"] = [
            {
                "author": comment["author"]["name"],
                "created": comment["created"],
                "updated": comment["updated"],
                "body": comment["body"]
            }
            for comment in fields["comment"]["comments"]
        ]

        # Pull requests and commits
        json_object["pull_requests"], json_object["commits"] = [], []
        if self.github:
            print("\t{}: loading pull requests. If not cached, this may take a while".format(self.project))
            json_object["pull_requests"] = self.github.get_pull_requests(issue["key"])
            print("\t{}: loading commits. If not cached, this may take a while".format(self.project))
            json_object["commits"] = self.github.get_commits(issue["key"])

        return json_object
