from JiraAnalyzer.jira_parser import JiraParser
import re

URL_REGEX = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
PROJECTS = ["PDFBOX"]

url_pattern = re.compile(URL_REGEX)
parser = JiraParser(PROJECTS[0])
parser.fetch_and_store_comments()
