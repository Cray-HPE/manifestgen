#!/bin/bash

VERSION=$(cat version)

RPM=$(ls -l RPMS |grep rpm | grep -v src | awk '{print $NF}')

if command -v yum > /dev/null; then
    yum install -y RPMS/$RPM
elif command -v zypper > /dev/null; then
    zypper --no-gpg-checks install -y -f -l RPMS/$RPM
else
    echo "Unsupported package manager or package manager not found -- installing nothing"
    exit 1
fi

# Run some sanity tests to make sure the built binary works.
CLI="manifestgen"


cli_help=$($CLI --help)
if [[ $? == 0 ]]; then
    echo "PASS: manifestgen returns help"
else
    echo "FAIL: manifestgen returns an error."
    echo $cli_help
    exit 1
fi

cli_run=$($CLI --charts-path tests/files/ --in tests/files/schema_v2.yaml)
if [[ $? == 0 ]]; then
    echo "PASS: manifestgen --charts-path tests/files/ returns successfully"
else
    echo "FAIL: manifestgen --charts-path tests/files/ returns an error."
    echo $cli_run
    exit 1
fi
