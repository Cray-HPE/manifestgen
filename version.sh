#!/usr/bin/env bash

set -eo pipefail

ROOTDIR="$(dirname "${BASH_SOURCE[0]}")"

cat "${ROOTDIR}/manifestgen/__init__.py" \
| grep '__version__' \
| sed -e 's/^.*__version__.*=.*"\([^"]\+\)".*$/\1/'
