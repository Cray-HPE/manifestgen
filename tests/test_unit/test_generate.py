""" Test the validator """
# pylint: disable=import-error, invalid-name, superfluous-parens, protected-access
import os

from manifestgen import generate, schema, nesteddict

TEST_FILES = os.path.join(os.path.dirname(__file__), '..', 'files')

SCHEMAV2 = os.path.join(TEST_FILES, 'schema_v2.yaml')
MANIFESTSV1 = os.path.join(TEST_FILES, 'manifests_v1.yaml')
CUSTOMIZATIONSV1 = os.path.join(TEST_FILES, 'customizations_v1.yaml')

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

    manifest = schema.new_schema(SCHEMAV2)
    args = {
        'charts_path': os.path.join(os.path.dirname(__file__), '..', 'files'),
        'manifest': manifest
    }
    data = generate.manifestgen(**args).data()

    assert len(data['charts']) == 2
    for c in data['charts']:
        assert c['name'] in ['cray-istio', 'cray-etcd-operator']

def test_generate_charts_repo():
    """ Test `manifestgen` for charts-repo """
    # pylint: disable=protected-access

    charts_repo = 'http://helmrepo.dev.cray.com:8080'
    manifest = schema.new_schema(SCHEMAV2)
    args = {
        'manifest': manifest,
        'charts_path': charts_repo,
    }


    data = generate.manifestgen(**args).data()
    assert data['charts'] == manifest.get('charts')


def test_generate_locked():
    """ Test `manifestgen` for charts-repo """
    # pylint: disable=protected-access

    manifest = schema.new_schema(os.path.join(TEST_FILES, 'locked_manifest.yaml'))
    args = {
        'manifest': manifest,
        'charts_path': os.path.join(os.path.dirname(__file__), '..', 'files'),
    }

    locked_data = generate.manifestgen(**args).data()
    print(locked_data)
    assert locked_data['charts'] == locked_data.get('charts')

    for chart in locked_data['charts']:
        if chart['name'] == 'cray-istio':
            locked_istio_chart = chart
            break

    assert locked_istio_chart['version'] == '0.0.1'


def test_generate_manifests_v1():
    """ Test `manifestgen` for charts-repo """
    # pylint: disable=protected-access

    manifest = schema.new_schema(MANIFESTSV1)
    customizations = schema.new_schema(CUSTOMIZATIONSV1)
    args = {
        'manifest': manifest,
        'customizations': customizations,
    }

    gen = generate.manifestgen(**args)
    data = gen.data()

    for release in data.get('spec.releases', []):
        r = nesteddict.NestedDict(release)


        if r.get('spec.chart.name') == 'cray-istio':
            found_istio_chart = r
            break

    print(found_istio_chart)
    assert found_istio_chart.get('spec.chart.version') == '3.2.0'
    assert found_istio_chart.get('spec.chart.values.ip') == '192.168.1.1'
    assert found_istio_chart.get('spec.chart.values.domain') == 'shasta.io'
    assert found_istio_chart.get('spec.chart.values.someList') == ['foo', 'bar']
    assert found_istio_chart.get('spec.chart.values.some-Dash') == 'dashed'
    assert found_istio_chart.get('spec.chart.values.someLink') == ['foo', 'bar']
    assert found_istio_chart.get('spec.chart.values.someSelfLink') == ['foo', 'bar']
    assert found_istio_chart.get('spec.chart.values.someMultiLineNoComment') == 'Foo\nBar\n'
    assert found_istio_chart.get('spec.chart.values.someMultiLineWithComment') == '# Foo\n#Bar\n'
    assert found_istio_chart.get('spec.chart.values.someYaml') == {"foo": {"bar": ["baz", "bazz"]}}
    assert found_istio_chart.get('spec.chart.values.someNull.test') is None
    assert found_istio_chart.get('spec.chart.values.someStaticNull') is None

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
