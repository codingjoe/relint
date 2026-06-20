---
description: Author and edit reLint rules in a .relint.yml config. Use when the user wants to create a new linting rule, write a regex-based linter, modify existing relint rules, or add rules from the Cookbook.
allowed-tools: Bash(uvx relint *) Bash(relint *) Read
---

# Write reLint Rules

You help the user write and maintain reLint rules. reLint rules are regular-expression-based linters defined in a YAML config file (default `.relint.yml`).

For the full rule schema, pattern behavior, and YAML gotchas, read `reference.md` in this skill directory.

## Rule schema (quick reference)

Each config is a YAML **list of rules**. Each rule supports:

| Key           | Required | Default | Purpose                                      |
| ------------- | -------- | ------- | -------------------------------------------- |
| `name`        | yes      | —       | Rule name shown in output.                   |
| `pattern`     | yes      | —       | Regex matched against entire file content.   |
| `hint`        | no       | `null`  | Message shown on match. Supports Markdown.   |
| `filePattern` | no       | `.*`    | Regex matched against the full file path.    |
| `error`       | no       | `true`  | `true` = hard error; `false` = warning only. |

## Workflow

1. **Understand the goal.** Ask what the user wants to lint and in which files. Determine the target file type(s) and whether it should be an error or warning.
1. **Find the config.** Default to `.relint.yml` in the project root. If it doesn't exist, create it (initialize as a list). If the user names another file, use `-c` when validating.
1. **Author the rule.** Write a `pattern` that matches the undesirable code. Be specific to avoid false positives. Add a clear `hint` explaining the fix, and a `filePattern` to scope it.
1. **Quote carefully.** Wrap `pattern` and `filePattern` in single quotes when they contain YAML-significant characters. Use the literal block scalar `|` for multi-line `hint`s.
1. **Validate.** After writing, run relint on a file known to match and a file known to be clean, and confirm the exit code/behavior is as expected. Always verify before finishing.
1. **Confirm.** Show the user the final rule and the validation results.

## Writing good patterns

- **Be specific.** Prefer anchored or contextual patterns over loose keyword matches, to reduce false positives.
- **Match across lines.** reLint lints entire files, so you can use `\n` or `[\s\S]` to match multiline constructs.
- **Use inline flags.** `(?i)` for case-insensitive; place at the start of the pattern.
- **Escape dots in filePattern.** `.*\.py` for Python files; `.*.py` would also match `xypy`.
- **Scope with filePattern.** Use path segments, e.g. `.*\/management\/commands\/.*\.py`.
- **Advanced regex.** If the pattern needs variable-width lookbehinds or Unicode properties, tell the user to run `uvx --with "relint[regex]" relint`.

## Template

```yaml
- name: <short, descriptive rule name> # by @<author>
  pattern: '<regular expression>'
  hint: |
    <Markdown explanation of the issue and how to fix it>
  filePattern: .*\.<ext>
  error: true  # set false for a warning
```

## Cookbook examples

Real-world rules to inspire and adapt. The full collection lives in `COOKBOOK.md` at the repo root.

### Python

```yaml
- name: Do not import datetime or date directly # by @codingjoe
  pattern: '(from datetime import|from django.utils.timezone import)'
  filePattern: .*\.py
  hint: |
    To differentiate between naive and timezone-aware dates,
    please use the following imports:
     * 'from django.utils import timezone'
     * 'import datetime'
```

### Django management commands

```yaml
- name: No logger in management commands # by @codingjoe
  pattern: (logger|import logging)
  hint: Please write to self.stdout or self.stderr in favor of using a logger.
  filePattern: \/management\/commands\/.*\.py
```

### Testing (pytest-django)

```yaml
- name: IO is lava – Avoid the 'db' fixture # by @codingjoe
  pattern: "def test_[^(]+\\([^)]*db[^)]*\\):"
  hint: Please use the "django_db" marker instead.
  filePattern: .*\.py
```

### HTML

```yaml
- name: no inline CSS # by @codingjoe
  pattern: 'style=\"[^\"]*;[^\"]+\"'
  hint: |
    Please do not use more than one inline style attribute.
    You may use a CSS class instead.
  filePattern: .*\.(html|vue|jsx|tsx)
```

### C/C++

```yaml
# This rule requires the `regex` extra — run via `uvx --with "relint[regex]" relint`.
- name: no line longer than 120 characters in a line (excluding comments) # by @yangcht
  pattern: '(?<!^[ \u00A0\u1680\u2000-\u200A\u202F\u205F\u3000]*//.*)(?<!/\*(?:(?!\*/)[\s\S\r])*?)\b(.{120,})\b'
  hint: |
    Please do not use more than 120 characters in codes except for comments.
  filePattern: .*\.(C|cc|cxx|cpp|c++|cppm)
```

## Common mistakes to avoid

- Forgetting that `filePattern` is matched against the **full path**, not the basename.
- Using unquoted patterns that break YAML parsing (e.g. patterns starting with `!` or containing `: `).
- Writing overly broad patterns that lint clean code as violations.
- Not validating the rule against real files after writing it.
