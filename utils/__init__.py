import argparse
import errno
import json
import os
from .ref_regex import *


def save_as_json(obj: object, path: str) -> None:
    with open(path, "w") as file:
        json.dump(obj, file, indent=2)


def load_json(path: str) -> dict:
    with open(path, "r") as file:
        loaded = json.load(file)
    return loaded


def create_dir_if_necessary(dir_path: str) -> None:
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise


def parse_arguments():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-j", "--jira-project", help="Target Jira project")
    return arg_parser.parse_args()


def construct_svn_revision_url(revision: str) -> str:
    """
    Extracts a revision ID and constructs a URL to SVN Apache.
    :param revision: Revision to build the URL to
    :return: URL
    """
    revision_id = extract_numbers(revision)[0]
    return "https://svn.apache.org/r{}".format(revision_id)


def filter_pdf_document_urls(urls: Set[str]) -> Set[str]:
    """
    Filter URLs leading to PDF documents. Usually, if there is a URL to a PDF document inside discussions, there is a
    high chance that this is a documentation.
    :param urls: List of URLs to filter PDF documents from
    :return: List of PDF document URLS
    """
    return set([url for url in urls if url.endswith(".pdf")])


def filter_mailing_list_urls(urls: Set[str], mailing_list_keys=None) -> Set[str]:
    """
    Filter URLs leading to mailing lists. This is a very rough implementation and should definitely be improved.
    :param urls: List of URLs to filter mailing lists from
    :param mailing_list_keys: If the URL is a mailing list, any entry from this list should be present in the URL.
    Otherwise, it checks whether the url contains "mail-archives" or "markmail".
    :return: List of mailing list URLs
    """
    if not mailing_list_keys:
        mailing_list_keys = ["mail-archives", "markmail"]
    return set([url for url in urls if any(key in url for key in mailing_list_keys)])


def atlassian_code_format_to_listing(string: str) -> str:
    string = string.replace(r"{code:java}", r"\begin{lstlisting}[language=Java]")
    string = string.replace(r"{code}", r"\end{lstlisting}")

    while string.find(r"{noformat}") != -1:
        string = string.replace(r"{noformat}", r"\begin{lstlisting}", 1)
        string = string.replace(r"{noformat}", r"\end{lstlisting}", 1)

    return string
