---
description: Run reLint to lint files using regular expression rules. Use when the user wants to run relint, check files against relint rules, lint a diff, or configure relint in pre-commit/CI.
---

# Run reLint

reLint is a regular expression linter. It checks files against user-defined rules written in a YAML config file (default `.relint.yml`).

## Prerequisites

reLint can be run directly with `uvx` — no install required:

```shell
uvx relint --version
# or, for advanced regex features (e.g. lookbehinds on variable-width patterns):
uvx --with "relint[regex]" relint
```

All CLI examples below can be run via `uvx relint ...` (e.g. `uvx relint -c .relint.yml FILE`).

## CLI usage

The config file defaults to `.relint.yml` in the working directory. Override it with `-c`/`--config`.

```shell
# Lint specific files using the default config (.relint.yml)
relint FILE FILE2 ...

# Lint with a custom config file
relint -c path/to/.relint.yml FILE FILE2 ...

# Lint only the changed lines piped from a git diff
git diff --unified=0 | relint my_file.py --diff

# Lint the currently staged git diff directly
relint --git-diff

# Fail (non-zero exit) on warnings too
relint -W FILE ...

# Suppress warnings (useful in CI)
relint --ignore-warnings FILE ...

# Group matches by rule instead of listing each occurrence
relint --summarize FILE ...

# Control code snippet padding (default 2; set -1 to hide snippets)
relint --code-padding 4 FILE ...
```

## How to run

1. Determine the scope of files the user wants to lint. If none are given, ask which files or globs to lint. Do NOT lint the entire repo by default — relint takes explicit file paths, not globs.
1. Locate the relint config. Default to `.relint.yml` in the working directory; use `-c` if the user specifies a different file. If no config exists, tell the user and offer to create one (see the `write-rule` skill).
1. Run relint via the Bash tool, passing the config and target files.
1. Report the results clearly: list each match with its rule name, file, line number, and hint. If relint exits non-zero, point out which rules errored vs. warned.
1. If running in a CI/GitHub Actions context, note that relint emits `::error`/`::warning` annotations automatically when `GITHUB_ACTIONS=true`.

## pre-commit integration

If the user wants to automate linting, add this to `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/codingjoe/relint
  rev: 1.4.0
  hooks:
    - id: relint
      args: [-W]  # optional: fail on warnings during commit
```

## Tips

- reLint reads the entire file, so patterns can span multiple lines and include newlines.
- The `error` attribute (default `true`) controls whether a rule produces a warning (`false`) or a hard error.
- The `filePattern` attribute (default `.*`) narrows which files a rule applies to. It is matched against the full file path.
