from __future__ import annotations

import re

GIT_DIFF_LINE_NUMBERS_PATTERN = re.compile(r"@ -\d+(,\d+)? \+(\d+)(,)?(\d+)? @")
GIT_DIFF_FILENAME_PATTERN = re.compile(r"(?:\n|^)diff --git a\/.* b\/(.*)(?:\n|$)")
GIT_DIFF_SPLIT_PATTERN = re.compile(r"(?:\n|^)diff --git a\/.* b\/.*(?:\n|$)")


def lint_file(filename, tests):
    try:
        with open(filename) as fs:
            content = fs.read()
    except (IsADirectoryError, UnicodeDecodeError):
        pass
    else:
        for test in tests:
            if test.file_pattern.match(filename):
                for match in test.pattern.finditer(content):
                    line_number = match.string[: match.start()].count("\n") + 1
                    yield filename, test, match, line_number


def parse_line_numbers(output):
    """
    Extract line numbers from ``git diff`` output.

    Git shows which lines were changed indicating a start line
    and how many lines were changed from that. If only one
    line was changed, the output will display only the start line,
    like this:
    ``@@ -54 +54 @@ import glob``
    If more lines were changed from that point, it will show
    how many after a comma:
    ``@@ -4,2 +4,2 @@ import glob``
    It means that line number 4 and the following 2 lines were changed
    (5 and 6).

    Args:
        output (int): ``git diff`` output.

    Returns:
        list: All changed line numbers.

    """
    line_numbers = []
    matches = GIT_DIFF_LINE_NUMBERS_PATTERN.finditer(output)

    for match in matches:
        start = int(match.group(2))
        if match.group(4) is not None:
            end = start + int(match.group(4))
            line_numbers.extend(range(start, end))
        else:
            line_numbers.append(start)

    return line_numbers


def parse_filenames(output):
    return re.findall(GIT_DIFF_FILENAME_PATTERN, output)


def split_diff_content_by_filename(output: str) -> {str: str}:
    """
    Split the output by filename.

    Args:
        output (int): ``git diff`` output.

    Returns:
        dict: Filename and its content.

    """
    content_by_filename = {}
    filenames = parse_filenames(output)
    split_content = re.split(GIT_DIFF_SPLIT_PATTERN, output)
    split_content = filter(lambda x: x != "", split_content)

    for filename, content in zip(filenames, split_content):
        content_by_filename[filename] = content
    return content_by_filename


def print_culprits(matches, msg_template):
    exit_code = 0
    _filename = ""
    lines = []

    for filename, test, match, _ in matches:
        exit_code = test.error if exit_code == 0 else exit_code

        if filename != _filename:
            _filename = filename
            lines = match.string.splitlines()

        start_line_no = match.string[: match.start()].count("\n")
        end_line_no = match.string[: match.end()].count("\n")
        match_lines = (
            "{line_no}>    {code_line}".format(
                line_no=no + start_line_no + 1,
                code_line=line.lstrip(),
            )
            for no, line in enumerate(lines[start_line_no : end_line_no + 1])
        )
        # special characters from shell are escaped
        msg_template = msg_template.replace("\\n", "\n")
        print(
            msg_template.format(
                filename=filename,
                line_no=start_line_no + 1,
                test=test,
                match=chr(10).join(match_lines),
            )
        )

    return exit_code


def match_with_diff_changes(content, matches):
    """Check matches found on diff output."""
    for filename, test, match, line_number in matches:
        if content.get(filename) and line_number in content.get(filename):
            yield filename, test, match, line_number


def parse_diff(output):
    """Parse changed content by file."""
    changed_content = {}
    for filename, content in split_diff_content_by_filename(output).items():
        changed_line_numbers = parse_line_numbers(content)
        changed_content[filename] = changed_line_numbers
    return changed_content
