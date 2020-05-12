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


def filter_pdf_document_urls(urls: Set[str]) -> Set[str]:
    """
    Filter URLs leading to PDF documents. Usually, if there is a URL to a PDF document inside discussions, there is a
    high chance that this is a documentation.
    :param urls: List of URLs to filter PDF documents from
    :return: List of PDF document URLS
    """
    return set([url for url in urls if url.endswith(".pdf")])


def filter_mailing_list_urls(urls: Set[str]) -> Set[str]:
    """
    Filter URLs leading to mailing lists. This is a very rough implementation and should definitely be improved.
    :param urls: List of URLs to filter mailing lists from
    :return: List of mailing list URLs
    """
    return set([url for url in urls if "mail" in url])


def extract_and_save_urls_from_directory(input_directory: str, output_directory: str) -> None:
    """
    Extract URLs from each file in input_directory and
    save them in appropriate files in .txt format in output_directory.
    :param input_directory: Directory to read files from
    :param output_directory: Directory to write files to
    :return: None
    """
    if not os.path.exists(input_directory):
        print("Input directory does not exist!")
        return
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    input_files = os.listdir(input_directory)

    for input_file in input_files:
        input_path = os.path.join(input_directory, input_file)
        with open(input_path, "r") as file:
            urls = extract_urls(file.read())

        output_file = os.path.splitext(input_file)[0] + ".txt"
        output_path = os.path.join(output_directory, output_file)
        with open(output_path, 'w') as file:
            file.write('\n'.join(urls))
