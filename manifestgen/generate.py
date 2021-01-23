""" Cray CLI """
# pylint: disable=unused-argument, superfluous-parens
# pylint: disable=invalid-name, broad-except

import argparse
try:
    from importlib import metadata
except ImportError:
    # Running on pre-3.8 Python; use importlib-metadata package
    import importlib_metadata as metadata
import os
import sys
import warnings

from manifestgen import io
from manifestgen.customizations import Customizations
from manifestgen.schema import new_schema


CHART_PACKAGE_TYPE = '.tgz'


def get_args(): # pragma: NO COVER
    """Get args"""
    # pylint: disable=line-too-long, fixme
    version = metadata.version('manifestgen')
    parser = argparse.ArgumentParser(description='Generate manifest.')
    parser.add_argument('-c', '--customizations',     metavar='FILE', type=argparse.FileType('r'), help='Customizations file')
    parser.add_argument('-i', '--in',  dest='input',  metavar='FILE', type=argparse.FileType('r'), default=sys.stdin,  help='Input file')
    parser.add_argument('-o', '--out', dest='output', metavar='FILE', type=argparse.FileType('w'), default=sys.stdout, help='Output file')
    parser.add_argument('--validate', default=False, action='store_true', help='Validate an existing manifest file.')
    parser.add_argument('--values-path', metavar='PATH', help='DEPRECATED: Path to chart_name.yaml files to be passed as values.yaml to charts.')
    parser.add_argument('--version', action='version', version=f'%(prog)s {version}')
    args = parser.parse_args()
    if args.values_path:
        warnings.warn("Option --values-path is deprecated and will be removed, use --customizations instead", DeprecationWarning, stacklevel=2)
    return args


def get_local_values(a_dir, chart_name):
    """ Open values file if it exists and return the yaml as a dict """
    value_file = os.path.join(a_dir, f'{chart_name}.yaml')
    if not os.path.isfile(value_file):
        print(f"error: no such file: {value_file}", file=sys.stderr)
        return None
    with open(value_file) as fp:
        return io.load(fp)


def manifestgen(manifest, customizations=None, values_path=None):
    """ Generate the manifest """
    # pylint: disable=too-many-branches
    updated_charts = []
    for chart in manifest.get_releases():
        # Merge values file into chart
        if values_path:
            values = get_local_values(values_path, chart.get(manifest.RELEASE_NAME_REF))
            if values:
                chart.set_deep(manifest.RELEASE_VALUES_REF, values)
        # Merge customizations into chart
        if customizations:
            values = customizations.get_chart(chart.get(manifest.RELEASE_NAME_REF))
            if values:
                chart.set_deep(manifest.RELEASE_VALUES_REF, values, update=True)
        # Save updated chart
        updated_charts.append(chart)
    # Update manifest charts
    manifest.set_releases(updated_charts)
    # Make sure updates are valid
    manifest.validate()
    return manifest


def main(): # pragma: NO COVER
    """ Main entrypoint """
    args = get_args()

    try:
        # Validate customizations immediately to fail early
        customizations = None
        if args.customizations:
            with (args.customizations):
                customizations = Customizations.load(args.customizations)
                customizations.validate()

        # Validate manifest
        with args.input as f:
            manifest = new_schema(io.load(f))
        manifest.validate()

        # Early abort if only validating
        if args.validate:
            sys.exit(0)

        # Generate manifest based on customizations
        manifestgen(manifest, customizations, args.values_path)

        # Output updated manifest
        with args.output as f:
            manifest.dump(stream=f)
        sys.exit(0)
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


if getattr(sys, 'frozen', False): # pragma: NO COVER
    main()
