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
""" Nox definitions for tests, docs, and linting """
from __future__ import absolute_import
import os

import nox  # pylint: disable=import-error


COVERAGE_FAIL = 80


@nox.session(python=['3'])
def tests(session):
    """Default unit test session.
    This is meant to be run against any python version intended to be used.
    """
    # Install all test dependencies, then install this package in-place.
    path = 'tests'
    session.install('.[test]')
    session.install('.')

    if session.posargs:
        path = session.posargs[0]


    # Run py.test against the tests.
    session.run(
        'py.test',
        '--quiet',
        '--cov=manifestgen',
        '--cov=tests',
        '--cov-append',
        '--cov-config=.coveragerc',
        '--cov-report=',
        '--cov-fail-under={}'.format(COVERAGE_FAIL),
        path,
        *session.posargs
    )


@nox.session(python=['3'])
def lint(session):
    """Run linters.
    Returns a failure if the linters find linting errors or sufficiently
    serious code quality issues.
    """
    run_cmd = ['pylint', 'manifestgen', 'tests']

    session.install('.[lint]')
    session.install('.')
    session.run(*run_cmd)


@nox.session(python="3")
def cover(session):
    """Run the final coverage report.
    This outputs the coverage report aggregating coverage from the unit
    test runs, and then erases coverage data.
    """
    session.install('coverage', 'pytest-cov')
    session.run('coverage', 'report', '--show-missing',
                '--fail-under={}'.format(COVERAGE_FAIL))
    session.run('coverage', 'erase')
