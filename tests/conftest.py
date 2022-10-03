import pathlib

import pytest

FIXTURE_DIR = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def fixture_dir():
    """Return the path to the fixture directory."""
    return FIXTURE_DIR
