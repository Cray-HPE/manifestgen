""" Cray CLI """
# pylint: disable=unused-argument, superfluous-parens
# pylint: disable=invalid-name, broad-except

import sys
import os
import argparse

import yaml

from manifestgen import schema

CHART_PACKAGE_TYPE = '.tgz'

def get_args(): # pragma: NO COVER
    """Get args"""
    # pylint: disable=line-too-long, fixme
    parser = argparse.ArgumentParser(description='Generate manifest.')
    parser.add_argument('--values-path', metavar='PATH', help='DEPRECATED: Path to chart_name.yaml files to be passed as values.yaml to charts.')
    parser.add_argument('-i', '--in', metavar='FILE', help='Input file', required=True)
    parser.add_argument('-c', '--customizations', metavar='FILE', help='Customizations file')
    parser.add_argument('-o', '--out', metavar='FILE', help='Output file')
    parser.add_argument('--validate', default=False, action='store_true', help='Validate an existing manifest file.')
    return parser.parse_args()


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

    filtered_charts = []
    for manifest_chart in manifest_charts:
        chart_name = manifest_chart.get(manifest.get_key('name'))

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
