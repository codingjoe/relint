ReLint
======

**Regular Expression Linter**

*Write your own linting rules using regular expressions.*

Installation
------------

.. code-block:: bash

    pip install relint

Usage
-----

You can write your own regular rules in a YAML file, like so:

.. code-block:: YAML

    - name: No ToDo
      pattern: "[tT][oO][dD][oO]"
      hint: Get it done right away!
      filename:
        - "*.py"
        - "*.js"
      error: false

The ``name`` attribute is the name of your linter, the ``pattern`` can be
any regular expression. The linter does lint entire files, therefore your
expressions can match multiple lines and include newlines.

You can narrow down the file types your linter should be working with, by
providing the optional ``filename`` attribute. The default is ``*``.

The ``filename`` list can also accept exclude patterns, prefixed by ``!``.
For example, to include all python files except ``run.py`` you may use:

.. code-block:: YAML

    - name: No ToDo
      pattern: "[tT][oO][dD][oO]"
      hint: Get it done right away!
      filename:
        - "*.py"
        - "!run.py"
      error: false

Note that the patterns are processed top to bottom, and the order matters:

.. code-block:: YAML

    - name: No ToDo
      pattern: "[tT][oO][dD][oO]"
      hint: Get it done right away!
      filename:
        - "!run.py"
        - "*.py"  # the exclude pattern above is overriden by this broader include pattern
      error: false

To include a filenames which starts with a literal ``!`` (eg. ``!important!.txt``),
use an escape sequence like so:

.. code-block:: YAML

    - name: No ToDo
      pattern: "[tT][oO][dD][oO]"
      hint: Get it done right away!
      filename:
        - "!*.txt"  # exclude all txt files
        - "\\!important!.txt"  # include the !important!.txt file despite the previous exclude pattern
        - "*.py"  # include all python files
        - "!!important_but_excluded!.py"  # exclude the !important_but_excluded!.py file despite the previous include pattern
      error: false

The optional `error` attribute allows you to only show a warning but not exit
with a bad (non-zero) exit code. The default is `true`.

The following command will lint all files in the current directory:

.. code-block:: bash

    relint -c .relint.yml **

The default configuration file name is `.relint.yaml` within your working
directory, but you can provide any YAML or JSON file.

If you prefer linting changed files (cached on git) you can use the option
`--diff [-d]`:

.. code-block:: bash

    git diff | relint my_file.py --diff

This option is useful for pre-commit purposes. Here an example of how to use it
with `pre-commit`_ framework:

.. code-block:: YAML

    - repo: https://github.com/codingjoe/relint
      rev: 0.5.0
      hooks:
        - id: relint

You can find an example of `relint-pre-commit.sh`_ in this repository.

Samples
-------

.. code-block:: yaml

    - name: db fixtures
      pattern: "def test_[^(]+\\([^)]*(customer|product)(, |\\))"
      hint: Use model_mommy recipies instead of db fixtures.
      filename:
        - "**/test_*.py"

    - name: model_mommy recipies
      pattern: "mommy\\.make\\("
      hint: Please use mommy.make_recipe instead of mommy.make.
      filename:
        - "**/test_*.py"
        - "conftest.py"
        - "**/conftest.py"

    - name: the database is lava
      pattern: "@pytest.fixture.*\\n[ ]*def [^(]+\\([^)]*(db|transactional_db)(, |\\))"
      hint: Please do not create db fixtures but model_mommy recipies instead.
      filename:
        - "*.py"

    - name: No logger in management commands
      pattern: "(logger|import logging)"
      hint: "Please write to self.stdout or self.stderr in favor of using a logger."
      filename:
        - "*/management/commands/*.py"

.. _`pre-commit`: https://pre-commit.com/
.. _`relint-pre-commit.sh`: relint-pre-commit.sh
