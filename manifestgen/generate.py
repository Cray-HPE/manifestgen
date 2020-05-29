""" Cray CLI """
# pylint: disable=unused-argument, superfluous-parens
# pylint: disable=invalid-name, broad-except

import sys
import os
import argparse
import re

import semver
import yaml
import requests

from manifestgen import schema

CHART_PACKAGE_TYPE = '.tgz'

def get_args(): # pragma: NO COVER
    """Get args"""
    # pylint: disable=line-too-long, fixme
    parser = argparse.ArgumentParser(description='Generate manifest.')
    parser.add_argument('--values-path', metavar='PATH', help='DEPRECATED: Path to chart_name.yaml files to be passed as values.yaml to charts.')
    parser.add_argument('--charts-path', metavar='BLOB/URL', help='DEPRECATED: Path to chart packages or url to charts repo.')
    parser.add_argument('-i', '--in', metavar='FILE', help='Input file', default=DEFAULT_MANIFEST)
    parser.add_argument('-c', '--customizations', metavar='FILE', help='Customizations file')
    parser.add_argument('-o', '--out', metavar='FILE', help='Output file')
    parser.add_argument('--validate', default=False, action='store_true', help='Validate an existing manifest file.')
    return parser.parse_args()



def _parse_chart_name(chart_name):
    # Note this NEEDs a file extension, otherwise you'll have problems
    # because it will just split out the last period which will chop the version
    parts = os.path.splitext(chart_name)[0].split('-')
    for i, part in enumerate(parts, start=0):
        ver = None
        try:
            ver = semver.parse(part)
        except ValueError:
            pass
        if ver:
            version = '-'.join(parts[i:])
            name = '-'.join(parts[:i])
            return (name, version)

    raise ValueError("No version found in {}".format(chart_name))


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
            raise IOError("Unable to get chart repo info at: {0}".format(charts_path))

        for chart_name in charts_json:
            for version in charts_json[chart_name]:
                if chart_name not in available_charts.keys():
                    available_charts[chart_name] = '0.0.0'
                available_charts[chart_name] = semver.max_ver(
                    available_charts[chart_name], str(version['version']))
    else:
        if not os.path.isdir(charts_path):
            msg = "Expected directory of charts, not file."
            raise IOError(msg)

        for _, _, files in os.walk(charts_path):
            charts = [f for f in files if f.endswith(CHART_PACKAGE_TYPE)]
            # Use this format to easily filter out files vs dirs
            break

        for chart in charts:
            name, version = _parse_chart_name(chart)
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

    manifest = args.get('manifest')

    values_dir = args.get('values_path')
    if values_dir:
        print("# DEPRECATED! Please migrate to the customizations yaml")
    customizations = args.get('customizations')

    manifest_charts = manifest.get_charts()
    available_charts = {}
    if args.get('charts_path'):
        print("# DEPRECATED! This will be removed in future releases!")
        available_charts = get_available_charts(args['charts_path'])

    filtered_charts = []
    for manifest_chart in manifest_charts:
        chart_name = manifest_chart.get(manifest.get_key('name'))

        chart_ver = manifest_chart.get(manifest.get_key('version'))
        if not chart_ver:
            found_latest_version = available_charts.get(chart_name)
            if not found_latest_version:
                # Means the chart DNE in the remote area and the user hasn't
                # defined a version. So we will omit it.
                continue
            # User didn't provide a version, so use the latest found version
            manifest_chart.set_deep(manifest.get_key('version'), found_latest_version)

        if values_dir:
            values = get_local_values(values_dir, chart_name)
            if values is not None:
                manifest_chart.set_deep(manifest.get_key('values'), values)

        # Merge customizations schema into chart data
        if customizations:
            custom_data = customizations.get_chart(chart_name)
            manifest_chart = manifest.customize(manifest_chart, custom_data)

        filtered_charts.append(manifest_chart)

    # Set our generated manifest with the appropriate/filtered list of charts/versions
    manifest.set_charts(filtered_charts)
    # Make sure it passes schema check
    manifest.validate()

    return manifest


def main(): # pragma: NO COVER
    """ Main entrypoint """
    args = vars(get_args())

    try:
        # Validate customizations immediately to fail early
        customizations = args.get('customizations')
        if customizations:
            args['customizations'] = schema.new_schema(args['customizations'],
                                                       expected='customizations')
            args['customizations'].validate()

        args['manifest'] = schema.new_schema(args['in'], expected=['manifests', 'schema'])

        if args.get('validate', False):
            args['manifest'].validate()
            sys.exit(0)

        out_yaml = manifestgen(**args).parse()
        if args.get('out') is not None:
            with open(args['out'], 'w') as output:
                output.write(out_yaml)
        else:
            print(out_yaml)

        sys.exit(0)
    except Exception as e:
        print(e)
        sys.exit(1)


if getattr(sys, 'frozen', False): # pragma: NO COVER
    main()
