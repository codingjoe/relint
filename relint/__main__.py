import argparse
import os
import subprocess  # nosec
import sys
import warnings

from rich.progress import track

from relint.config import load_config
from relint.parse import (
    lint_file,
    match_with_diff_changes,
    parse_diff,
    print_culprits,
    print_github_actions_output,
)


def parse_args(args=None):
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
        "--ignore-warnings",
        action="store_true",
        help="Do not output warnings. Could be useful when using relint in CI.",
    )
    parser.add_argument(
        "--summarize",
        action="store_true",
        help="Summarize the output by grouping matches by test.",
    ),
    parser.add_argument(
        "--code-padding",
        type=int,
        default=2,
        help=(
            "Lines of padding to show around the matching code snippet. Default: 2\n"
            "Set to -1 disable code snippet output."
        ),
    )
    return parser.parse_args(args=args)


def main(args=None):
    args = parse_args(args=args)
    if args.version:
        from . import __version__

        print(f"relint: {__version__}")
        exit(0)

    tests = list(load_config(args.config, args.fail_warnings, args.ignore_warnings))

    matches = []
    for path in track(args.files, description="Linting files..."):
        matches.extend(lint_file(path, tests))

    output = ""
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

    GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"
    if GITHUB_ACTIONS:
        exit_code = print_github_actions_output(matches, args)
    else:
        exit_code = print_culprits(matches, args)
    exit(exit_code)


if not sys.warnoptions:
    warnings.simplefilter("default")

if __name__ == "__main__":
    main()  # pragma: no cover
