#!/bin/bash

VERSION="$(cat ./version).$BUILD_NUMBER"

echo $VERSION > build_version


if command -v yum > /dev/null; then
    yum install -y python-devel
    yum install -y python34
    yum install -y python34-setuptools
    yum install -y python3-devel
elif command -v zypper > /dev/null; then
    zypper install -y -f -l python-pip
    zypper install -y -f -l python-devel
    zypper install -y -f -l python3
    zypper install -y -f -l python3-setuptools
    zypper install -y -f -l python3-devel
else
    echo "Unsupported package manager or package manager not found -- installing nothing"
    exit 1
fi

PIP2="pip"

function set_pip2(){

    if command -v pip2.7 > /dev/null; then
        PIP2="pip2.7"
    elif command -v pip-2.7 > /dev/null; then
        PIP2="pip-2.7"
    elif command -v pip2 > /dev/null; then
        PIP2="pip2"
    fi
}

set_pip2

if ! command -v pip3 > /dev/null; then
    easy_install-3.4 pip || easy_install-3.6 pip || easy_install pip
fi
pip3 install --upgrade pip
pip3 install --upgrade --no-use-pep517 nox
# We want to build as python2.7 so install with normal pip
$PIP2 install --upgrade pip
# On sles12 the pip upgrade changes the symlink from pip-2.7 to pip2.7, cool.
set_pip2

$PIP2 install --ignore-installed pyinstaller==3.3

pyinstaller_version=$(python2 -m PyInstaller --version)
if [[ $? != 0 ]]; then
    echo "FAIL: pyinstaller not installed with python2."
    exit 1
fi

$PIP2 install --ignore-installed -r requirements.txt

find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf

rm -rf .nox

set -e

# Note we are running this all here as we want to break the build BEFORE an rpm is built.
nox
