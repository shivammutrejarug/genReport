import argparse
from typing import List, Optional
from jira.exceptions import JIRAError

import genreport
import utils

__EXCLUDE_SECTIONS = {"summary", "description", "attachments", "commits", "pull_requests", "comments", "other_issues"}


def __parse_arguments() -> argparse.Namespace:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-p", "--project", help="Jira project in capital letters", required=True)
    arg_parser.add_argument("-g", "--github", help="Target Jira project's GitHub repository")
    arg_parser.add_argument("-b", "--bots", help="List of bots to exclude from report, separated by comma")
    arg_parser.add_argument("-i", "--issues", help="Issues to generate reports for, separated by comma and/or"
                                                   "defined as ranges. For example, \"124,136-152,174\"", required=True)
    arg_parser.add_argument("-e", "--exclude", help="Sections to skip when generating report, separated by comma."
                                                    "Sections are: [summary, description, attachments, commits, "
                                                    "pull_requests, comments, other_issues]")
    return arg_parser.parse_args()


def __define_issues(issues_arg: str) -> Optional[List[str]]:
    if not issues_arg:
        print("You should specify at least one issue.")
        return None
    issues = []
    for issues_entry in utils.split_and_strip(issues_arg, ','):
        if issues_entry.isdecimal():  # If it is a single issue
            issues.append(issues_entry)
        else:
            issues_range = utils.split_and_strip(issues_entry, '-')
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
    return [exclude for exclude in exclude_list if exclude not in __EXCLUDE_SECTIONS]


if __name__ == "__main__":
    github, bots, issues, exclude = None, None, None, None

    args = __parse_arguments()
    project = args.project
    if args.github:
        github = args.github
    if args.bots:
        bots = utils.split_and_strip(args.bots, ',')
    if args.exclude:
        exclude = utils.split_and_strip(args.exclude, ',')
        invalid_sections = __validate_exclude_list(exclude)
        if invalid_sections:
            print("Invalid sections to exclude: {}. Aborting...".format(", ".join(invalid_sections)))
            exit(-1)
        elif len(invalid_sections) == 7:
            print("All sections are excluded. Aborting...")
            exit(0)
    issues = __define_issues(args.issues)
    if not issues:
        print("Aborting...")
        exit(-1)

    for issue in issues:
        issue_key = "{}-{}".format(project, issue)
        print("{}: generating report".format(issue_key))
        try:
            generator = genreport.ReportGenerator(project, issue_key, github, bots, exclude)
            generator.generate_report()
        except JIRAError:
            print("{}: issue does not exist. Aborting...".format(issue_key))
            exit(-1)
