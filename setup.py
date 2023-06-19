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
#
import subprocess
from os.path import dirname
from os.path import isdir
from os.path import join
from os import devnull
import re

import pkg_resources

from setuptools import find_namespace_packages
from setuptools import setup

version_re = re.compile("^Version: (.+)$", re.M)

with open("LICENSE") as license_file:
    LICENSE = license_file.read()


def readme() -> str:
    """
    Print the README file.
    :returns: Read README file.
    """
    with open("README.md") as file:
        return str(file.read())


def get_version():
    d = dirname(__file__)

    if isdir(join(d, ".git")):
        # Get the version using "git describe".
        cmd = "git describe --tags --match v[0-9]*".split()
        try:
            version = subprocess.check_output(cmd).decode().strip()
        except subprocess.CalledProcessError:
            print("Unable to get version number from git tags")
            exit(1)

        # PEP 386 compatibility
        if "-" in version:
            version = ".post".join(version.split("-")[:2])

        # Don't declare a version "dirty" merely because a time stamp has
        # changed. If it is dirty, append the branch name as a suffix to
        # indicate a development revision after the release.
        with open(devnull, "w") as fd_devnull:
            subprocess.call(["git", "status"], stdout=fd_devnull, stderr=fd_devnull)

        cmd = "git diff-index --name-only HEAD".split()
        try:
            dirty = subprocess.check_output(cmd).decode().strip()
        except subprocess.CalledProcessError:
            print("Unable to get git index status")
            exit(1)

        if dirty != "":
            version += ".dev1"
    else:
        try:
            # Extract the version from the PKG-INFO file.
            with open(join(d, "PKG-INFO")) as f:
                version = version_re.search(f.read()).group(1)
        except FileNotFoundError:
            # Maybe this package is already installed, and setup.py is invoked
            # out of context by a scanner.
            version = pkg_resources.get_distribution("manifestgen").version
    return version

setup(
    name='manifestgen',
    description="Loftsman manifest generator",
    long_description=readme(),
    version=get_version(),
    license=LICENSE,
    url='https://github.com/Cray-HPE/manifestgen',
    packages=find_namespace_packages(),
    include_package_data=True,
    zip_safe=False,
    extras_require={
        'ci': {
            'nox',
        },
        'lint': {
            'pylint',
            'six>=1.11.0',
        },
        'test': {
            'mock',
            'names',
            'pytest',
            'pytest-cov',
            'requests-mock',
            'six>=1.11.0',
        }
    },
    install_requires=[
        'certifi==2022.12.7',
        'jinja2==3.1.2',
        'markupsafe<2.2.0',
        'pyyaml==6.0',
        'requests>=2.20.0',
        'semver==3.0.1',
        'yamale==4.0.0',
    ],
    entry_points={
        "console_scripts": ["manifestgen=manifestgen.generate:main"],
    },
)
