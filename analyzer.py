from JiraAnalyzer.jira_parser import JiraParser
import utils

PROJECTS = ["PDFBOX"]

parser = JiraParser(PROJECTS[0])
parser.fetch_and_store_comments()

# This is just an example of URL extraction from a string
example_string = "If you want to reach https://www.wikipedia.org/ from Google, you should enter the following URL: https://www.google.com/search?q=wikipedia&oq=wikipedia&aqs=chrome.0.69i59j0l3j69i65j69i60l3.2620j0j7&sourceid=chrome&ie=UTF-8"
print(utils.extract_urls_from_string(example_string))
