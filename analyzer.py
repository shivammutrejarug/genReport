import json
from jiraanalyzer import JiraParser
import os
import pickle
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


def retrieve_and_save_issues(projects: List[str]) -> None:
    for project in projects:
        print("Fetching project {}".format(project))
        parser = JiraParser(project)
        parser.fetch_issues()

        parser.fetch_and_save_comments()
        utils.extract_and_save_urls_from_directory(input_directory=os.path.join("Projects", project, "Issues"),
                                                   output_directory=os.path.join("Projects", project, "URLs"))


args = utils.parse_arguments()
projects = [args.jira_project] if args.jira_project else PROJECTS


# ALREADY DONE
# retrieve_and_save_issues(projects)


def collect_issues_summary(project: str) -> List[Tuple[str, int, Set[str], Set[str], Set[str], Set[str]]]:
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

            issues.append(
                (issue_key, issue_id, urls, revisions, mailing_lists, pdf_documents)
            )
    return issues


def save_references(project: str, issues: List[Tuple[str, int, Set[str], Set[str], Set[str], Set[str]]]) -> None:
    reference_directory = os.path.join("Projects", project, "References")

    shutil.rmtree(reference_directory, ignore_errors=True)
    os.mkdir(reference_directory)

    for issue in issues:
        issue_dict = dict()
        issue_dict["issue_key"] = issue[0]
        issue_dict["issue_id"] = issue[1]
        issue_dict["urls"] = list(issue[2])
        issue_dict["revisions"] = list(issue[3])
        issue_dict["mailing_lists"] = list(issue[4])
        issue_dict["pdf_documents"] = list(issue[5])
        path = os.path.join(reference_directory, issue[0] + ".json")
        utils.save_as_json(issue_dict, path)


issues = collect_issues_summary("PDFBOX")
# with open("issues_summary_backup.P", 'w') as backup_file:
#     pickle.dump(issues, backup_file)
# with open("issues_summary_backup.P", 'r') as backup_file:
#     issues = pickle.load(backup_file)

save_references("PDFBOX", issues)
