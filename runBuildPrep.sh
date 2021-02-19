#!/bin/bash
# MIT License
#
# (C) Copyright [2020] Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
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
