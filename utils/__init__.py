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


def filter_pdf_document_urls(urls: List[str]) -> List[str]:
    """
    Filter URLs leading to PDF documents. Usually, if there is a URL to a PDF document inside discussions, there is a
    high chance that this is a documentation.
    :param urls: List of URLs to filter PDF documents from
    :return: List of PDF document URLS
    """
    return [url for url in urls if url.endswith(".pdf")]


def filter_mailing_list_urls(urls: List[str]) -> List[str]:
    """
    Filter URLs leading to mailing lists. This is a very rough implementation and should definitely be improved.
    :param urls: List of URLs to filter mailing lists from
    :return: List of mailing list URLs
    """
    return [url for url in urls if "mail" in url]
