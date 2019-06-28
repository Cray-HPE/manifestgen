""" Test the validator """
# pylint: disable=import-error, invalid-name
import os
import tempfile

from ruamel import yaml

from manifestgen import generate

def test_generate_charts_path_basic():
    """ Test `manifestgen` with only charts-path """
    # pylint: disable=protected-access

    args = {
        'charts_path': os.path.join(os.path.dirname(__file__), '..', 'files')
    }
    generate.manifestgen(**args)
    assert True is True # Just to make sure we got here


def test_custom_values():
    """ Test `manifestgen` with only charts-path """
    # pylint: disable=protected-access, superfluous-parens

    curr = os.path.dirname(os.path.realpath(__file__))
    x = generate.get_local_values(os.path.join(curr, '../files/'), 'test')
    print(x)
    assert x == {'foo': {'bar': 'baz'}}


def test_custom_values_dne():
    """ Test `manifestgen` with only charts-path """
    # pylint: disable=protected-access, superfluous-parens

    curr = os.path.dirname(os.path.realpath(__file__))
    x = generate.get_local_values(os.path.join(curr, '../files/'), 'bad')
    print(x)
    assert x is None


def test_generate_charts_path():
    """ Test `manifestgen` for charts-path """
    # pylint: disable=protected-access

    manifest_name = 'testing'
    images_registry = 'asdf'

    with tempfile.NamedTemporaryFile(suffix='.yaml') as fp:
        args = {
            'charts_path': os.path.join(os.path.dirname(__file__), '..', 'files'),
            'out': fp.name,
            'images_registry': images_registry,
            'name': manifest_name
        }
        generate.manifestgen(**args)
        fp.seek(0)
        data = yaml.safe_load(fp)

    assert data['name'] == manifest_name
    assert data['repositories']['docker'] == images_registry

    assert len(data['charts']) == 2
    for c in data['charts']:
        assert c['name'] in ['cray-istio', 'cray-etcd-operator']

def test_generate_charts_repo():
    """ Test `manifestgen` for charts-repo """
    # pylint: disable=protected-access

    manifest_name = 'testing'
    images_registry = 'dtr.dev.cray.com'
    charts_repo = 'http://helmrepo.dev.cray.com:8080'

    with tempfile.NamedTemporaryFile(suffix='.yaml') as fp:
        args = {
            'out': fp.name,
            'images_registry': images_registry,
            'charts_repo': charts_repo,
            'name': manifest_name,
            'ignore_extra': True
        }
        generate.manifestgen(**args)
        fp.seek(0)
        data = yaml.safe_load(fp)

    assert data['name'] == manifest_name
    assert data['repositories']['docker'] == images_registry
    assert data['repositories']['helm'] == charts_repo
    assert data['charts']
