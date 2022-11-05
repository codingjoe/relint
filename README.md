![/(re)lint/](https://repository-images.githubusercontent.com/127479533/061e8bfe-f0e0-4f0b-857b-eae82f9df6af)

# reLint

**Regular Expression Linter**

*Write your own linting rules using regular expressions.*

[![PyPi Version](https://img.shields.io/pypi/v/relint.svg)](https://pypi.python.org/pypi/relint/)
[![Test Coverage](https://codecov.io/gh/codingjoe/relint/branch/main/graph/badge.svg)](https://codecov.io/gh/codingjoe/relint)
[![GitHub License](https://img.shields.io/github/license/codingjoe/relint)](https://raw.githubusercontent.com/codingjoe/relint/main/LICENSE)

## Installation

```shell-session
python3 -m pip install relint
```

## [Examples & Recipes – The reLint Cookbook](https://github.com/codingjoe/relint/blob/main/COOKBOOK.md)

## Usage

You can write your own regular rules in a YAML file, like so:

```yaml
- name: No ToDo
  pattern: '(?i)todo' # case insensitive flag
  hint: Get it done right away!
  filePattern: .*\.(py|js)
  error: false
```

The `name` attribute is the name of your linter, the `pattern` can be
any regular expression. The linter does lint entire files, therefore
your expressions can match multiple lines and include newlines.

You can narrow down the file types your linter should be working with,
by providing the optional `filePattern` attribute. The default is `.*`.

The optional `error` attribute allows you to only show a warning but not
exit with a bad (non-zero) exit code. The default is `true`.

The following command will lint all files in the current directory:

```shell
relint -c .relint.yml **
```

The default configuration file name is `.relint.yml` within your working
directory, but you can provide any YAML or JSON file.

If you prefer linting changed files (cached on git) you can use the
option `--diff [-d]` or `--git-diff [-g]`:

```shell
git diff --unified=0 | relint my_file.py --diff
```

### Custom message format

Customize the output message format with the `--msg-template=<format string>` option.
[Python format syntax](https://docs.python.org/3/library/string.html#formatstrings)
is suported for the message template and the following fields are available:

* `filename`
  The name of the file being linted.

* `line_no`
  The line number of the match.

* `match`
  The matched text.

* `test.*`
  Any attribute of the test rule, e.g. `test.name` or `test.hint`.


### pre-commit

You can automate the linting process by adding a
[pre-commit](https://pre-commit.com/) hook to your project. Add the
following entry to your `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/codingjoe/relint
  rev: 1.4.0
  hooks:
    - id: relint
      args: [-W]  # optional, if you want to fail on warnings during commit
```
