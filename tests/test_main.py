import io
import sys

import pytest

import relint
from relint.__main__ import main


def test_version(tmpdir, capsys):
    """Test that the version is correct."""
    with tmpdir.as_cwd():
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
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
                main(["dummy.py"])

        assert exc_info.value.code == 0

    def test_main_execution_with_error(self, capsys, tmpdir, fixture_dir):
        with (fixture_dir / ".relint.yml").open() as fs:
            config = fs.read()
        tmpdir.join(".relint.yml").write(config)
        tmpdir.join("dummy.py").write("# FIXME do something")
        with tmpdir.as_cwd():
            with pytest.raises(SystemExit) as exc_info:
                main(["dummy.py"])

        out, _ = capsys.readouterr()
        assert "dummy.py:1" in out
        assert "No fixme (warning)" in out
        assert "Fix it right away!" in out
        assert "❱ 1 # FIXME do something" in out
        assert exc_info.value.code == 1

    def test_main_execution_with_error__github_workflow_output(
        self, monkeypatch, capsys, tmpdir, fixture_dir
    ):
        monkeypatch.setenv("GITHUB_ACTIONS", "true")
        with (fixture_dir / ".relint.yml").open() as fs:
            config = fs.read()
        tmpdir.join(".relint.yml").write(config)
        tmpdir.join("dummy.py").write("# FIXME do something")
        with tmpdir.as_cwd():
            with pytest.raises(SystemExit) as exc_info:
                main(["dummy.py"])

        out, _ = capsys.readouterr()
        assert (
            "::error file=dummy.py,line=1,endLine=1,col=3,colEnd=8,title=No fixme (warning)::### This is a multiline hint%0AFix it right away!%0A%0AYou can use code blocks too, like Python:%0A%0A"
            in out
        )
        assert exc_info.value.code == 1

    @pytest.mark.parametrize("args", [[], ["--summarize"]])
    def test_main_execution_without_hint(self, args, capsys, tmpdir, fixture_dir):
        with (fixture_dir / ".relint.yml").open() as fs:
            config = fs.read()
        tmpdir.join(".relint.yml").write(config)
        tmpdir.join("dummy.py").write("# hint: 🤐")
        with tmpdir.as_cwd():
            with pytest.raises(SystemExit):
                main(["dummy.py", *args])

        out, _ = capsys.readouterr()
        assert "dummy.py:1" in out
        assert "Error: no hint" in out

    def test_raise_for_warnings(self, tmpdir, fixture_dir):
        with (fixture_dir / ".relint.yml").open() as fs:
            config = fs.read()
        tmpdir.join(".relint.yml").write(config)
        tmpdir.join("dummy.py").write("# TODO do something")
        with tmpdir.as_cwd():
            with pytest.raises(SystemExit) as exc_info:
                main(["dummy.py", "-W"])

        assert exc_info.value.code == 1

    def test_ignore_warnings(self, tmpdir, fixture_dir):
        with (fixture_dir / ".relint.yml").open() as fs:
            config = fs.read()
        tmpdir.join(".relint.yml").write(config)
        tmpdir.join("dummy.py").write("# TODO do something")
        with tmpdir.as_cwd():
            with pytest.raises(SystemExit) as exc_info:
                main(["dummy.py", "--ignore-warnings"])

        assert exc_info.value.code == 0

    def test_summarize(self, tmpdir, fixture_dir, capsys):
        with (fixture_dir / ".relint.yml").open() as fs:
            config = fs.read()
        tmpdir.join(".relint.yml").write(config)
        tmpdir.join("dummy.py").write("# FIXME do something")
        with tmpdir.as_cwd():
            with pytest.raises(SystemExit) as exc_info:
                main(["dummy.py", "--summarize"])

        out, _ = capsys.readouterr()
        assert "dummy.py:1" in out
        assert "No fixme (warning)" in out
        assert "Fix it right away!" in out
        assert "1 occurrence(s)" in out
        assert exc_info.value.code == 1

    def test_code_padding_disabled(self, tmpdir, fixture_dir, capsys):
        with (fixture_dir / ".relint.yml").open() as fs:
            config = fs.read()
        tmpdir.join(".relint.yml").write(config)
        tmpdir.join("dummy.py").write("# FIXME do something")
        with tmpdir.as_cwd():
            with pytest.raises(SystemExit) as exc_info:
                main(["dummy.py", "--code-padding=-1"])

        out, _ = capsys.readouterr()
        assert "dummy.py:1" in out
        assert "No fixme (warning)" in out
        assert "Fix it right away!" in out
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
                main(["dummy.py", "--diff"])

        out, _ = capsys.readouterr()
        assert "Get it done right away!" in out
        assert exc_info.value.code == 0
