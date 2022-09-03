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
      pattern: '(?i)todo' # case insensitive flag
      hint: Get it done right away!
      filePattern: .*\.(py|js)
      error: false

The ``name`` attribute is the name of your linter, the ``pattern`` can be
any regular expression. The linter does lint entire files, therefore your
expressions can match multiple lines and include newlines.

You can narrow down the file types your linter should be working with, by
providing the optional ``filePattern`` attribute. The default is ``.*``.

The optional ``error`` attribute allows you to only show a warning but not exit
with a bad (non-zero) exit code. The default is ``true``.

The following command will lint all files in the current directory:

.. code-block:: bash

    relint -c .relint.yml **

The default configuration file name is ``.relint.yml`` within your working
directory, but you can provide any YAML or JSON file.

If you prefer linting changed files (cached on git) you can use the option
``--diff [-d]`` or ``--git-diff [-g]``:

.. code-block:: bash

    git diff --unified=0 | relint my_file.py --diff


pre-commit
^^^^^^^^^^

You can automate the linting process by adding a `pre-commit`_ hook to your
project. Add the following entry to your ``.pre-commit-config.yaml``:

.. code-block:: yaml

    - repo: https://github.com/codingjoe/relint
      rev: 1.4.0
      hooks:
        - id: relint
          args: [-W]  # optional, if you want to fail on warnings during commit

Samples
-------

.. code-block:: yaml

    - name: db fixtures
      pattern: 'def test_[^(]+\([^)]*(customer|product)(, |\))'
      hint: Use model_bakery recipies instead of db fixtures.
      filePattern: test_.*\.py

    - name: model_bakery recipies
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

.. _`pre-commit`: https://pre-commit.com/
.. _`relint-pre-commit.sh`: relint-pre-commit.sh
