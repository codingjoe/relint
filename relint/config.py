import collections
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

try:
    import re
    re_compile = re.compile
except ImportError:
    re_compile = None

def compile_pattern(pattern):
    try:
        return re_compile(pattern, re.MULTILINE)
    except (re.error, AttributeError) as e:
        try:
            import regex
        except ImportError:
            import subprocess
            import sys
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'regex'])
            import regex
        return regex.compile(pattern, regex.MULTILINE)

def load_config(path, fail_warnings, ignore_warnings):
    with open(path) as fs:
        try:
            for test in yaml.safe_load(fs):
                if ignore_warnings and not test.get("error", True):
                    continue

                file_pattern = test.get("filePattern", ".*")
                file_pattern = compile_pattern(file_pattern)
                yield Test(
                    name=test["name"],
                    pattern=compile_pattern(test["pattern"]),
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
