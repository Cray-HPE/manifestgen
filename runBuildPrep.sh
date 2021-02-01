#!/bin/bash

VERSION="$(cat ./version)"

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

if ! command -v pip3 > /dev/null; then
    easy_install-3.4 pip || easy_install-3.6 pip || easy_install pip
fi
pip3 install --upgrade pip
pip3 install --upgrade --no-use-pep517 nox

pip3 install --ignore-installed pyinstaller

pyinstaller_version=$(python3 -m PyInstaller --version)
if [[ $? != 0 ]]; then
    echo "FAIL: pyinstaller not installed with python3."
    exit 1
fi

pip3 install --ignore-installed -r requirements.txt

find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf
