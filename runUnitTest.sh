#!/bin/bash


# Run some sanity tests to make sure the built binary works.
CLI="./dist/manifestgen"


cli_help=$($CLI --help)
if [[ $? == 0 ]]; then
    echo "PASS: manifestgen returns help"
else
    echo "FAIL: manifestgen returns an error."
    exit 1
fi