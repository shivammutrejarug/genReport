from jiraanalyzer.jiraparser import JiraParser
import os
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
for project in projects:
    print("Fetching project {}".format(project))
    parser = JiraParser(project)
    issues = parser.fetch_issues()

    parser.fetch_and_save_comments()
    utils.extract_urls(input_directory=os.path.join("Projects", project, "Issues"),
                       output_directory=os.path.join("Projects", project, "URLs"))
