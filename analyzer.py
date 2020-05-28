import json
from jiraanalyzer import JiraParser
import matplotlib.pyplot as plt
import os
from typing import List, Tuple, Set
import shutil

import utils

PROJECTS = [
    "PDFBOX",
    "DERBY",
    "CASSANDRA",
    "YARN",
    "HDFS",
    "HADOOP",
    "MAPREDUCE",
    "ZOOKEEPER",
    "CONNECTORS",  # ManifoldCF https://issues.apache.org/jira/projects/CONNECTORS/summary
    "BIGTOP",
    "OFBIZ",
    "DIRSTUDIO",  # Directory Studio https://issues.apache.org/jira/projects/DIRSTUDIO/summary
    "DIRMINA",  # MINA https://issues.apache.org/jira/projects/DIRMINA/summary
    "CAMEL",  # Camel https://issues.apache.org/jira/projects/CAMEL/summary
    "AXIS2"  # Axis2 https://issues.apache.org/jira/projects/AXIS2/summary
]

PROJECTS_WITH_QA_BOTS = [
    "HBASE",  # HBase https://issues.apache.org/jira/projects/HBASE/summary
    "HIVE",  # Hive https://issues.apache.org/jira/projects/HIVE/summary
]

PROJECTS_WITH_PULL_REQUESTS = [
    "TAJO",  # Tajo https://issues.apache.org/jira/projects/TAJO/summary
    "NUTCH"  # Nutch https://issues.apache.org/jira/projects/NUTCH/summary
]

args = utils.parse_arguments()
projects = [args.jira_project] if args.jira_project else PROJECTS


# ALREADY DONE
# retrieve_and_save_issues(projects)


def collect_issues_summary(project: str) -> List[Tuple[str, int, Set[str], Set[str], Set[str], Set[str], Set[str]]]:
    """
    For each Issue inside Projects/<project>/Issues, extract all types of references and return a data type containing
    all the necessary data
    :param project: Project to extract references from
    :return: List of tuples containing data
    #TODO explain better what exactly is returned
    """
    directory = os.path.join("Projects", project, "Issues")
    issues_dir = os.listdir(directory)
    issues = []

    for filename in issues_dir:
        path = os.path.join(directory, filename)
        with open(path, 'r') as issue_file:
            data = json.load(issue_file)
            issue_key = str(data["issue_key"])
            issue_id = int(utils.extract_numbers(issue_key)[0])

            urls = set()
            revisions = set()
            mailing_lists = set()
            pdf_documents = set()
            other_issues = set()

            for comment in data["comments"]:
                comment_body = comment["body"]
                comment_urls = set(utils.extract_urls(comment_body, filter_revisions=True))
                comment_revisions = utils.extract_revisions(comment_body, uniform=True)

                comment_mailing_lists = utils.filter_mailing_list_urls(comment_urls)
                comment_urls = comment_urls.difference(comment_mailing_lists)

                comment_pdf_documents = utils.filter_pdf_document_urls(comment_urls)
                comment_urls = comment_urls.difference(comment_pdf_documents)

                urls.update(comment_urls)
                revisions.update(comment_revisions)
                mailing_lists.update(comment_mailing_lists)
                pdf_documents.update(comment_pdf_documents)

            for issue in data["issue_links"]:
                other_issues.add(issue["issue_key"])

            remote_links = [remote_link["url"] for remote_link in data["remote_links"]]
            urls.update(remote_links)
            issues.append(
                (issue_key, issue_id, urls, revisions, mailing_lists, pdf_documents, other_issues)
            )
    return issues


def save_references(project: str,
                    issues: List[Tuple[str, int, Set[str], Set[str], Set[str], Set[str], Set[str]]]) -> None:
    """
    Save references for each issue in JSON format
    :param project: Project to write references for
    :param issues: Data type describing necessary data
    :return: None
    """
    reference_dir = os.path.join("Projects", project, "References")

    shutil.rmtree(reference_dir, ignore_errors=True)
    os.mkdir(reference_dir)

    for issue in issues:
        issue_dict = dict()
        issue_dict["issue_key"] = issue[0]
        issue_dict["issue_id"] = issue[1]
        issue_dict["urls"] = list(issue[2])  # parser.parse_issues(parser.load_issues())
        # utils.extract_and_save_urls_from_directory(input_directory=os.path.join("Projects", project, "Issues"),
        #                                            output_directory=os.path.join("Projects", project, "URLs"))
        # statistics = generate_statistics("PDFBOX")
        #
        issue_dict["revisions"] = list(issue[3])
        issue_dict["mailing_lists"] = list(issue[4])
        issue_dict["pdf_documents"] = list(issue[5])
        issue_dict["other_issues"] = list(issue[6])
        path = os.path.join(reference_dir, issue[0] + ".json")
        utils.save_as_json(issue_dict, path)


def generate_statistics(project: str):
    """
    Based on the references for each issue, generate the frequency of each type of references and split the data
    into blocks of 100 issues for a broader analysis of the data.
    :param project: Project to parse references from
    :return: Generated statistics
    #TODO better documentation
    """
    issues = []
    reference_directory = os.path.join("Projects", project, "References")

    for filename in os.listdir(reference_directory):
        path = os.path.join(reference_directory, filename)
        with open(path, 'r') as file:
            data = json.load(file)
            issues.append(
                (str(data["issue_key"]),
                 int(data["issue_id"]),
                 list(data["urls"]),
                 list(data["revisions"]),
                 list(data["mailing_lists"]),
                 list(data["pdf_documents"]),
                 list(data["other_issues"]))
            )
    issues = sorted(issues, key=lambda x: x[1])

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

    block_idx = 1
    statistics = []
    for block in blocks:
        total = 0
        revisions = 0
        mailing_lists = 0
        pdf_documents = 0
        other_urls = 0
        for issue in block:
            revisions += len(issue[3])
            mailing_lists += len(issue[4])
            pdf_documents += len(issue[5])
            other_urls += len(issue[2])
            for i in range(2, 6):
                total += len(issue[i])
        statistics.append((block_idx * 100, total, revisions, mailing_lists, pdf_documents, other_urls))
        block_idx += 1
    return statistics


def make_plot(project: str, statistics: List[Tuple[int, int, int, int, int, int]], blocks: List[int], param_idx: int,
              param_title: str):
    x = blocks
    y = [param[param_idx] for param in statistics]
    plt.plot(x, y)
    plt.xlabel("Issue IDs")
    plt.ylabel("Frequency of {}".format(param_title))
    plt.title("Changes in frequency of {} through the evolution of the project {}".format(param_title, project))
    plt.savefig(os.path.join("Plots", project, param_title + ".png"), bbox_inches='tight')
    plt.close()


def make_plots(project: str, statistics: List[Tuple[int, int, int, int, int, int]]):
    blocks = [param[0] for param in statistics]
    types = [
        (1, "Total references"),
        (2, "Revisions"),
        (3, "Mailing Lists"),
        (4, "PDF documents"),
        (5, "Other URLs")
    ]

    plots_dir = "Plots"
    shutil.rmtree(plots_dir, ignore_errors=True)
    os.makedirs(os.path.join(plots_dir, project))
    for t in types:
        make_plot(project, statistics, blocks, t[0], t[1])


project = "DERBY"
parser = JiraParser(project)
issues = parser.fetch_issues(save=True)
parser.fetch_comments()
parser.parse_issues(issues)

issues_summary = collect_issues_summary(project)
save_references(project, issues_summary)
generate_statistics(project)