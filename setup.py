from setuptools import setup


with open('LICENSE.txt') as license_file:
    LICENSE = license_file.read()

with open('requirements.txt') as reqs_file:
    REQUIREMENTS = reqs_file.read().splitlines()

with open('version') as vers_file:
    VERSION = vers_file.read()

setup(
    name='manifestgen',
    author="Cray Inc.",
    author_email="rbezdicek@cray.com",
    url="http://cray.com",
    description="Loftsman manifest generator",
    long_description="Loftsman manifest generator",
    version=VERSION,
    packages=['manifestgen'],
    license=LICENSE,
    include_package_data=True,
    install_requires=[REQUIREMENTS] + [
        'importlib-metadata ~= 1.0 ; python_version < "3.8"',
    ],
    entry_points='''
        [console_scripts]
        manifestgen=manifestgen.generate:main
    '''
)
