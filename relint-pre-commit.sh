#!/usr/bin/env bash

set -eo pipefail
git diff --staged --unified=0 | relint --diff -W "${@:1}"
