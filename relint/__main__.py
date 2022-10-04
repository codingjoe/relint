import argparse
import glob
import subprocess  # nosec
import sys
import warnings
from itertools import chain

from relint.config import load_config
from relint.parse import lint_file, match_with_diff_changes, parse_diff, print_culprits


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show relint version and exit.",
    )
    parser.add_argument(
        "files",
        metavar="FILE",
        type=str,
        nargs="*",
        help="Path to one or multiple files to be checked.",
    )
    parser.add_argument(
        "-c",
        "--config",
        metavar="CONFIG_FILE",
        type=str,
        default=".relint.yml",
        help="Path to config file, default: .relint.yml",
    )
    parser.add_argument(
        "-d", "--diff", action="store_true", help="Analyze content from a diff."
    )
    parser.add_argument(
        "--git-diff",
        action="store_true",
        help="Analyze content from git diff directly by calling `git diff --staged`.",
    )
    parser.add_argument(
        "-W", "--fail-warnings", action="store_true", help="Fail for warnings."
    )
    parser.add_argument(
        "--msg-template",
        metavar="MSG_TEMPLATE",
        type=str,
        default="{filename}:{line_no} {test.name}\nHint: {test.hint}\n{match}",
        help="Template used to display messages. "
        r"Default: {filename}:{line_no} {test.name}\nHint: {test.hint}\n{match}",
    )
    return parser.parse_args(args=args)


def main(args=sys.argv[1:]):
    args = parse_args(args)
    if args.version:
        from . import __version__

        print(f"relint: {__version__}")
        exit(0)
    paths = {
        path
        for file in args.files
        for path in glob.iglob(glob.escape(file), recursive=True)
    }

    tests = list(load_config(args.config, args.fail_warnings))

    matches = chain.from_iterable(lint_file(path, tests) for path in paths)

    if args.diff:
        output = sys.stdin.read()
    elif args.git_diff:
        output = subprocess.check_output(  # nosec
            ["git", "diff", "--staged", "--unified=0", "--no-color"],
            universal_newlines=True,
        )
    if args.diff or args.git_diff:
        changed_content = parse_diff(output)
        matches = match_with_diff_changes(changed_content, matches)

    exit_code = print_culprits(matches, args.msg_template)
    exit(exit_code)


if not sys.warnoptions:
    warnings.simplefilter("default")

if __name__ == "__main__":
    main()  # pragma: no cover
