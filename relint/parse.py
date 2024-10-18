from __future__ import annotations

import collections

try:
    import regex as re
except ImportError:
    import re

from rich import print as rprint
from rich.console import Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax

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
    return GIT_DIFF_FILENAME_PATTERN.findall(output)


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
    split_content = GIT_DIFF_SPLIT_PATTERN.split(output)
    split_content = filter(lambda x: x != "", split_content)

    for filename, content in zip(filenames, split_content):
        content_by_filename[filename] = content
    return content_by_filename


def print_github_actions_output(matches, args):
    exit_code = 0
    for filename, test, match, line_number in matches:
        exit_code = test.error if exit_code == 0 else exit_code
        start_line_no = match.string[: match.start()].count("\n") + 1
        end_line_no = match.string[: match.end()].count("\n") + 1
        col = match.start() - match.string.rfind("\n", 0, match.start())
        col_end = match.end() - match.string.rfind("\n", 0, match.end())

        print(
            f"::{'error' if test.error else 'warning'} file={filename},"
            f"line={start_line_no},endLine={end_line_no},col={col},colEnd={col_end},"
            f"title={test.name}::{test.hint}".replace("\n", "%0A")
        )
    return exit_code


def print_culprits(matches, args):
    exit_code = 0
    messages = []
    match_groups = collections.defaultdict(list)

    for filename, test, match, _ in matches:
        exit_code = test.error if exit_code == 0 else exit_code

        start_line_no = match.string[: match.start()].count("\n") + 1
        end_line_no = match.string[: match.end()].count("\n") + 1

        if args.summarize:
            match_groups[test].append(f"{filename}:{start_line_no}")
        else:
            message_bits = []

            if args.code_padding != -1:
                lexer = Syntax.guess_lexer(filename)
                message_bits.append(
                    Syntax(
                        match.string,
                        lexer=lexer,
                        line_numbers=True,
                        line_range=(
                            start_line_no - args.code_padding,
                            end_line_no + args.code_padding,
                        ),
                        highlight_lines=range(start_line_no, end_line_no + 1),
                    )
                )

            if test.hint:
                message_bits.append(
                    Panel(
                        Markdown(test.hint, justify="left"),
                        title="Hint:",
                        title_align="left",
                        padding=(0, 2),
                    )
                )

            messages.append(
                Panel(
                    Group(*message_bits),
                    title=f"{'Error' if test.error else 'Warning'}: {test.name}",
                    title_align="left",
                    subtitle=f"{filename}:{start_line_no}",
                    subtitle_align="left",
                    border_style="bold red" if test.error else "yellow",
                    padding=(0, 2),
                )
            )

    if args.summarize:
        for test, filenames in match_groups.items():
            group = Group(*filenames)
            if test.hint:
                group = Group(
                    group,
                    Panel(
                        Markdown(test.hint, justify="left"),
                        title="Hint:",
                        title_align="left",
                        padding=(0, 2),
                    ),
                )

            messages.append(
                Panel(
                    group,
                    title=f"{'Error' if test.error else 'Warning'}: {test.name}",
                    title_align="left",
                    subtitle=f"{len(filenames)} occurrence(s)",
                    subtitle_align="left",
                    border_style="bold red" if test.error else "yellow",
                    padding=(0, 2),
                )
            )

    rprint(*messages, sep="\n")

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
