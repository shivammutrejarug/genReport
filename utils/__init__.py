import argparse
import json
from .ref_regex import *


def save_as_json(obj: object, path: str):
    with open(path, "w") as file:
        json.dump(obj, file, indent=2)


def parse_arguments():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-j", "--jira-project", help="Target Jira project")
    return arg_parser.parse_args()


def construct_svn_revision_url(revision: str) -> str:
    revision_id = int(extract_numbers(revision)[0])
    return "https://svn.apache.org/r{}".format(revision_id)
