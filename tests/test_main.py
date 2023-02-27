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
    def test_main_execution(self, tmpdir, fixture_dir):
        with (fixture_dir / ".relint.yml").open() as fs:
            config = fs.read()
        tmpdir.join(".relint.yml").write(config)
        tmpdir.join("dummy.py").write("# TODO do something")
        with tmpdir.as_cwd():
            with pytest.raises(SystemExit) as exc_info:
                main(["relint.py", "dummy.py"])

        assert exc_info.value.code == 0

    def test_main_execution_with_error(self, capsys, tmpdir, fixture_dir):
        with (fixture_dir / ".relint.yml").open() as fs:
            config = fs.read()
        tmpdir.join(".relint.yml").write(config)
        tmpdir.join("dummy.py").write("# FIXME do something")
        with tmpdir.as_cwd():
            with pytest.raises(SystemExit) as exc_info:
                main(["relint.py", "dummy.py"])

        expected_message = "dummy.py:1 No fixme (warning)\nHint: Fix it right away!\n1>    # FIXME do something\n"

        out, _ = capsys.readouterr()
        assert expected_message == out
        assert exc_info.value.code == 1

    def test_main_execution_with_custom_template(self, capsys, tmpdir, fixture_dir):
        with (fixture_dir / ".relint.yml").open() as fs:
            config = fs.read()
        tmpdir.join(".relint.yml").write(config)
        tmpdir.join("dummy.py").write("# TODO do something")

        with tmpdir.as_cwd():
            with pytest.raises(SystemExit) as exc_info:
                template = r"😵{filename}:{line_no} | {test.name} \n {match}"
                main(["relint.py", "dummy.py", "--msg-template", template])

        expected_message = "😵dummy.py:1 | No ToDo \n" " 1>    # TODO do something\n"

        out, _ = capsys.readouterr()
        assert expected_message == out
        assert exc_info.value.code == 0

    def test_raise_for_warnings(self, tmpdir, fixture_dir):
        with (fixture_dir / ".relint.yml").open() as fs:
            config = fs.read()
        tmpdir.join(".relint.yml").write(config)
        tmpdir.join("dummy.py").write("# TODO do something")
        with tmpdir.as_cwd():
            with pytest.raises(SystemExit) as exc_info:
                main(["relint.py", "dummy.py", "-W"])

        assert exc_info.value.code == 1

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
