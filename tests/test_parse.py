import subprocess
import warnings

import pytest

from relint.__main__ import main
from relint.config import Test
from relint.exceptions import ConfigError
from relint.parse import (
    lint_file,
    match_with_diff_changes,
    parse_diff,
    parse_filenames,
    parse_line_numbers,
    split_diff_content_by_filename,
)


class TestParseGitDiff:
    def test_line_numbers(self):
        output = "@@ -4,2 +4,2 @@ import glob"

        assert parse_line_numbers(output) == [4, 5]

    def test_line_numbers_when_only_one_line_was_changed(self):
        output = "@@ -54 +54 @@ import glob"

        assert parse_line_numbers(output) == [54]

    @pytest.mark.parametrize(
        "output,expected_filename",
        [
            ("diff --git a/relint.py b/relint.py", "relint.py"),
            (
                "diff --git a/pardal/authserver/app.py b/pardal/authserver/app.py",
                "pardal/authserver/app.py",
            ),
        ],
    )
    def test_parse_filenames(self, output, expected_filename):
        assert parse_filenames(output) == [expected_filename]

    def test_split_diff_content(self, fixture_dir):
        with (fixture_dir / "test.diff").open() as fs:
            output = fs.read()
        split = split_diff_content_by_filename(output)

        assert isinstance(split, dict)
        assert len(split) == 3

    def test_return_empty_list_if_can_not_split_diff_content(self):
        split = split_diff_content_by_filename("")
        assert split == {}

    def test_return_empty_dict_when_diff_returns_empty(self):
        parsed_content = parse_diff("")

        assert parsed_content == {}

    def test_match_with_diff_changes(self):
        content = {"test_parse.py": [2], "setup.py": [6]}
        matches = (
            ("test_parse.py", None, None, 2),
            ("test_relint2.py", None, None, 1),
            ("test_relint3.py", None, None, 1),
        )

        paths_from_diff = match_with_diff_changes(content, matches)
        filename, _, _, line_number = next(paths_from_diff)

        assert filename == "test_parse.py"
        assert line_number == 2

        with pytest.raises(StopIteration):
            filename, _, _, line_number = next(paths_from_diff)

    def test_parse_one_line_changed_one_file(self):
        output = (
            "diff --git a/test_parse.py b/test_parse.py\n"
            "@@ -73 +92 @@ def main():\n"
            "-        lint_file(path, tests)\n"
            "+        lint_file(path, tests, diff)\n"
        )

        parsed_content = parse_diff(output)
        expected = {"test_parse.py": [92]}

        assert parsed_content == expected

    def test_parse_multiple_line_changed_one_file(self):
        output = (
            "diff --git a/test_parse.py b/test_parse.py\n"
            "@@ -27,0 +28,6 @@ def parse_args():\n"
            "+    parser.add_argument(\n"
            "+        '--diff',\n"
            "+        '-d',\n"
            "+        action='store_true',\n"
            "+        help='Analyze content from git diff.'\n"
            "+    )\n"
        )

        parsed_content = parse_diff(output)
        expected = {"test_parse.py": [28, 29, 30, 31, 32, 33]}

        assert parsed_content == expected

    def test_parse_complete_diff(self):
        output = (
            "diff --git a/test_parse.py b/test_parse.py\n"
            "index 9c7f392..9bde2ad 100644\n"
            "--- a/test_parse.py\n"
            "+++ b/test_parse.py\n"
            "@@ -1,0 +2 @@\n"
            "+# TODO: I'll do it later, promise\n"
        )

        parsed_content = parse_diff(output)
        expected = {"test_parse.py": [2]}

        assert parsed_content == expected

    def test_empty_config_file(self, tmpdir):
        tmpdir.join(".relint.yml").write("")
        tmpdir.join("dummy.py").write("")

        with tmpdir.as_cwd():
            with warnings.catch_warnings(record=True) as w:
                with pytest.raises(SystemExit) as exc_info:
                    main(["dummy.py"])

        assert exc_info.value.code == 0
        assert issubclass(w[-1].category, UserWarning)
        assert "Your relint config is empty, no tests were executed." in str(
            w[-1].message
        )

    def test_malformed_config_file(self, tmpdir):
        tmpdir.join(".relint.yml").write("test:")

        with tmpdir.as_cwd():
            with pytest.raises(ConfigError) as exc_info:
                main(["**"])

        assert "Your relint config is not a valid YAML list of relint tests." in str(
            exc_info.value
        )

    def test_corrupt_config_file(self, tmpdir):
        tmpdir.join(".relint.yml").write(b"\x00")

        with tmpdir.as_cwd():
            with pytest.raises(ConfigError) as exc_info:
                main(["**"])

        assert "Error parsing your relint config file." in str(exc_info.value)

    def test_git_diff(self, capsys, tmpdir, fixture_dir):
        with (fixture_dir / ".relint.yml").open() as fs:
            config = fs.read()
        tmpdir.join(".relint.yml").write(config)
        tmpdir.join("dummy.py").write("# TODO do something")
        subprocess.check_call(["git", "init"], cwd=tmpdir.strpath)  # nosec

        with tmpdir.as_cwd():
            with pytest.raises(SystemExit) as exc_info:
                main(["dummy.py", "--git-diff"])

        assert "0" in str(exc_info.value)


def test_no_unicode(capsys, tmpdir, fixture_dir):
    with (fixture_dir / ".relint.yml").open() as fs:
        config = fs.read()
    tmpdir.join(".relint.yml").write(config)
    with (fixture_dir / "test.png").open("rb") as fs:
        png = fs.read()
    tmpdir.join("test.png").write(png, mode="wb")
    with tmpdir.as_cwd():
        with pytest.raises(SystemExit) as exc_info:
            main(["test.png"])
    assert "0" in str(exc_info.value)


def test_cc_linting_rule(tmpdir, fixture_dir):
    regex = pytest.importorskip("regex")
    cc_file = tmpdir.join("example.cpp")
    cc_file.write(
        "#include <iostream>\n"
        "/* This is an extremely long COMMENT that has over one hundred and twenty characters to test whether this is recognized by the regex or not. */\n"
        "int main() {\n"
        '    std::cout << "This is an extremely long CODE that has over one hundred and twenty characters to test whether this is recognized by the regex or not."\n'
        "    return 0;\n"
        "}\n"
    )

    with (fixture_dir / ".relint.yml").open() as fs:
        config = fs.read()
    tmpdir.join(".relint.yml").write(config)

    # Load the configuration as Test named tuples

    with tmpdir.as_cwd():
        assert list(
            lint_file(
                str(cc_file),
                [
                    Test(
                        name="No line longer than 120 characters",
                        pattern=regex.compile(
                            r".{120,}(?<!\s)(?=\s|$)|.{120,}(?<=\s)(?=\s)"
                        ),
                        hint="There should be no line longer than 120 characters in a line.",
                        file_pattern=regex.compile(r".*\.(cpp|h)"),
                        error=True,
                    )
                ],
            )
        )
