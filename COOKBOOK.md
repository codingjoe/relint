# reLint Cookbook

A collection of recipes for reLint. Please feel free to contribute!

# Table of Contents

- [Python](#python)
  - [Django](#django)
- [HTML](#html)
- [C/C++](#cc)

# Python

## Django

### Databases

```yaml
- name: potential database connection limit with use of threading # by @syphar
  pattern: "(threading|ThreadPoolExecutor)[^#]*(?!\\s+# noqa)$"
  hint: |
    When using threads, keep in mind that they might use additional database
    connections. This can lead to a connection limit being reached. You may
    also need to manually close the database connection in the thread.
  filePattern: .*\.py
```

### Utils

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

### Management Commands

```yaml
- name: No logger in management commands # by @codingjoe
  pattern: (logger|import logging)
  hint: Please write to self.stdout or self.stderr in favor of using a logger.
  filePattern: \/management\/commands\/.*\.py
```

### Testing

#### PyTest-Django

```yaml
- name: Code and tests seem too complex # by @codingjoe
  pattern: '(pytest\.fixture|def (?!test_)).*(?!\\s+# noqa)$'
  hint: |
    Large test setups hint towards complex or convoluted production code.
    Consider breaking down your code into smaller individually testable chunks.
    You may also use pytest fixtures inside a conftest.py file. Their usage should
    be limited to technical setups, like stubs or IO mocks. Data fixtures should
    be implemented via baker recipes only.
  filePattern: '.*\/test_.*\.py'
```

```yaml
- name: IO is lava – Avoid using database fixtures # by @codingjoe
  pattern: '@pytest.fixture.*\n[ ]*def [^(]+\([^)]*(db|transactional_db)(, |\))'
  hint: Please use the "django_db" marker on individual tests only.
  filePattern: .*\.py
```

```yaml
- name: IO is lava – Avoid the 'db' fixture # by @codingjoe
  pattern: "def test_[^(]+\\([^)]*db[^)]*\\):"
  hint: Please use the "django_db" marker instead.
  filePattern: .*\.py
```

```yaml
- name: IO is lava – Do not mark a whole test class for database usage # by @codingjoe
  pattern: \@pytest\.mark\.django_db[^\n]*\n\w*class
  hint: Please use the "django_db" marker on individual tests only.
  filePattern: .*\.py
```

#### Model Bakery

```yaml
- name: Follow the recipe # by @codingjoe
  pattern: 'baker\.(make|prepare)\('
  filePattern: '.*\/test_.*\.py'
  hint: |
    Please use baker recipes instead of `baker.make` or `baker.prepare`.
    This allows us to easily create complex objects with a single line of code.
```

# HTML

```yaml
- name: no inline CSS # by @codingjoe
  pattern: 'style=\"[^\"]*;[^\"]+\"'
  hint: |
    Please do not use more than one inline style attribute.
    You may use a CSS class instead.
  filePattern: .*\.(html|vue|jsx|tsx)
```

# C/C++

```yaml
- name: no line longer than 120 characters in a line (excluding comments) # by @yangcht
  pattern: ' (?<=\/\*(\*(?!\/)|[^*])*\*\/(\s|\S)*\n)(?!\/\*(\s|\S)*\n)(.{120,})(?!(\s(?!\/\*)|\S(?!\/\*))*\*\/\n)'
  hint: |
    Please do not use more than 120 characters in codes except for comments.
  filePattern: .*\.(C|cc|cxx|cpp|c++|cppm)
```
