import argparse
import json
import os
import re

from typing import List

# Taken from http://www.noah.org/wiki/RegEx_Python#URL_regex_pattern
URL_REGEX = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
url_pattern = re.compile(URL_REGEX)


def save_as_json(obj: object, path: str):
    with open(path, "w") as file:
        json.dump(obj, file, indent=2)


def extract_urls_from_string(string: str) -> List[str]:
    return url_pattern.findall(string)


def parse_arguments():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-j", "--jira-project", help="Target Jira project")
    return arg_parser.parse_args()


def extract_urls(input_directory: str, output_directory: str) -> None:
    """
    Extract URLs from each file in input_directory and
    save them in appropriate files in .txt format in output_directory.
    :param input_directory: Directory to read files from
    :param output_directory: Directory to write files to
    :return: None
    """
    if not os.path.exists(input_directory):
        return
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    input_files = os.listdir(input_directory)

    for input_file in input_files:
        input_path = os.path.join(input_directory, input_file)
        with open(input_path, "r") as file:
            urls = url_pattern.findall(clean_text(file.read()))

            urls = list(
                map(
                    # if a URL ends with '.', '\' or '?', then we should remove that character
                    lambda url: url[:-1] if url[-1] in ['.', '\\', '?'] else url,
                    urls
                )
            )
        file.close()

        output_file = os.path.splitext(input_file)[0] + ".txt"
        output_path = os.path.join(output_directory, output_file)
        with open(output_path, 'w') as file:
            file.write('\n'.join(urls))
        file.close()


def clean_text(text: str) -> str:
    """
    Prepare text to be parsed by URL regex.
    By now, the regex doesn't parse URLs 100% correctly, so they may end up having redundant characters.

    The reason is that the regex tries to catch all possible formats of URLs, including those which are typed by hand.
    Such URLS may contain specific characters like brackets, '<', '>' and backslash.
    Developers usually just copy-paste URLs from a browser's address bar, and browsers, for their part, have those URLs
    already formatted to exclude those characters (e.g. '[' -> "%5B", ')' -> "%29")

    TODO: Either:
        1. Adjust the regex to match URLs already formatted by a browser
        2. Join replace() calls below into a regex
    :param text: Text to remove characters from
    :return: Cleaned text
    """
    chars_to_remove = [r'\n', '(', ')', '[', ']', '<', '>', '\\']
    for char in chars_to_remove:
        text = text.replace(char, ' ')
    return text


if __name__ == "__main__":
    project = "PDFBOX"
    extract_urls(input_directory=os.path.join("..", "Projects", project, "Issues"),
                 output_directory=os.path.join("..", "Projects", project, "URLs"))
