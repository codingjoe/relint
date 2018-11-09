import argparse
import fnmatch
import glob
import re
from collections import namedtuple
import subprocess  # nosec
import yaml


def parse_args():
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
    return parser.parse_args()


Test = namedtuple('Test', ('name', 'pattern', 'hint', 'filename', 'error'))


def load_config(path):
    with open(path) as fs:
        for test in yaml.load(fs):
            filename = test.get('filename', ['*'])
            if not isinstance(filename, list):
                filename = list(filename)
            yield Test(
                name=test['name'],
                pattern=re.compile(test['pattern']),
                hint=test.get('hint'),
                filename=filename,
                error=test.get('error', True)
            )


def lint_file(content, tests):
    for test in tests:
        for filename, content in content.items():

            if any(fnmatch.fnmatch(filename, fp) for fp in test.filename):
                for predefined_line_number, line in content.items():
                    for match in test.pattern.finditer(line):
                        start_line_no = match.string[:match.start()].count('\n')

                        if predefined_line_number is None:  # whole content
                            line_number = start_line_no + 1
                        else:
                            line_number = predefined_line_number

                        lines = match.string.splitlines()
                        yield filename, test, lines[start_line_no], line_number


def parse_diff(output):
    changed_content = {}
    current_file = None
    line_after_number_line = False
    current_line = None

    pattern = re.compile(r"(([+]|[-])\d*[,]?\d*)")

    for line in output.splitlines():
        if line.startswith('diff'):
            current_file = line[line.rfind(' b/')+3:]
            line_after_number_line = False

        elif line.startswith('@@'):
            result = pattern.findall(line)
            result = result[1][0].replace('+', '').split(',')
            if result:
                current_line = int(result[0])
            line_after_number_line = True

        elif line_after_number_line and line.startswith('+'):
            if changed_content.get(current_file):
                changed_content[current_file][current_line] = line[1:]
            else:
                changed_content[current_file] = {
                    current_line: line[1:]
                }
            current_line += 1

    return changed_content


def print_culprits(matches):
    exit_code = 0

    for filename, test, match, line_number in matches:
        exit_code = test.error if exit_code == 0 else exit_code

        output_format = "{filename}:{line_no} {test.name}"
        print(output_format.format(
            filename=filename, line_no=line_number, test=test,
        ))
        if test.hint:
            print("Hint:", test.hint)

        print("{line_no}>    {code_line}".format(
            line_no=line_number,
            code_line=match,
        ))

    return exit_code


def filter_paths_from_diff(content, paths):
    filtered_content = content.copy()
    for filename in content.keys():
        if filename not in paths:
            del filtered_content[filename]
    return filtered_content


def content_from_paths(paths):
    contents = {}

    for filename in paths:
        try:
            with open(filename) as fs:
                contents[filename] = {
                    None: fs.read()
                }
        except (IsADirectoryError, UnicodeDecodeError):
            pass

    return contents


def main():
    args = parse_args()
    paths = {
        path
        for file in args.files
        for path in glob.iglob(file, recursive=True)
    }

    tests = list(load_config(args.config))

    if args.diff:
        git_command = ['git', 'diff', '-U0', '--cached']
        output = subprocess.check_output(git_command, encoding='utf-8')
        content = parse_diff(output)
        content = filter_paths_from_diff(content, paths)
    else:
        content = content_from_paths(paths)

    matches = lint_file(content, tests)
    exit_code = print_culprits(matches)
    exit(exit_code)


if __name__ == '__main__':
    main()
