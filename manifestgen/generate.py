""" Cray CLI """
# pylint: disable=unused-argument, superfluous-parens
# pylint: disable=invalid-name

import sys
import os
import argparse
import re

import semver
from ruamel import yaml
import requests

from manifestgen import validator

CHART_PACKAGE_TYPE = '.tgz'
DEFAULT_MANIFEST = os.path.join(os.path.realpath(os.path.dirname(__file__)),
                                'files', 'master_manifest.yaml')

def get_args(): # pragma: NO COVER
    """Get args"""
    # pylint: disable=line-too-long, fixme
    parser = argparse.ArgumentParser(description='Generate manifest.')
    parser.add_argument('--values-path', metavar='PATH', help='Path to chart_name.yaml files to be passed as values.yaml to charts.')
    parser.add_argument('--charts-path', metavar='BLOB/URL', help='Path to chart packages or url to charts repo.')
    parser.add_argument('--name', dest='name', help='Manifest name.')
    parser.add_argument('--schema', dest='schema', help='Manifest schema to generate.', default='v2')
    parser.add_argument('--fastfail', default=False, action='store_true',
                        help='Tell the manifest to fail on first error.')
    parser.add_argument('--images-registry', metavar='URL', help='Docker registry where images reside.')
    parser.add_argument('--charts-repo', metavar='URL', help='Deprecated. This will be removed in future releases.')
    # TODO: Set default to baked in manifest for now. When all tools migrate to external manifest, remove the default
    # and no longer bake manifest in.
    parser.add_argument('-i', '--in', metavar='FILE', help='Input file', default=DEFAULT_MANIFEST)
    parser.add_argument('-o', '--out', metavar='FILE', help='Output file')
    parser.add_argument('--ignore-extra', default=True, action='store_true',
                        help='Deprecated. This will be removed in future releases.')
    parser.add_argument('--version-lock', default=False, action='store_true',
                        help='Do not update chart versions that exist in master manifest (default: %(default)s).')
    parser.add_argument('--validate', metavar='PATH', help='Validate an existing manifest file.')
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
        self.schema = data['schema']

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.schema)

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


def get_available_charts(charts_path):
    """ Get all available latest-version charts either from the local blob or charts repo """
    available_charts = {}

    charts_path = os.path.expanduser(charts_path)

    if not os.path.exists(charts_path): # assume URL if doesn't exist
        charts_path = re.sub(r"/$", "", charts_path)

        try:
            charts_json = requests.get('{}/api/charts'.format(charts_path))
            charts_json = charts_json.json()
        except Exception:
            raise Exception("Unable to get chart repo info at: {0}".format(charts_path))

        for chart_name in charts_json:
            for version in charts_json[chart_name]:
                if chart_name not in available_charts.keys():
                    available_charts[chart_name] = '0.0.0'
                available_charts[chart_name] = semver.max_ver(
                    available_charts[chart_name], str(version['version']))
    else:
        if os.path.isfile(charts_path):
            msg = "Expected directory of charts, not file."
            raise Exception(msg)

        for _, _, files in os.walk(charts_path):
            charts = [f for f in files if f.endswith(CHART_PACKAGE_TYPE)]
            # Use this format to easily filter out files vs dirs
            break

        for chart in charts:
            parts = chart.split('-')
            version = parts[-1].replace(CHART_PACKAGE_TYPE, '')
            name = '-'.join(parts[:-1])
            if name not in available_charts.keys():
                available_charts[name] = '0.0.0'
            available_charts[name] = semver.max_ver(available_charts[name], version)

    return available_charts


def get_local_values(a_dir, chart_name):
    """ Open values file if it exists and return the yaml as a dict """
    value_file = os.path.join(a_dir, '{}.yaml'.format(chart_name))
    if os.path.isfile(value_file):
        with open(value_file) as fp:
            return yaml.safe_load(fp)
    return None



def manifestgen(**args):
    """ Generate the manifest """
    # pylint: disable=too-many-branches

    mani_path = args.get('in')
    manifest = Manifest(mani_path)

    if args.get('name') is not None:
        manifest.data['name'] = args['name']
    if args.get('schema') is not None:
        manifest.data['schema'] = args['schema']
    if args.get('fastfail') is not None:
        manifest.data['failOnFirstError'] = args['fastfail']
    if args.get('images_registry') is not None:
        manifest.data['repositories']['docker'] = args['images_registry']
    if not os.path.exists(args['charts_path']):
        manifest.data['repositories']['helm'] = args['charts_path']

    values_dir = args.get('values_path')

    master_manifest_charts = manifest.get_charts()
    available_charts = get_available_charts(args.get('charts_path'))

    filtered_charts = []
    for master_manifest_chart in master_manifest_charts:
        available_chart_version = available_charts.get(master_manifest_chart['name'])
        if available_chart_version:
            # Set version if it DNE or update it if not version lock
            if 'version' not in master_manifest_chart.keys() or not args.get('version_lock', False):
                master_manifest_chart['version'] = available_chart_version

            if values_dir and manifest.schema != 'v1':
                values = get_local_values(values_dir, master_manifest_chart['name'])
                if values is not None:
                    master_manifest_chart['values'] = values
            filtered_charts.append(master_manifest_chart)
            del available_charts[master_manifest_chart['name']]

    if available_charts and not args.get('ignore_extra'):
        # Some charts exist that aren't in the master manifest
        extra_charts = ", ".join(available_charts.keys())
        msg = "Some charts exist in the blob that don't exist in the master manifest: {}"
        raise Exception(msg.format(extra_charts))

    # Set our generated manifest with the appropriate/filtered list of charts/versions
    manifest.set_charts(filtered_charts)

    # Make sure it passes schema check
    manifest.validate()

    out_yaml = manifest.parse()

    if args.get('out') is not None:
        with open(args['out'], 'w') as output:
            output.write(out_yaml)
    else:
        print(out_yaml)


def main(): # pragma: NO COVER
    """ Main entrypoint """
    args = vars(get_args())

    if args.get('validate') is not None:
        manifest = Manifest(args['validate'])
        manifest.validate()
    else:
        args['charts_path'] = args.get('charts_path', args.get('charts_repo'))

        if 'charts_repo' in args:
            del args['charts_repo']

        if (args.get('charts_path') is None):
            raise Exception('The charts-path argument must be provided')

        manifestgen(**args)
    sys.exit(0)


if getattr(sys, 'frozen', False): # pragma: NO COVER
    main()
