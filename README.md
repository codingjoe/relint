![/(re)lint/](https://repository-images.githubusercontent.com/127479533/158678f4-7840-425a-9f31-12f4b0fd56ba)

# reLint

**Regular Expression Linter**

*Write your own linting rules using regular expressions.*

[![PyPi Version](https://img.shields.io/pypi/v/relint.svg)](https://pypi.python.org/pypi/relint/)
[![Test Coverage](https://codecov.io/gh/codingjoe/relint/branch/main/graph/badge.svg)](https://codecov.io/gh/codingjoe/relint)
[![GitHub License](https://img.shields.io/github/license/codingjoe/relint)](https://raw.githubusercontent.com/codingjoe/relint/master/LICENSE)

## Installation

```shell-session
python3 -m pip install relint
```

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

```shell-session
relint -c .relint.yml **
```

The default configuration file name is `.relint.yml` within your working
directory, but you can provide any YAML or JSON file.

If you prefer linting changed files (cached on git) you can use the
option `--diff [-d]` or `--git-diff [-g]`:

```shell
git diff --unified=0 | relint my_file.py --diff
```

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

## Samples

```yaml
- name: db fixtures
  pattern: 'def test_[^(]+\([^)]*(customer|product)(, |\))'
  hint: Use model_bakery recipes instead of db fixtures.
  filePattern: test_.*\.py

- name: model_bakery recipes
  pattern: baker\.make\(
  hint: Please use baker.make_recipe instead of baker.make.
  filePattern: (test_.*|conftest)\.py

- name: the database is lava
  pattern: '@pytest.fixture.*\n[ ]*def [^(]+\([^)]*(db|transactional_db)(, |\))'
  hint: Please do not create db fixtures but model_bakery recipes instead.
  filePattern: .*\.py

- name: No logger in management commands
  pattern: (logger|import logging)
  hint: Please write to self.stdout or self.stderr in favor of using a logger.
  filePattern: \/management\/commands\/.*\.py
```
