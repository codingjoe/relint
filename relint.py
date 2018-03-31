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


Test = namedtuple('Test', ('name', 'pattern', 'hint', 'filename'))


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
        exit_code = 1
        if filename != _filename:
            _filename = filename
            lines = match.string.splitlines()

        line_no = match.string[:match.start()].count('\n')
        print(f"{filename}:{line_no + 1} {test.name}")
        if test.hint:
            print("Hint:", test.hint)
        print(">   ", lines[line_no])

    exit(exit_code)


if __name__ == '__main__':
    main()
