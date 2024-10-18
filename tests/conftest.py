import pathlib

import pytest

FIXTURE_DIR = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def fixture_dir():
    """Return the path to the fixture directory."""
    return FIXTURE_DIR


@pytest.fixture(autouse=True)
def env(monkeypatch):
    """Remove GITHUB_ACTIONS the environment as it is part of our feature set."""
    monkeypatch.setenv("GITHUB_ACTIONS", "false")
