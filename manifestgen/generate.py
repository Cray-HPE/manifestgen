""" Cray CLI """
# pylint: disable=unused-argument, superfluous-parens
# pylint: disable=invalid-name

import sys
import os
import argparse

from ruamel import yaml

from manifestgen import validator


CHART_PACKAGE_TYPE = '.tgz'

def get_args():
    """Get args"""
    parser = argparse.ArgumentParser(description='Generate manifest.')
    parser.add_argument('charts', metavar='BLOB', help='Path to chart packages.')
    parser.add_argument('--name', dest='name', help='Manifest name.')
    parser.add_argument('--fastfail', default=False, action='store_true',
                        help='Tell the manifest to fail on first error.')
    parser.add_argument('--docker-repo', help='Docker repo to install from.')
    parser.add_argument('--helm-repo', help='Chart repo to install from.')
    parser.add_argument('-o', '--out', help='Output file')
    parser.add_argument('--ignore-extra', default=False, action='store_true',
                        help='Don\'t error for extra charts that are in the master manifest.')
    return parser.parse_args()


class _NullStream:  # pylint: disable=no-init, old-style-class
    """ NullStream used for yaml dump """

    def write(self, *args, **kwargs):
        """ Null writer """
        pass

    def flush(self, *args, **kwargs):
        """ Null flusher """
        pass


class Manifest(object):  # pylint: disable=old-style-class
    """ Load yaml file, and do things with it """

    def __init__(self, path):
        with open(path) as fp:
            data = yaml.safe_load(fp)
        self.data = data
        self.yaml = None

    def _to_string(self, data):
        self.yaml = data

    def get_charts(self):
        """ Get current manifest charts """
        return self.data.get('charts', [])

    def set_charts(self, charts):
        """ Set the current manifest charts """
        self.data['charts'] = charts

    def validate(self):
        """ Validate manifest data """
        self.parse()
        validator.validate(self.yaml)

    def parse(self):
        """ Generate manifest yaml from data """
        yaml.YAML().dump(self.data, _NullStream(), transform=self._to_string)
        return self.yaml


def validate_charts_path(chart_dir):
    """ Make sure path passed by user exists """
    if not os.path.isdir(chart_dir):
        return False
    return True


def find_charts(chart_dir):
    """ Get all the charts in the directory """
    for _, _, files in os.walk(chart_dir):
        charts = [f for f in files if f.endswith(CHART_PACKAGE_TYPE)]
        # Use this format to easily filter out files vs dirs
        break
    resp = {}
    for chart in charts:
        i = chart.split('-')
        version = i[-1].replace(CHART_PACKAGE_TYPE, '')
        name = '-'.join(i[:-1])
        resp[name] = {'version': version}
    return resp


def manifestgen(**args):
    """ Generate the manifest """
    mani_path = os.path.join(os.path.realpath(os.path.dirname(__file__)),
                             'files', 'master_manifest.yaml')
    manifest = Manifest(mani_path)

    if args.get('name') is not None:
        manifest.data['name'] = args['name']
    if args.get('fastfail') is not None:
        manifest.data['failOnFirstError'] = args['fastfail']
    if args.get('docker_repo') is not None:
        manifest.data['repositories']['docker'] = args['docker_repo']
    if args.get('helm_repo') is not None:
        manifest.data['repositories']['helm'] = args['helm_repo']

    chart_dir = args['charts']
    all_charts = manifest.get_charts()

    if not validate_charts_path(chart_dir):
        raise Exception("{} does not exist!".format(chart_dir))

    blob_charts = find_charts(chart_dir)

    manifest_charts = []
    for chart in all_charts:
        c = blob_charts.get(chart['name'])
        if c:
            chart.update(c)
            del blob_charts[chart['name']]
            manifest_charts.append(chart)

    if blob_charts and not args.get('ignore_extra'):
        # Some charts exist that aren't in the master manifest
        extra_charts = ", ".join(blob_charts.keys())
        msg = "Some charts exist in the blob that don't exist in the master manifest: {}"
        raise Exception(msg.format(extra_charts))

    # Trim master chart to only include charts in blob
    manifest.set_charts(manifest_charts)
    # Make sure it passes schema check
    manifest.validate()

    out_yaml = manifest.parse()

    if args.get('out') is not None:
        with open(args['out'], 'w') as output:
            output.write(out_yaml)
    else:
        print(out_yaml)


def main():
    """ Main entrypoint """
    args = get_args()
    manifestgen(**vars(args))
    sys.exit(0)


if getattr(sys, 'frozen', False):
    main()
