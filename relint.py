import argparse
import fnmatch
import glob
import re
from collections import namedtuple
from itertools import chain

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


def lint_file(filename, tests):
    try:
        with open(filename) as fs:
            content = fs.read()
    except (IsADirectoryError, UnicodeDecodeError):
        pass
    else:
        for test in tests:
            if any(fnmatch.fnmatch(filename, fp) for fp in test.filename):
                for match in test.pattern.finditer(content):
                    yield filename, test, match


def main():
    args = parse_args()
    paths = {
        path
        for file in args.files
        for path in glob.iglob(file, recursive=True)
    }

    tests = list(load_config(args.config))

    matches = chain.from_iterable(
        lint_file(path, tests)
        for path in paths
    )

    _filename = ''
    lines = []

    exit_code = 0

    for filename, test, match in matches:
        exit_code = test.error if exit_code == 0 else exit_code
        if filename != _filename:
            _filename = filename
            lines = match.string.splitlines()

        line_no = match.string[:match.start()].count('\n')
        output_format = "{filename}:{line_no} {test.name}"
        print(output_format.format(
            filename=filename, line_no=line_no + 1, test=test,
        ))
        if test.hint:
            print("Hint:", test.hint)
        print(">   ", lines[line_no])

    exit(exit_code)


if __name__ == '__main__':
    main()
