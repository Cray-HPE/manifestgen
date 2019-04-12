#!/bin/bash

echo "PWD"
echo $PWD

echo "ls -la"
ls -la
echo "ls -la .dist"
ls -la ./dist


# Run some sanity tests to make sure the built binary works.
CLI="./dist/manifestgen"


cli_help=$($CLI --help)
if [[ $? == 0 ]]; then
    echo "PASS: manifestgen returns help"
else
    echo "FAIL: manifestgen returns an error."
    echo $cli_help
    exit 1
fi


cli_run=$($CLI tests/files/)
if [[ $? == 0 ]]; then
    echo "PASS: manifestgen tests/files/ returns successfully"
else
    echo "FAIL: manifestgen tests/files/ returns an error."
    echo $cli_run
    exit 1
fi