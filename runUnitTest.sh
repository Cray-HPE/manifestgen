#!/bin/bash

# Remove before just to ensure a clean nox env.
rm -rf .nox

set -e

# Note we are running this all here as we want to break the build BEFORE an rpm is built.
nox

# Remove these files again to speed up source tar for build step.
rm -rf .nox