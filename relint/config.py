import collections
import re
import warnings

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


def load_config(path, fail_warnings):
    with open(path) as fs:
        try:
            for test in yaml.safe_load(fs):
                file_pattern = test.get("filePattern", ".*")
                file_pattern = re.compile(file_pattern)
                yield Test(
                    name=test["name"],
                    pattern=re.compile(test["pattern"], re.MULTILINE),
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
