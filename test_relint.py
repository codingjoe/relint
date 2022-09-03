import io
import os
import subprocess
import sys
import warnings

import pytest
import yaml

from relint import (main, match_with_diff_changes, parse_diff, parse_filenames,
                    parse_line_numbers, split_diff_content_by_filename, ConfigError, )


class TestMain:
    @pytest.mark.parametrize('filename', ['test_relint.py', '[a-b].py', '[b-a].py'])
    def test_main_execution(self, mocker, filename):
        with pytest.raises(SystemExit) as exc_info:
            main(['relint.py', filename])

        assert exc_info.value.code == 0

    @pytest.mark.parametrize('filename', ['test_relint.py', '[a-b].py', '[b-a].py'])
    def test_main_execution(self, mocker, filename):
        with pytest.raises(SystemExit) as exc_info:
            main(['relint.py', '-W', filename])

        assert exc_info.value.code != 0

    def test_main_execution_with_diff(self, capsys, mocker, tmpdir):
        tmpdir.join('.relint.yml').write(open('.relint.yml').read())
        tmpdir.join('dummy.py').write("# TODO do something")
        diff = io.StringIO(
            "diff --git a/dummy.py b/dummy.py\n"
            "@@ -0,0 +1 @@\n"
            "+# TODO do something"
        )

        mocker.patch.object(sys, 'stdin', diff)

        with tmpdir.as_cwd():
            with pytest.raises(SystemExit) as exc_info:
                main(['relint.py', 'dummy.py', '--diff'])

        expected_message = 'Hint: Get it done right away!'

        out, _ = capsys.readouterr()
        assert expected_message in out
        assert exc_info.value.code == 0


class TestParseGitDiff:
    def test_line_numbers(self):
        output = '@@ -4,2 +4,2 @@ import glob'

        assert parse_line_numbers(output) == [4, 5]

    def test_line_numbers_when_only_one_line_was_changed(self):
        output = '@@ -54 +54 @@ import glob'

        assert parse_line_numbers(output) == [54]

    @pytest.mark.parametrize('output,expected_filename', [
        (
            'diff --git a/relint.py b/relint.py',
            'relint.py'
        ),
        (
            'diff --git a/pardal/authserver/app.py b/pardal/authserver/app.py',
            'pardal/authserver/app.py'
        ),
    ])
    def test_parse_filenames(self, output, expected_filename):
        assert parse_filenames(output) == [expected_filename]

    def test_split_diff_content(self):
        output = open('test.diff').read()
        splited = split_diff_content_by_filename(output)

        assert isinstance(splited, dict)
        assert len(splited) == 3

    def test_return_empty_list_if_can_not_split_diff_content(self):
        splited = split_diff_content_by_filename('')
        assert splited == {}

    def test_return_empty_dict_when_diff_returns_empty(self):
        parsed_content = parse_diff('')

        assert parsed_content == {}

    def test_match_with_diff_changes(self):
        content = {
            'test_relint.py': [2],
            'setup.py': [6]
        }
        matches = (
            ('test_relint.py', None, None, 2),
            ('test_relint2.py', None, None, 1),
            ('test_relint3.py', None, None, 1)
        )

        paths_from_diff = match_with_diff_changes(content, matches)
        filename, _, _, line_number = next(paths_from_diff)

        assert filename == 'test_relint.py'
        assert line_number == 2

        with pytest.raises(StopIteration):
            filename, _, _, line_number = next(paths_from_diff)

    def test_parse_one_line_changed_one_file(self):
        output = (
            "diff --git a/test_relint.py b/test_relint.py\n"
            "@@ -73 +92 @@ def main():\n"
            "-        lint_file(path, tests)\n"
            "+        lint_file(path, tests, diff)\n"
        )

        parsed_content = parse_diff(output)
        expected = {'test_relint.py': [92]}

        assert parsed_content == expected

    def test_parse_multiple_line_changed_one_file(self):
        output = (
            "diff --git a/test_relint.py b/test_relint.py\n"
            "@@ -27,0 +28,6 @@ def parse_args():\n"
            "+    parser.add_argument(\n"
            "+        '--diff',\n"
            "+        '-d',\n"
            "+        action='store_true',\n"
            "+        help='Analyze content from git diff.'\n"
            "+    )\n"
        )

        parsed_content = parse_diff(output)
        expected = {'test_relint.py': [28, 29, 30, 31, 32, 33]}

        assert parsed_content == expected

    def test_parse_complete_diff(self):
        output = (
            "diff --git a/test_relint.py b/test_relint.py\n"
            "index 9c7f392..9bde2ad 100644\n"
            "--- a/test_relint.py\n"
            "+++ b/test_relint.py\n"
            "@@ -1,0 +2 @@\n"
            "+# TODO: I'll do it later, promise\n"
        )

        parsed_content = parse_diff(output)
        expected = {'test_relint.py': [2]}

        assert parsed_content == expected

    def test_filename_warning(self, tmpdir):
        tmpdir.join('.relint.yml').write(
            '- name: old\n'
            '  pattern: ".*"\n'
            '  filename: "*.py"\n'
        )

        with tmpdir.as_cwd():
            with warnings.catch_warnings(record=True) as w:
                with pytest.raises(SystemExit) as exc_info:
                    main(['**'])

        assert exc_info.value.code == 0
        assert issubclass(w[-1].category, DeprecationWarning)
        assert "'filename'" in str(w[-1].message)

    def test_empty_config_file(self, tmpdir):
        tmpdir.join('.relint.yml').write('')

        with tmpdir.as_cwd():
            with warnings.catch_warnings(record=True) as w:
                with pytest.raises(SystemExit) as exc_info:
                    main(['**'])

        assert exc_info.value.code == 0
        assert issubclass(w[-1].category, UserWarning)
        assert "Your relint config is empty, no tests were executed." in str(w[-1].message)

    def test_malformed_config_file(self, tmpdir):
        tmpdir.join('.relint.yml').write('test:')

        with tmpdir.as_cwd():
            with pytest.raises(ConfigError) as exc_info:
                main(['**'])

        assert "Your relint config is not a valid YAML list of relint tests." in str(exc_info.value)

    def test_corrupt_config_file(self, tmpdir):
        tmpdir.join('.relint.yml').write(b'\x00')

        with tmpdir.as_cwd():
            with pytest.raises(ConfigError) as exc_info:
                main(['**'])

        assert 'Error parsing your relint config file.' in str(exc_info.value)

    def test_git_diff(self, capsys, tmpdir):
        tmpdir.join('.relint.yml').write(open('.relint.yml').read())
        tmpdir.join('dummy.py').write("# TODO do something")
        subprocess.check_call(['git', 'init'], cwd=tmpdir.strpath)  # nosec

        with tmpdir.as_cwd():
            with pytest.raises(SystemExit) as exc_info:
                main(['relint.py', 'dummy.py', '--git-diff'])

        assert '0' in str(exc_info.value)
