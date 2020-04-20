from jira_analyzer.jira_parser import JiraParser
import os
import utils

PROJECTS = ["PDFBOX"]

args = utils.parse_arguments()
jira_project = args.jira_project if args.jira_project else PROJECTS[0]
parser = JiraParser(jira_project)

parser.fetch_and_save_comments()
utils.extract_urls(input_directory=os.path.join("Projects", jira_project, "Issues"),
                   output_directory=os.path.join("Projects", jira_project, "URLs"))
