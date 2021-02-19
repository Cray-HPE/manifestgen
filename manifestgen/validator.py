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
""" Functions for validating manifest schemas """
# pylint: disable=global-statement,invalid-name
import os
import tempfile

import semver
import yamale
from yamale.validators import DefaultValidators, Validator

from manifestgen.nesteddict import NestedDict


# Global Var
SCHEMAS = NestedDict({})

def _load_schemas():
    global SCHEMAS
    packge_dir_name = 'schemas'
    schemas_dict = NestedDict()
    dirname = os.path.realpath(os.path.join(os.path.dirname(
        os.path.realpath(__file__)), packge_dir_name))
    for root, _, files in os.walk(dirname):
        if '__' in root:
            # ignore python cache dirs
            continue
        temp_dict = {}
        for f in files:
            if '__' in f or f[0] == '.':
                # ignore python init and hidden files
                continue
            parts = f.replace('.yaml', '').replace('.yml', '').split('_')
            if "schema" not in parts: # pragma: NO COVER
                continue
            key = parts[-1]
            temp_dict[key] = os.path.realpath(os.path.join(root, f))
        schemas_dict.set_deep(root.replace(dirname, packge_dir_name).replace("/", "."), temp_dict)
    SCHEMAS = NestedDict(schemas_dict[packge_dir_name])


def _get_schema_filename(schema_ver):
    """ Attempt to get the filepath for a schema version """
    # Lazy load schema filepaths

    schema_key = schema_ver.replace("/", ".")

    if not SCHEMAS.get(schema_key):
        _load_schemas()

    filename = SCHEMAS.get(schema_key)
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
            semver.VersionInfo.parse(value)
        except Exception:  # pragma: NO COVER
            return False
        return True


class SealedSecret(Validator):
    """ Custom Semver v2 validator."""
    tag = 'sealedSecret'

    def _is_valid(self, value):
        # pylint: disable=broad-except
        try:
            kind = value.get("kind", value.get("Kind"))
            if kind not in "SealedSecret":
                raise Exception("Could not find valid SealedSecret")
        except Exception:  # pragma: NO COVER
            return False
        return True


def validate(manifest_data):
    """ Validate a manifest file against it's schema """
    # pylint: disable=invalid-name
    with tempfile.NamedTemporaryFile(suffix='.yaml', mode='w') as fp:
        fp.write(manifest_data)
        fp.seek(0)
        data = yamale.make_data(fp.name)

    validators = DefaultValidators.copy()  # This is a dictionary
    validators[Version.tag] = Version
    validators[SealedSecret.tag] = SealedSecret
    schema_file = _get_schema_filename(data[0][0].get('schema', data[0][0].get('apiVersion', '')))
    s = yamale.make_schema(schema_file, validators=validators)
    try:
        yamale.validate(s, data)
    except ValueError as e:
        msg = "Error validating manifest: \n" + '\n'.join(str(e).split('\n')[2:])
        raise Exception(msg) from e

    return manifest_data
