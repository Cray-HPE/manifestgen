""" Test the validator """
# pylint: disable=import-error, invalid-name, superfluous-parens, protected-access
import os
import tempfile

from ruamel import yaml

from manifestgen import generate

def test_generate_charts_path_basic():
    """ Test `manifestgen` with only charts-path """
    # pylint: disable=protected-access

    args = {
        'in': generate.DEFAULT_MANIFEST,
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
            'in': generate.DEFAULT_MANIFEST,
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
            'in': generate.DEFAULT_MANIFEST,
            'out': fp.name,
            'images_registry': images_registry,
            'charts_path': charts_repo,
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


def test_generate_locked():
    """ Test `manifestgen` for charts-repo """
    # pylint: disable=protected-access

    manifest_name = 'testing'
    images_registry = 'dtr.dev.cray.com'

    with tempfile.NamedTemporaryFile(suffix='.yaml') as fp:
        args = {
            'in': os.path.join(os.path.dirname(__file__), '..', 'files/locked_manifest.yaml'),
            'out': fp.name,
            'images_registry': images_registry,
            'charts_path': os.path.join(os.path.dirname(__file__), '..', 'files'),
            'name': manifest_name,
            'ignore_extra': True,
            'version_lock': True,
        }
        generate.manifestgen(**args)
        fp.seek(0)
        locked_data = yaml.safe_load(fp)

    assert locked_data['name'] == manifest_name
    assert locked_data['repositories']['docker'] == images_registry
    assert locked_data['charts']

    with tempfile.NamedTemporaryFile(suffix='.yaml') as fp:
        args = {
            'in': os.path.join(os.path.dirname(__file__), '..', 'files/locked_manifest.yaml'),
            'out': fp.name,
            'images_registry': images_registry,
            'charts_path': os.path.join(os.path.dirname(__file__), '..', 'files'),
            'name': manifest_name,
            'ignore_extra': True,
            'version_lock': False,
        }
        generate.manifestgen(**args)
        fp.seek(0)
        data = yaml.safe_load(fp)

    assert data['name'] == manifest_name
    assert data['repositories']['docker'] == images_registry
    assert data['charts']

    for chart in data['charts']:
        if chart['name'] == 'cray-istio':
            istio_chart = chart
            break

    for chart in locked_data['charts']:
        if chart['name'] == 'cray-istio':
            locked_istio_chart = chart
            break

    assert istio_chart['version'] == '1.0.2'
    assert locked_istio_chart['version'] == '0.0.1'


def test_parse_chart_name():
    """ Test chart name parser """
    tests = [
        {'chart_name': 'foo-1.2.3.tgz', 'name': 'foo', 'version': '1.2.3'},
        {'chart_name': 'foo-1.2.3-rc1.tgz', 'name': 'foo', 'version': '1.2.3-rc1'},
        {'chart_name': 'foo-bar-1.2.3.tgz', 'name': 'foo-bar', 'version': '1.2.3'},
        {'chart_name': 'foo-1.2.3-123.tgz', 'name': 'foo', 'version': '1.2.3-123'},
        {'chart_name': 'foo-1.2.3-123.1.tgz', 'name': 'foo', 'version': '1.2.3-123.1'},
    ]
    for test in tests:
        print('Testing chart name parsing for: {}'.format(test['chart_name']))
        name, version = generate._parse_chart_name(test['chart_name'])
        assert name == test['name']
        assert version == test['version']
