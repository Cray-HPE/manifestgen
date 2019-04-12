""" Nox definitions for tests, docs, and linting """
from __future__ import absolute_import
import os

import nox  # pylint: disable=import-error


COVERAGE_FAIL = 80


@nox.session(python=['2.7'])
def tests(session):
    """Default unit test session.
    This is meant to be run against any python version intended to be used.
    """
    # Install all test dependencies, then install this package in-place.
    path = 'tests'
    session.install('-r', 'requirements-test.txt')
    session.install('-e', '.')

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


@nox.session(python=['2.7'])
def lint(session):
    """Run linters.
    Returns a failure if the linters find linting errors or sufficiently
    serious code quality issues.
    """
    run_cmd = ['pylint', 'manifestgen', 'tests']

    session.install('-r', 'requirements-lint.txt')
    session.install('.')
    session.run(*run_cmd)


@nox.session(python="2.7")
def cover(session):
    """Run the final coverage report.
    This outputs the coverage report aggregating coverage from the unit
    test runs, and then erases coverage data.
    """
    session.install('coverage', 'pytest-cov')
    session.run('coverage', 'report', '--show-missing',
                '--fail-under={}'.format(COVERAGE_FAIL))
    session.run('coverage', 'erase')
