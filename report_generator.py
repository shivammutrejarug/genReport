import argparse
from typing import List, Optional
from jira.exceptions import JIRAError

import genreport
import utils

__EXCLUDE_SECTIONS = {"summary", "description", "attachments", "commits", "pull_requests", "comments", "other_issues"}


def __parse_arguments() -> argparse.Namespace:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-p", "--project", help="Jira project in capital letters", required=True)
    arg_parser.add_argument("-i", "--issues", help="Issues to generate reports for, separated by comma and/or"
                                                   "defined as ranges. For example, \"124,136-152,174\"", required=True)
    arg_parser.add_argument("-g", "--github", help="Target Jira project's GitHub repository")
    arg_parser.add_argument("-c", "--credentials", help="GitHub username and API key separated by comma. "
                                                        "Compulsory if GitHub repository is specified")
    arg_parser.add_argument("-b", "--bots", help="List of bots to exclude from report, separated by comma")
    arg_parser.add_argument("-e", "--exclude", help="Sections to skip when generating report, separated by comma."
                                                    "Sections are: [summary, description, attachments, commits, "
                                                    "pull_requests, comments, other_issues]")
    return arg_parser.parse_args()


def __define_issues(issues_arg: str) -> Optional[List[str]]:
    """
    Split the string of issues into the list of issues. Returns None if failed to parse issues.
    :param issues_arg: String representing issues and issue ranges separated by comma
    :return: List of parsed issues
    """
    if not issues_arg:
        print("You should specify at least one issue.")
        return None
    issues = []
    for issues_entry in utils.split_and_strip(issues_arg, ','):
        if issues_entry.isdecimal():  # If it is a single issue
            issues.append(issues_entry)
        else:
            issues_range = utils.split_and_strip(issues_entry, '-')  # Split the range of issues, e.g. 123-130
            if len(issues_range) != 2 or not issues_range[0].isdecimal() or not issues_range[1].isdecimal():
                print("Invalid issues list format.")
                return None

            first_issue = int(issues_range[0])
            last_issue = int(issues_range[1])
            if last_issue < first_issue:
                print("The range should be from smaller to bigger.")
                return None

            for issue in range(first_issue, last_issue + 1):
                issues.append(str(issue))
    issues.sort()
    return issues


def __validate_exclude_list(exclude_list: List[str]) -> List[str]:
    """
    Returns the list of invalid sections to exclude.
    :param exclude_list: List of sections to check for being valid
    :return: List of invalid sections
    """
    return [exclude for exclude in exclude_list if exclude not in __EXCLUDE_SECTIONS]


if __name__ == "__main__":
    github, github_credentials, bots, issues, exclude = None, None, None, None, None

    args = __parse_arguments()
    project = args.project

    # If GitHub repository and credentiols are specified
    if args.github:
        github = args.github
        if args.credentials is None:
            print("You should specify GitHub credentials as well. For example:\n"
                  "--credentials \"github_username, API key\"\n"
                  "-c \"github_username, API key\"")
            exit(-1)
        else:
            github_credentials = utils.define_github_credentials(args.credentials)

    # If the list of bots is specified
    if args.bots:
        bots = utils.split_and_strip(args.bots, ',')

    # If the list of sections to exclude is specified
    if args.exclude:
        exclude = utils.split_and_strip(args.exclude, ',')
        invalid_sections = __validate_exclude_list(exclude)
        if invalid_sections:
            print("Invalid sections to exclude: {}. Aborting...".format(", ".join(invalid_sections)))
            exit(-1)
        elif len(exclude) == 7:
            print("All sections are excluded. Aborting...")
            exit(0)

    issues = __define_issues(args.issues)
    # If the list of issues passed is invalid (e.g. they are passed as an empty string
    # or string containing invalid characters.
    if not issues:
        print("Aborting...")
        exit(-1)

    for issue in issues:
        issue_key = "{}-{}".format(project, issue)
        print("{}: generating report".format(issue_key))
        try:
            generator = genreport.ReportGenerator(project, issue_key, github, github_credentials, bots, exclude)
            generator.generate_report()
        except JIRAError:
            print("{}: issue does not exist. Aborting...".format(issue_key))
            exit(-1)
