import io
import sys

import pytest

import relint
from relint.__main__ import main


def test_version(tmpdir, capsys):
    """Test that the version is correct."""
    with tmpdir.as_cwd():
        with pytest.raises(SystemExit) as exc_info:
            main(["relint.py", "--version"])
    assert "0" in str(exc_info.value)
    assert f"relint: {relint.__version__}" in capsys.readouterr().out


class TestMain:
    @pytest.mark.parametrize("filename", ["test_parse.py", "[a-b].py", "[b-a].py"])
    def test_main_execution(self, filename, tmpdir, fixture_dir):
        with (fixture_dir / ".relint.yml").open() as fs:
            config = fs.read()
        tmpdir.join(".relint.yml").write(config)
        with tmpdir.as_cwd():
            with pytest.raises(SystemExit) as exc_info:
                main(["relint.py", filename])

        assert exc_info.value.code == 0

    def test_main_execution_with_custom_template(self, capsys, tmpdir, fixture_dir):
        with (fixture_dir / ".relint.yml").open() as fs:
            config = fs.read()
        tmpdir.join(".relint.yml").write(config)
        tmpdir.join("dummy.py").write("# TODO do something")

        with tmpdir.as_cwd():
            with pytest.raises(SystemExit) as exc_info:
                template = "😵{filename}:{line_no} | {test.name} \n {match}"
                main(["relint.py", "dummy.py", "--msg-template", template])

        expected_message = "😵dummy.py:1 | No ToDo \n" " 1>    # TODO do something\n"

        out, _ = capsys.readouterr()
        assert expected_message == out
        assert exc_info.value.code == 0

    @pytest.mark.parametrize("filename", ["test_parse.py", "[a-b].py", "[b-a].py"])
    def test_raise_for_warnings(self, filename, tmpdir, fixture_dir):
        with (fixture_dir / ".relint.yml").open() as fs:
            config = fs.read()
        tmpdir.join(".relint.yml").write(config)
        with tmpdir.as_cwd():
            with pytest.raises(SystemExit) as exc_info:
                main(["relint.py", "-W", filename])

        assert exc_info.value.code != 0

    def test_main_execution_with_diff(self, capsys, mocker, tmpdir, fixture_dir):
        with (fixture_dir / ".relint.yml").open() as fs:
            config = fs.read()
        tmpdir.join(".relint.yml").write(config)
        tmpdir.join("dummy.py").write("# TODO do something")
        diff = io.StringIO(
            "diff --git a/dummy.py b/dummy.py\n"
            "@@ -0,0 +1 @@\n"
            "+# TODO do something"
        )

        mocker.patch.object(sys, "stdin", diff)

        with tmpdir.as_cwd():
            with pytest.raises(SystemExit) as exc_info:
                main(["relint.py", "dummy.py", "--diff"])

        expected_message = "Hint: Get it done right away!"

        out, _ = capsys.readouterr()
        assert expected_message in out
        assert exc_info.value.code == 0
