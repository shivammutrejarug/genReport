from github import Github

import os
from typing import List

import utils


class GitHubFetcher:
    def __init__(self, project: str, repo_name: str):
        self.project = project
        self.github = Github("AlexFyod", "NormalFortExpress23yZ4R3R}{7if2")
        self.repo = self.github.get_repo(repo_name)
        self.savedir = os.path.join("Projects", self.project, "Commits")

    def get_commits(self, issue_key: str = None):
        path = os.path.join(self.savedir, issue_key + ".json")
        if not os.path.isfile(path):
            path = os.path.join(self.savedir, "all.json")
            if not os.path.isfile(path):
                commits = self.fetch_commits()
            else:
                commits = utils.load_json(path)
        else:
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

    def fetch_commits(self, issue_key: str = None, save: bool = True):
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
            commit["date"] = commit_raw.commit.author.date.date().strftime("%Y-%m-%d")
            commit["message"] = commit_raw.commit.message
            commits.append(commit)

        if save:
            self.__save_commits(commits, issue_key)
        return commits

    def __save_commits(self, commits: List[dict], issue_key: str = None):
        utils.create_dir_if_necessary(self.savedir)
        if issue_key:
            filename = issue_key + ".json"
        else:
            filename = "all.json"
        path = os.path.join(self.savedir, filename)
        utils.save_as_json(commits, path)
