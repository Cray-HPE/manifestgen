#!/bin/bash

./version.sh > build_version


if command -v yum > /dev/null; then
    yum install -y \
        python3 \
        python3-devel \
        python3-setuptools \
        python3-pip
elif command -v zypper > /dev/null; then
    zypper install -y -f -l \
        python3 \
        python3-devel \
        python3-setuptools \
        python3-pip
else
    echo "Unsupported package manager or package manager not found -- installing nothing"
    exit 1
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
