import re

from typing import List, Set

# Regex developed by Diego Perini: https://gist.github.com/dperini/729294
# Was converted from JS to Python using https://regex101.com/
URL_REGEX = r"(?:(?:(?:https?|ftp):)?\/\/)(?:\S+(?::\S*)?@)?(?:(?!(?:10|127)" \
            r"(?:\.\d{1,3}){3})(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})(?!172\." \
            r"(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])" \
            r"(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))" \
            r"|(?:(?:[a-z0-9\u00a1-\uffff][a-z0-9\u00a1-\uffff_-]{0,62})?[a-z0-9\u00a1-\uffff]\.)" \
            r"+(?:[a-z\u00a1-\uffff]{2,}\.?))(?::\d{2,5})?(?:[/?#]\S*)?"
REVISION_REGEX = r"(?:r|[Rr]ev. |[Rr]evision |[Cc]ommit )([0-9]+)"
NUMBER_REGEX = r"d+"

url_matcher = re.compile(URL_REGEX)
revision_matcher = re.compile(REVISION_REGEX)
number_matcher = re.compile(NUMBER_REGEX)


def extract_urls(text: str, project: str, filter_revisions=True, filter_issues=True) -> Set[str]:
    """
    Extract unique URLs from the text. If filter_revisions set to True, all URLs belonging to SVN revisions are ignored.
    :param text: Text to extract URLs from
    :param project: Project name to filter URLs to issues
    :param filter_revisions: Whether to ignore SVN revision URLs
    :param filter_issues: Whether to filter other issues links
    :return: Set of extracted URLs
    """

    urls = set(url_matcher.findall(text))
    urls = set(
        map(
            # if a URL ends with '.', '\' or '?', then we should remove that character
            lambda url: url[:-1] if url[-1] in ['.', '\\', '?'] else url,
            urls
        )
    )
    if filter_revisions:
        urls = set(
            filter(
                lambda url: not url.startswith("https://svn.apache.org"),
                urls
            )
        )
    if filter_issues:
        urls = set(
            filter(
                lambda url: not extract_issues(url, project),
                urls
            )
        )
    return urls


def extract_issues(text: str, project_name: str) -> Set[str]:
    """
    Extract all issue IDs from the text. Each issue ID has the form <project_name>-{int_id}.
    :param text: Text to extract issue IDs from
    :param project_name: Name of the project to match issue IDs
    :return: List of issue IDs
    """
    issue_matcher = re.compile("{}-{}".format(project_name, r'\d+'))
    return set(issue_matcher.findall(text))


def extract_revisions(text: str) -> Set[str]:
    """
    Extract all revision IDs mentioned in the text.
    :param text: Text to extract revisions IDs from
    :return: List containing extracted revision IDs
    """
    return set(revision_matcher.findall(text))


def extract_numbers(text: str) -> List[int]:
    """
    Extract numbers from the text.
    :param text: Text to extract numbers from
    :return: List of strings containing a single number each
    """
    return list(
        map(
            lambda number: int(number),
            re.findall(r'\d+', text)
        )
    )


def clear_text(text: str) -> str:
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
    :return: Cleared text
    """
    chars_to_remove = [r'\n', '[', ']', '<', '>', '\\']
    for char in chars_to_remove:
        text = text.replace(char, ' ')
    return text
