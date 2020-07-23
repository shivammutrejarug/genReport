from github import Github

import os
from typing import List, Tuple

import utils

DATE_FORMAT = "%Y-%m-%d"


class GitHubFetcher:
    def __init__(self, project: str, repo_name: str, credentials: Tuple[str, str]):
        self.project = project
        self.github = Github(credentials[0], credentials[1])
        self.repo = self.github.get_repo(repo_name)
        self.savedir_commits = os.path.join("Projects", self.project, "Commits")
        self.savedir_pull_requests = os.path.join("Projects", self.project, "PullRequests")

    @staticmethod
    def __save_json(json_list: List[dict], directory: str, issue_key: str = None) -> None:
        """
        Save target list of dictionaries to the desired directory in a file in JSON format.
        If issue_key is specified, then the file is name "<issue_key>.json", otherwise - "all.json".
        :param json_list: List of dictionaries to save as JSON file
        :param directory: Directory where to save the file
        :param issue_key: Target issue key
        :return: None
        """
        utils.create_dir_if_necessary(directory)
        if issue_key:
            filename = issue_key + ".json"
        else:
            filename = "all.json"
        path = os.path.join(directory, filename)
        utils.save_as_json(json_list, path)

    def get_commits(self, issue_key: str = None) -> List[dict]:
        """
        Get list of dictionaries representing commits for the desired issue. If issue_key is not specified, then
        all commits are retrieved.
        :param issue_key: Target issue key
        :return: List of dictionaries representing commits
        """
        path = os.path.join(self.savedir_commits, "all.json")
        if not os.path.isfile(path):
            print("\t\tCommits are not cached. Fetching...")
            commits = self.fetch_commits()
            print("\t\tSuccessfully fetched fommits")
        else:
            print("\t\tCommits are cached. Loading...")
            commits = utils.load_json(path)
        if issue_key:
            prefix = issue_key + ':'
            commits = list(
                filter(
                    lambda commit: commit["message"].startswith(prefix),
                    commits
                )
            )
        return commits

    def fetch_commits(self, issue_key: str = None, save: bool = True) -> List[dict]:
        """
        Fetch and parse all commits for the target project. If issue_key is specified, then only PRs targeting the issue
        are retrieved. Targeting is determined by whether the commit message starts with issue_key + ':' since it is the
        standard convention for commit description.
        :param issue_key: Target issue key
        :param save: Whether to save commits to a file
        :return: List of dictionaries representing commits
        """
        commits_raw = self.repo.get_commits()
        if issue_key:
            prefix = issue_key + ":"
            commits_raw = list(
                filter(
                    lambda commit: commit.commit.message.startswith(prefix),
                    commits_raw
                )
            )
        commits = []
        for commit_raw in commits_raw:
            commit = dict()
            sha = commit_raw.sha
            commit["sha"] = sha
            commit["short_sha"] = sha[:7]
            commit["author"] = commit_raw.commit.author.name
            commit["date"] = commit_raw.commit.author.date.date().strftime(DATE_FORMAT)
            commit["message"] = commit_raw.commit.message
            commits.append(commit)

        if save:
            self.__save_commits(commits, issue_key)
        return commits

    def __save_commits(self, commits: List[dict], issue_key: str = None) -> None:
        """
        Save commits to a file. If issue_key is not specified, then commits are saved to "all.json" file.
        :param commits: List of dictionaries representing commits
        :param issue_key: Target issue key
        :return: None
        """
        self.__save_json(commits, self.savedir_commits, issue_key)

    def get_pull_requests(self, issue_key: str = None) -> List[dict]:
        """
        Get list of dictionaries representing pull requests for the desired issue. If issue_key is not specified, then
        all pull requests are retrieved.
        :param issue_key: Target issue key
        :return: List of dictionaries representing pull requests
        """
        path = os.path.join(self.savedir_pull_requests, "all.json")
        if not os.path.isfile(path):
            pull_requests = self.fetch_pull_requests()
        else:
            pull_requests = utils.load_json(path)
        if issue_key:
            pull_requests = list(
                filter(
                    lambda pr: issue_key in utils.extract_issues(pr["title"], self.project) or
                               issue_key in utils.extract_issues(pr["body"], self.project),
                    pull_requests
                )
            )
        return pull_requests

    def fetch_pull_requests(self, issue_key: str = None, save: bool = True) -> List[dict]:
        """
        Fetch and parse all pull requests for the target project, both closed and opened. If issue_key is specified,
        then only PRs targeting the issue are retrieved. Targeting is determined by the presence of issue_key
        in PR title or its body.
        :param issue_key: Target issue key
        :param save: Whether to save pull requests to a file
        :return: List of dictionaries representing pull requests
        """
        pull_requests_raw = self.repo.get_pulls(state="all")
        if issue_key:
            pull_requests_raw = list(
                filter(
                    lambda pr: issue_key in utils.extract_issues(pr.title, self.project) or
                               issue_key in utils.extract_issues(pr.body, self.project),
                    pull_requests_raw
                )
            )
        pull_requests = []
        for pr_raw in pull_requests_raw:
            pr = dict()
            pr["number"] = pr_raw.number
            pr["title"] = pr_raw.title
            pr["author"] = pr_raw.user.login
            pr["status"] = pr_raw.state
            pr["date"] = pr_raw.created_at.strftime(DATE_FORMAT)
            pr["body"] = pr_raw.body

            # Now let's fetch comments
            pr["comments"] = []
            pr_comments = pr["comments"]
            for comment in pr_raw.get_issue_comments():
                comment_dict = dict()
                comment_dict["author"] = comment.user.login
                comment_dict["date"] = comment.created_at.strftime(DATE_FORMAT)
                comment_dict["body"] = comment.body
                pr_comments.append(comment_dict)

            pull_requests.append(pr)

        if save:
            self.__save_pull_requests(pull_requests, issue_key)
        return pull_requests

    def __save_pull_requests(self, pull_requests: List[dict], issue_key: str = None) -> None:
        """
        Save pull requests to a file. If issue_key is not specified, then pull requests are saved to "all.json" file.
        :param pull_requests: List of dictionaries representing pull requests
        :param issue_key: Target issue key
        :return: None
        """
        self.__save_json(pull_requests, self.savedir_pull_requests, issue_key)
