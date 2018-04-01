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

The optional `error` attribute allows you to only show a warning but not exit
with a bad (non-zero) exit code. The default is `true`.

The following command will lint all files in the current directory:

.. code-block:: bash

    relint -c .relint.yml **

The default configuration file name is `.relint.yaml` within your working
directory, but you can provide any YAML or JSON file.
