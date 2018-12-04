#!/usr/bin/env sh

set -eo pipefail
git diff --staged | relint --diff ${@:1}
