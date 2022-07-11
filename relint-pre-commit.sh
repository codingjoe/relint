#!/usr/bin/env bash

set -eo pipefail
git diff --staged | relint --diff -W "${@:1}"
