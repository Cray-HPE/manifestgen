""" Functions for validating manifest schemas """
import os
import tempfile

import semver
import yamale

from yamale.validators import DefaultValidators, Validator

# Global Var
SCHEMAS = {}

def _load_schemas():
    """ Load schema version to filepath mapping """
    # pylint: disable=global-statement, invalid-name
    global SCHEMAS
    SCHEMAS = {}
    dirname = os.path.realpath(os.path.join(os.path.dirname(
        os.path.realpath(__file__)), 'schemas'))
    for f in os.listdir(dirname):
        if f.endswith('.yaml') or f.endswith('.yml'):
            parts = f.replace('.yaml', '').replace('.yml', '').split('_')
            if len(parts) != 2: # pragma: NO COVER
                continue
            key = parts[-1]
            SCHEMAS[key] = os.path.realpath(os.path.join(dirname, f))


def _get_schema_filename(schema_ver):
    """ Attempt to get the filepath for a schema version """
    # Lazy load schema filepaths
    if schema_ver not in SCHEMAS:
        _load_schemas()

    filename = SCHEMAS.get(schema_ver)
    if not filename:
        raise Exception('No schema found for: {}'.format(schema_ver))
    return filename


class Version(Validator):
    """ Custom Semver v2 validator."""
    tag = 'version'

    def _is_valid(self, value):
        # pylint: disable=broad-except
        value = '{}'.format(value)
        try:
            semver.parse(value)
        except Exception:  # pragma: NO COVER
            return False
        return True


def validate(manifest_data):
    """ Validate a manifest file against it's schema """
    # pylint: disable=invalid-name
    with tempfile.NamedTemporaryFile(suffix='.yaml') as fp:
        fp.write(manifest_data)
        fp.seek(0)

        validators = DefaultValidators.copy()  # This is a dictionary
        validators[Version.tag] = Version

        data = yamale.make_data(fp.name, parser='ruamel')
        schema_file = _get_schema_filename(data[0].get('schema', ''))
        s = yamale.make_schema(schema_file, validators=validators, parser='ruamel')
        yamale.validate(s, data)
        return manifest_data
