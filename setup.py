from setuptools import setup


with open('requirements.txt') as reqs_file:
    REQUIREMENTS = reqs_file.read().splitlines()

setup(
    name='manifestgen',
    description="Loftsman manifest generator",
    packages=['manifestgen'],
    include_package_data=True,
    install_requires=[REQUIREMENTS],
    entry_points='''
        [console_scripts]
        manifestgen=manifestgen.generate:main
    '''
)
