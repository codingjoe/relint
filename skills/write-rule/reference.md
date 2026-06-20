# reLint Rule Reference

A reLint config is a YAML file (default `.relint.yml`) containing a **list of rules**.
Each rule is a mapping with the following keys:

| Key           | Required | Default | Description                                                                                     |
| ------------- | -------- | ------- | ----------------------------------------------------------------------------------------------- |
| `name`        | yes      | —       | The rule name. Shown in output as the lint message title.                                       |
| `pattern`     | yes      | —       | A regular expression matched against the entire file content. Can span multiple lines/newlines. |
| `hint`        | no       | `null`  | A human-readable message shown when the rule matches. Supports Markdown.                        |
| `filePattern` | no       | `.*`    | A regex matched against the **full file path** to narrow which files a rule applies to.         |
| `error`       | no       | `true`  | If `true`, a match is a hard error (non-zero exit). If `false`, it is only a warning.           |

## Pattern behavior

- The pattern is compiled with Python's `re` module by default. Run with the `regex` extra (`uvx --with "relint[regex]" relint`) to get access to advanced features such as variable-width lookbehinds and Unicode properties.
- `reLint` lints **entire files** at once, so your pattern can match across multiple lines. Include `\n` in your pattern to match newlines, or use `(?s)`/`[\s\S]` to span lines.
- Inline flags such as `(?i)` (case-insensitive) are supported in the pattern itself.

## filePattern notes

- Matched against the full file path (e.g. `src/app/views.py`), not just the basename.
- Defaults to `.*` (every file). Commonly narrowed to extensions, e.g. `.*\.py`, or paths, e.g. `.*\/management\/commands\/.*\.py`.
- It is a regex, so escape dots: `.*\.py` matches `.py` files; `.*.py` would also match `xypy`.

## YAML gotchas

- Quote patterns that contain characters with special YAML meaning (`:`, `{`, `}`, `[`, `]`, `,`, `&`, `*`, `#`, `?`, `|`, `-`, `<`, `>`, `=`, `!`, `%`, `@`, `` ` ``) or that start with a character that could be misread.
- Multi-line `hint:` values use the YAML literal block scalar (`|`) to preserve newlines.
- Avoid trailing whitespace in patterns unless it is intentional; YAML may strip it.

## Example rule

```yaml
- name: No ToDo
  pattern: '(?i)todo'
  hint: Get it done right away!
  filePattern: .*\.(py|js)
  error: false
```

## Verification workflow

After writing a rule, always validate it:

1. Ensure the config is valid YAML and parses as a list (reLint expects a top-level list of rules).
1. Run relint against a sample file that is known to match, and one that is known to be clean, to confirm the rule behaves as intended.
1. Check the exit code: errors cause a non-zero exit, warnings do not (unless `-W`/`--fail-warnings` is passed).
