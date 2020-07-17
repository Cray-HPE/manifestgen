""" Test the validator """
# pylint: disable=import-error, invalid-name, superfluous-parens, protected-access
import os

import semver

from manifestgen import generate, schema, nesteddict

TEST_FILES = os.path.join(os.path.dirname(__file__), '..', 'files')

SCHEMAV2 = os.path.join(TEST_FILES, 'schema_v2.yaml')
MANIFESTSV1BETA1 = os.path.join(TEST_FILES, 'manifests_v1beta1.yaml')
MANIFESTSV1 = os.path.join(TEST_FILES, 'manifests_v1.yaml')
CUSTOMIZATIONSV1 = os.path.join(TEST_FILES, 'customizations_v1.yaml')


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


def test_generate_manifests_v1beta1():
    """ Test `manifestgen` for charts-repo """
    # pylint: disable=protected-access

    manifest = schema.new_schema(MANIFESTSV1BETA1)
    customizations = schema.new_schema(CUSTOMIZATIONSV1)
    args = {
        'manifest': manifest,
        'customizations': customizations,
    }

    gen = generate.manifestgen(**args)
    data = gen.data()

    for chart in data.get('spec.charts', []):
        c = nesteddict.NestedDict(chart)


        if c.get('name') == 'cray-istio':
            found_istio_chart = c
            break

    print(found_istio_chart)
    assert found_istio_chart.get('version') == '3.2.0'
    assert found_istio_chart.get('values.values.ip') == '192.168.1.1'
    assert found_istio_chart.get('values.values.domain') == 'shasta.io'
    assert found_istio_chart.get('values.values.someList') == ['foo', 'bar']
    assert found_istio_chart.get('values.values.some-Dash') == 'dashed'
    assert found_istio_chart.get('values.values.someLink') == ['foo', 'bar']
    assert found_istio_chart.get('values.values.someSelfLink') == ['foo', 'bar']
    assert found_istio_chart.get('values.values.someMultiLineNoComment') == 'Foo\nBar\n'
    assert found_istio_chart.get('values.values.someMultiLineWithComment') == '# Foo\n#Bar\n'
    assert found_istio_chart.get('values.values.someYaml') == {"foo": {"bar": ["baz", "bazz"]}}
    assert found_istio_chart.get('values.values.someNull.test') is None
    assert found_istio_chart.get('values.values.someStaticNull') is None

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
        name, version = _parse_chart_name(test['chart_name'])
        assert name == test['name']
        assert version == test['version']
