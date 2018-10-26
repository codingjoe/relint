import argparse
import fnmatch
import glob
import re
from collections import namedtuple
from itertools import chain
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
        '--config',
        '-c',
        metavar='CONFIG_FILE',
        type=str,
        default='.relint.yml',
        help='Path to config file, default: .relint.yml'
    )
    parser.add_argument(
        '--diff',
        '-d',
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


def lint_file(filename, tests, diff=None):
    if diff and diff.get(filename):
        for test in tests:
            for line_number, content in diff.get(filename).items():
                for match in test.pattern.finditer(content):
                    yield filename, test, match, line_number
    else:
        try:
            with open(filename) as fs:
                content = fs.read()
        except (IsADirectoryError, UnicodeDecodeError):
            pass
        else:
            for test in tests:
                if any(fnmatch.fnmatch(filename, fp) for fp in test.filename):
                    for match in test.pattern.finditer(content):
                        yield filename, test, match, None


def parse_diff(output):
    changed_content = {}
    current_file = None
    line_after_number_line = False
    current_line = None

    for line in output.split('\n'):
        if line.startswith('diff'):
            current_file = line[line.rfind(' b/')+3:]
            line_after_number_line = False

        elif line.startswith('@@'):
            result = re.findall(r'(([+]|[-])\d*[,]?\d*)', line)
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


def main():
    args = parse_args()
    paths = {
        path
        for file in args.files
        for path in glob.iglob(file, recursive=True)
    }

    tests = list(load_config(args.config))

    diff = None
    if args.diff:
        output = subprocess.run(['git', 'diff', '-U0'], stdout=subprocess.PIPE)
        diff = parse_diff(output.stdout.decode('utf-8'))

    matches = chain.from_iterable(
        lint_file(path, tests, diff)
        for path in paths
    )

    _filename = ''
    lines = []

    exit_code = 0

    if diff:
        for filename, test, match, line_number in matches:
            exit_code = test.error if exit_code == 0 else exit_code

            output_format = "{filename}:{line_no} {test.name}"
            print(output_format.format(
                filename=filename, line_no=line_number, test=test,
            ))

            if test.hint:
                print("Hint:", test.hint)

            print("{line_no}>    {code_line}\n".format(
                line_no=line_number,
                code_line=match.string,
            ))
    else:
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

    exit(exit_code)


if __name__ == '__main__':
    main()
