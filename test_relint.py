# TODO: I'll do it later, promise
import argparse
from unittest.mock import patch

import pytest

from relint import parse_diff, main


class TestParseGitDiff:
    def test_parse_filename(self):
        output = "diff --git a/relint.py b/relint.py\n" \
                 "index a022799..695d0da 100644\n" \
                 "--- a/relint.py\n" \
                 "+++ b/relint.py\n" \
                 "@@ -27,0 +28,6 @@ def parse_args():\n" \
                 "+    parser.add_argument("
        parsed_content = parse_diff(output)

        assert parsed_content['relint.py'] is not None

    def test_parse_one_line_changed_one_file(self):
        output = '@@ -73 +92 @@ def main():\n' \
               '-        lint_file(path, tests)\n' \
               '+        lint_file(path, tests, diff)\n'

        parsed_content = parse_diff(output)
        expected = {
            None: {
                92: '        lint_file(path, tests, diff)'
            }
        }

        assert parsed_content == expected

    def test_parse_multiple_line_changed_one_file(self):
        output = "@@ -27,0 +28,6 @@ def parse_args():\n" \
                 "+    parser.add_argument(\n" \
                 "+        '--diff',\n" \
                 "+        '-d',\n" \
                 "+        action='store_true',\n" \
                 "+        help='Analyze content from git diff.'\n" \
                 "+    )\n"

        parsed_content = parse_diff(output)
        expected = {
            None: {
                28: "    parser.add_argument(",
                29: "        '--diff',",
                30: "        '-d',",
                31: "        action='store_true',",
                32: "        help='Analyze content from git diff.'",
                33: "    )"
            }
        }

        assert parsed_content == expected

    def test_return_empty_dict_when_diff_returns_empty(self):
        parsed_content = parse_diff('')

        assert parsed_content == {}


class TestMain:
    @patch('argparse.ArgumentParser.parse_args',
           return_value=argparse.Namespace(
               files='test_relint.py',
               config='.relint.yml',
               diff=None
           ))
    def test_main_execution(self, parse_args_mock):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0

    @patch('argparse.ArgumentParser.parse_args',
           return_value=argparse.Namespace(
               files='test_relint.py',
               config='.relint.yml',
               diff=True
           ))
    def test_main_execution_with_diff(self, parse_args_mock):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
