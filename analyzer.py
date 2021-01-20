import argparse
import json
import matplotlib.pyplot as plt
import os
from typing import List, Tuple, Set
import shutil
from github.GithubException import UnknownObjectException, BadCredentialsException

from jira_parser import JiraParser
import utils


def __parse_arguments():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-p", "--project", help="Target Jira project in capital letters", required=True)
    arg_parser.add_argument("-g", "--github", help="Target Jira project's GitHub repository")
    arg_parser.add_argument("-c", "--credentials", help="GitHub username and personal access token separated by comma. "
                                                        "Compulsory if GitHub repository is specified")
    return arg_parser.parse_args()


def __collect_issue_summary(project: str, issue: dict, save=True) -> \
        Tuple[str, int, Set[str], Set[str], Set[str], Set[str], Set[str], Set[str], List[str], List[str]]:
    """

    :param project: Related project
    :param issue: Issue represented as a dictionary
    :param save: Whether to save the statistics on hard drive
    :return:
    """

    # FIELD 1: issue key
    issue_key = str(issue["issue_key"])

    # FIELD 2: issue ID; used to increase the efficiency of sorting the data
    issue_id = int(issue_key.split('-')[1])

    # Parse Description and Remote Links. Remote links are not different from any other type of URLs,
    # so we will just append them to the description of the issue in order to avoid code duplication.
    description_and_remote_links = issue["description"] + " " + " ".join(
        [remote_link["url"] for remote_link in issue["remotelinks"]]
    )

    # FIELD 3: unparsed URLs
    # FIELD 4: revision IDs
    # FIELD 5: URLs detected as mailing lists
    # FIELD 6: URLs detected as PDF documents
    # FIELD 7: URLs detected as archive files
    # FIELD 8: Other issues
    urls, revisions, mailing_lists, pdf_documents, archives, other_issues = \
        utils.extract_references(description_and_remote_links, project)

    # Parse Comments
    for comment in issue["comments"]:
        comment_details = utils.extract_references(comment["body"], project)
        urls.update(comment_details[0])
        revisions.update(comment_details[1])
        mailing_lists.update(comment_details[2])
        pdf_documents.update(comment_details[3])
        archives.update(comment_details[4])
        other_issues.update(comment_details[5])

    for other_issue in issue["issuelinks"]:
        other_issues.add(other_issue["issue_key"])

    # FIELD 9: commits
    # FIELD 10: pull requests
    commits = [commit["sha"] for commit in issue["commits"]]
    pull_requests = [str(pr["number"]) for pr in issue["pull_requests"]]

    summary = (issue_key,
               issue_id,
               urls,
               revisions,
               mailing_lists,
               pdf_documents,
               archives,
               other_issues,
               commits,
               pull_requests)

    if save:
        __save_references(project, summary)
    return summary


def __collect_issues_summary(project: str, save=True) -> List[
    Tuple[str, int, Set[str], Set[str], Set[str], Set[str], Set[str], Set[str], List[str], List[str]]]:
    """
    For each Issue inside Projects/<project>/Issues, extract all types of references and return a data type containing
    all the necessary data
    :param project: Project to extract references from
    :param save: Whether to save extracted references to JSON documents
    :return: List of tuples containing data
    """
    directory = os.path.join("Projects", project, "Issues")
    if not os.path.isdir(directory):
        print("The folder does not exist. Make sure you fetched and parsed at least one issue.")
        return []
    issues_dir = os.listdir(directory)
    issues = []

    for filename in issues_dir:
        path = os.path.join(directory, filename)
        with open(path, 'r') as issue_file:
            issue = json.load(issue_file)
            summary = __collect_issue_summary(project, issue, save)
            issues.append(summary)
    return issues


def __save_references(project: str,
                      issue_summary: Tuple[
                          str, int, Set[str], Set[str], Set[str], Set[str], Set[str], Set[str], List[str], List[str]
                      ]) -> None:
    """
    Save references for an issue in JSON format.
    :param project: Project to write references for
    :param issue_summary: Data type describing necessary data
    :return: None
    """
    summary_dir = os.path.join("Projects", project, "Summary")
    if not os.path.isdir(summary_dir):
        os.mkdir(summary_dir)

    issue_dict = {
        "issue_key": issue_summary[0],
        "issue_id": issue_summary[1],
        "urls": list(issue_summary[2]),
        "revisions": list(issue_summary[3]),
        "mailing_lists": list(issue_summary[4]),
        "pdf_documents": list(issue_summary[5]),
        "archives": list(issue_summary[6]),
        "other_issues": list(issue_summary[7]),
        "commits": issue_summary[8],
        "pull_requests": issue_summary[9]
    }
    path = os.path.join(summary_dir, issue_summary[0] + ".json")
    utils.save_as_json(issue_dict, path)


def __generate_statistics(project: str) -> List[Tuple[int, int, int, int, int, int, int, int, int, int]]:
    """
    Based on the references for each issue, generate the frequency of each type of references and split the data
    into blocks of 100 issues for a broader analysis of the data.
    :param project: Project to parse references from
    :return: List of tuples representing generated statistics with the following fields:
        1. Current block description (e.g. 100 means block 1-100, 400 means block 301-400)
        2. Total number of references in block
        3. Number of revisions
        4. Number of mailing lists
        5. Number of PDF documents URLs
        6. Number of archive files URLs
        7. Number of other issues
        8. Number of uncategorized URLs
        9. Number of commits
        10. Number of pull requests
    """
    issues = []
    summary_directory = os.path.join("Projects", project, "Summary")

    for filename in os.listdir(summary_directory):
        path = os.path.join(summary_directory, filename)
        with open(path, 'r') as file:
            data = json.load(file)
            issues.append(
                (str(data["issue_key"]),
                 int(data["issue_id"]),
                 list(data["urls"]),
                 list(data["revisions"]),
                 list(data["mailing_lists"]),
                 list(data["pdf_documents"]),
                 list(data["archives"]),
                 list(data["other_issues"]),
                 data["commits"],
                 data["pull_requests"])
            )
    issues = sorted(issues, key=lambda x: x[1])

    # Since the number of references in each issue can be very little, it makes sense to combine them in blocks of 100
    # in order to have a better overview of the development of the project.
    blocks = []
    block_size = 100
    block_idx = 0
    while True:
        start_idx = block_idx * block_size
        block = issues[start_idx:start_idx + block_size]
        if len(block) == 0:
            break
        blocks.append(block)
        block_idx += 1

    # Now it's time to collect statistics
    block_idx = 1
    statistics = []
    for block in blocks:
        total = 0
        revisions = 0
        mailing_lists = 0
        pdf_documents = 0
        archives = 0
        other_issues = 0
        other_urls = 0
        commits = 0
        pull_requests = 0
        for issue in block:
            revisions += len(issue[3])
            mailing_lists += len(issue[4])
            pdf_documents += len(issue[5])
            archives += len(issue[6])
            other_issues += len(issue[7])
            other_urls += len(issue[2])
            commits += len(issue[8])
            pull_requests += len(issue[9])
            for i in range(2, 10):
                total += len(issue[i])
        statistics.append(
            (block_idx * 100, total, revisions, mailing_lists, pdf_documents, archives, other_issues, other_urls,
             commits, pull_requests))
        block_idx += 1
    return statistics


def __make_plot(project: str, plots_dir: str,
                statistics: List[Tuple[int, int, int, int, int, int, int, int, int]], blocks: List[int],
                param_idx: int, param_title: str) -> None:
    """
    Make a plot for the statistics provided.
    :param project: Project name
    :param plots_dir: Directory where to save the plot
    :param statistics: List of tuples representing generated statistics with the following fields:
        1. Total number of references in block
        2. Number of revisions
        3. Number of mailing lists
        4. Number of PDF documents URLs
        5. Number of archive files URLs
        6. Number of other issues
        7. Number of uncategorized URLs
        8. Number of commits
        9. Number of pull requests
        10. Number of pull requests
    :param blocks: List of 100-based values representing blocks (100 = block 1, 300 = block 3, etc.)
    :param param_idx: Index of the parameter to make the plot for
    :param param_title: Name of the parameter to make the plot for
    :return: None
    """
    x = blocks
    y = [param[param_idx] for param in statistics]
    plt.plot(x, y)
    plt.xlabel("Issue IDs")
    plt.ylabel("Frequency of {}".format(param_title))
    plt.title("Changes in frequency of {} through the evolution of the project {}".format(param_title, project))
    path = os.path.join(plots_dir, param_title + ".png")
    if os.path.isfile(path):
        os.remove(path)
    plt.savefig(path, bbox_inches='tight')
    plt.close()


def __make_plots(project: str, statistics: List[Tuple[int, int, int, int, int, int, int, int, int, int]]) -> None:
    """
    Make plots for the statistics provided.
    :param project: Project name
    :param statistics: List of tuples representing generated statistics with the following fields:
        1. Total number of references in block
        2. Number of revisions
        3. Number of mailing lists
        4. Number of PDF documents URLs
        5. Number of archive files URLs
        6. Number of other issues
        7. Number of uncategorized URLs
        8. Number of commits
        9. Number of pull requests
    :return: None
    """
    blocks = [param[0] for param in statistics]
    types = [
        (1, "Total references"),
        (2, "Revisions"),
        (3, "Mailing Lists"),
        (4, "PDF documents"),
        (5, "Archives"),
        (6, "Other issues"),
        (7, "Other URLs"),
        (8, "Commits"),
        (9, "Pull requests")
    ]

    plots_dir = os.path.join("Projects", project, "Plots")
    shutil.rmtree(plots_dir, ignore_errors=True)
    os.mkdir(plots_dir)

    for t in types:
        __make_plot(project, plots_dir, statistics, blocks, t[0], t[1])


if __name__ == "__main__":
    args = __parse_arguments()
    project = args.project

    github_repository, github_credentials = None, None
    if args.github:
        github_repository = args.github
        if not args.credentials:
            print("You should specify GitHub credentials as well. For example:\n"
                  "--credentials \"github_username,personal access token\"\n"
                  "-c \"github_username,personal access token\"")
            exit(-1)
        else:
            github_credentials = utils.define_github_credentials(args.credentials)

    try:
        parser = JiraParser(project, github_repository, github_credentials)
        parser.fetch_issues_raw()  # This is the assumption that the issues are not fetched.

        # While parsing issues, the program may fail to access GitHub repository or to use credentials provided.
        parser.parse_issues()
    except UnknownObjectException:
        print("Invalid GitHub repository. Aborting...")
        exit(-1)
    except BadCredentialsException:
        print("Invalid GitHub credentials. Aborting...")
        exit(-1)
    summary = __collect_issues_summary(project)
    statistics = __generate_statistics(project)
    __make_plots(project, statistics)
