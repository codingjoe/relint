import collections
import warnings

try:
    import regex as re
except ImportError:
    import re

import yaml

from .exceptions import ConfigError

Test = collections.namedtuple(
    "Test",
    (
        "name",
        "pattern",
        "hint",
        "file_pattern",
        "error",
    ),
)


def load_config(path, fail_warnings, ignore_warnings):
    with open(path) as fs:
        try:
            for test in yaml.safe_load(fs):
                if ignore_warnings and not test.get("error", True):
                    continue

                file_pattern = test.get("filePattern", ".*")
                file_pattern = re.compile(file_pattern)
                yield Test(
                    name=test["name"],
                    pattern=re.compile(test["pattern"]),
                    hint=test.get("hint"),
                    file_pattern=file_pattern,
                    error=test.get("error", True) or fail_warnings,
                )
        except yaml.YAMLError as e:
            raise ConfigError("Error parsing your relint config file.") from e
        except TypeError:
            warnings.warn(
                "Your relint config is empty, no tests were executed.", UserWarning
            )
        except (AttributeError, ValueError) as e:
            raise ConfigError(
                "Your relint config is not a valid YAML list of relint tests."
            ) from e
