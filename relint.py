import argparse
import fnmatch
import glob
import re
import sys
import warnings
from collections import namedtuple
from itertools import chain

import yaml

GIT_DIFF_LINE_NUMBERS_PATTERN = re.compile(
    r"@ -\d+(,\d+)? \+(\d+)(,)?(\d+)? @")
GIT_DIFF_FILENAME_PATTERN = re.compile(
    r"(?:\n|^)diff --git a\/.* b\/(.*)(?:\n|$)")
GIT_DIFF_SPLIT_PATTERN = re.compile(
    r"(?:\n|^)diff --git a\/.* b\/.*(?:\n|$)")


class RelintError(Exception):
    pass


class ConfigError(ValueError, RelintError):
    pass


Test = namedtuple(
    'Test', (
        'name',
        'pattern',
        'hint',
        'file_pattern',
        'filename',
        'error',
    )
)


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'files',
        metavar='FILE',
        type=str,
        nargs='+',
        help='Path to one or multiple files to be checked.'
    )
    parser.add_argument(
        '-c',
        '--config',
        metavar='CONFIG_FILE',
        type=str,
        default='.relint.yml',
        help='Path to config file, default: .relint.yml'
    )
    parser.add_argument(
        '-d',
        '--diff',
        action='store_true',
        help='Analyze content from git diff.'
    )
    parser.add_argument(
        '-W',
        '--fail-warnings',
        action='store_true',
        help='Fail for warnings.'
    )
    return parser.parse_args(args=args)


def load_config(path, fail_warnings):
    with open(path) as fs:
        try:
            for test in yaml.safe_load(fs):
                filename = test.get('filename')
                if filename:
                    warnings.warn(
                        "The glob style 'filename' configuration attribute has been"
                        " deprecated in favor of a new RegEx based 'filePattern' attribute."
                        " 'filename' support will be removed in relint version 2.0.",
                        DeprecationWarning
                    )
                    if not isinstance(filename, list):
                        filename = list(filename)
                file_pattern = test.get('filePattern', '.*')
                file_pattern = re.compile(file_pattern)
                yield Test(
                    name=test['name'],
                    pattern=re.compile(test['pattern'], re.MULTILINE),
                    hint=test.get('hint'),
                    file_pattern=file_pattern,
                    filename=filename,
                    error=test.get('error', True) or fail_warnings
                )
        except yaml.YAMLError as e:
            raise ConfigError("Error parsing your relint config file.") from e
        except TypeError:
            warnings.warn("Your relint config is empty, no tests were executed.", UserWarning)
        except (AttributeError, ValueError) as e:
            raise ConfigError(
                "Your relint config is not a valid YAML list of relint tests."
            ) from e


def lint_file(filename, tests):
    try:
        with open(filename) as fs:
            content = fs.read()
    except (IsADirectoryError, UnicodeDecodeError):
        pass
    else:
        for test in tests:
            if test.filename:
                if any(fnmatch.fnmatch(filename, fp) for fp in test.filename):
                    for match in test.pattern.finditer(content):
                        line_number = match.string[:match.start()].count('\n') + 1
                        yield filename, test, match, line_number
            else:
                if test.file_pattern.match(filename):
                    for match in test.pattern.finditer(content):
                        line_number = match.string[:match.start()].count('\n') + 1
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


def split_diff_content_by_filename(output):
    """
    Split the output by filename.

    Args:
        output (int): ``git diff`` output.

    Returns:
        dict: Filename and its content.

    """
    content_by_filename = {}
    filenames = parse_filenames(output)
    splited_content = re.split(GIT_DIFF_SPLIT_PATTERN, output)
    splited_content = filter(lambda x: x != '', splited_content)

    for filename, content in zip(filenames, splited_content):
        content_by_filename[filename] = content
    return content_by_filename


def print_culprits(matches):
    exit_code = 0
    _filename = ''
    lines = []

    for filename, test, match, _ in matches:
        exit_code = test.error if exit_code == 0 else exit_code

        if filename != _filename:
            _filename = filename
            lines = match.string.splitlines()

        start_line_no = match.string[:match.start()].count('\n')
        end_line_no = match.string[:match.end()].count('\n')
        output_format = "{filename}:{line_no} {test.name}"
        print(output_format.format(
            filename=filename, line_no=start_line_no + 1, test=test,
        ))
        if test.hint:
            print("Hint:", test.hint)
        match_lines = (
            "{line_no}>    {code_line}".format(
                line_no=no + start_line_no + 1,
                code_line=line,
            )
            for no, line in enumerate(lines[start_line_no:end_line_no + 1])
        )
        print(*match_lines, sep="\n")

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


def main(args=sys.argv[1:]):
    args = parse_args(args)
    paths = {
        path
        for file in args.files
        for path in glob.iglob(glob.escape(file), recursive=True)
    }

    tests = list(load_config(args.config, args.fail_warnings))

    matches = chain.from_iterable(
        lint_file(path, tests)
        for path in paths
    )

    if args.diff:
        output = sys.stdin.read()
        changed_content = parse_diff(output)
        matches = match_with_diff_changes(changed_content, matches)

    exit_code = print_culprits(matches)
    exit(exit_code)


if not sys.warnoptions:
    warnings.simplefilter('default')


if __name__ == '__main__':
    main()
