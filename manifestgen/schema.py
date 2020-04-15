""" Various Schema objects that are passed in via yaml files """
# pylint: disable=invalid-name,no-else-raise,no-else-return,unnecessary-pass
import re

import jinja2
import yaml

from manifestgen import validator, nesteddict


class BaseSchema:
    """ Load yaml file, and do things with it """

    _keys = {}

    def __init__(self, path):

        if isinstance(path, dict):
            data = path
        else:
            with open(path) as fp:
                data = yaml.safe_load(fp)
        self._data = nesteddict.NestedDict(data)
        self._schema = data.get('schema', data.get('apiVersion'))
        parts = data.get('schema', data.get('apiVersion', '')).split('/')
        if not parts:
            raise Exception("Schema Version Could Not Be Parsed")
        self._version = parts.pop().lower()
        self._kind = parts.pop().lower() if parts else "schema"


    def __repr__(self):
        return "%s(%r)" % (self.__class__, self._schema)

    def _dict(self):
        return dict(self._data)

    def validate(self):
        """ Validate manifest data """
        validator.validate(self.parse())

    def parse(self):
        """ Generate manifest yaml from data """
        return yaml.dump(self._dict())

    def data(self):
        """ Get data """
        return self._data

    def get(self, key, default=None):
        """ Getter for the internal data """
        return self._data.get(key, default=default)

    def set(self, key, value):
        """ Setter for the internal data """
        self._data.set_deep(key, value)

    def version(self):
        """ Get the version of the schema """
        return self._version

    def kind(self):
        """ Get the kind of the schema """
        return self._kind

    def get_key(self, key):
        """ Get the proper key for the given common name """
        return self._keys.get(key)


class Customizations(BaseSchema):
    """ Load yaml file, and do things with it """

    _keys = {
        'values': 'values',
        'repository': 'repository',
        'chart_base': 'spec.kubernetes.services'
    }

    def __init__(self, path, fixme="~FIXME~"):
        rendered = yaml.safe_load(self._render(path, fixme))
        super().__init__(rendered)
        # Validate to ensure the rendering didn't affect anything
        self.validate()

    @classmethod
    def _render(cls, path, fixme):
        data = ""
        found_fixmes = []
        with open(path) as fp:
            for num, line in enumerate(fp, 1):
                data += line
                if fixme in line:
                    found_fixmes.append("Line {}: {}".format(num, line))
        if found_fixmes:
            raise Exception("{} key found in {}:\n{}".format(fixme, path, ''.join(found_fixmes)))

        scrubbed = cls._scrub(data)
        count = 0
        while '===TEMPLATE_VALUE___' in scrubbed:
            count += 1
            template = jinja2.Template(data)
            rendered = template.render(yaml.safe_load(scrubbed)['spec'])
            data = cls._descrub(rendered)
            scrubbed = cls._scrub(data)
            if count > 10:
                raise Exception("Too many nested lookups. Maximum: {}".format(count))

        return rendered

    @staticmethod
    def _scrub(data):
        return re.sub(r'\{\{(.*)\}\}', r'===TEMPLATE_VALUE___\1___===', data)

    @staticmethod
    def _descrub(data):
        return re.sub(r'===TEMPLATE_VALUE___(\s?\S+\s?)___===', r'{{\1}}', data)

    def get_chart(self, name):
        """ Get an embedded chart dict from the given name """
        return self.get('{}.{}'.format(self.get_key('chart_base'), name), {})


class CustomizationsV1(Customizations):
    """ Kind: Customizations, Version: V1 """
    _keys = {
        'values': 'values',
        'repository': 'repository',
        'chart_base': 'spec.kubernetes.services'
    }



class Manifest(BaseSchema):
    """ Load yaml file, and do things with it """
    _chart_key = 'spec.releases'
    _keys = {
        'name': 'metadata.name',
        'version': 'spec.chart.version',
        'values': 'spec.chart.values',
    }

    def _dict(self):
        return dict(self._data)

    def get_charts(self):
        """ Get current manifest charts """
        return [nesteddict.NestedDict(i) for i in self.get(self._chart_key, [])]

    def set_charts(self, charts):
        """ Set the current manifest charts """
        charts = [dict(i) for i in charts]
        self.set(self._chart_key, charts)


    def customize(self, chart, data):
        """ Properly apply customization data to the given chart for the schema version """
        # pylint: disable=no-self-use
        # This works for now, but may need to change if the customizations
        # schema changes
        chart['spec']['chart'].update(data)
        return chart


class SchemaV2(Manifest):
    """ DEPRECATED: Old Style Schema """
    _chart_key = 'charts'
    _keys = {
        'name': 'name',
        'version': 'version',
        'values': 'values',
    }

    def customize(self, chart, data):
        """ Properly apply customization data to the given chart for the schema version """
        # Only support values customizations in Schema V2
        chart.setdefault(self._keys['values'], {})
        chart[self._keys['values']].update(data)
        return chart


class ManifestV1(Manifest):
    """ Kind: Manifests, Version: V1 """

    _keys = {
        'name': 'metadata.name',
        'version': 'spec.chart.version',
        'values': 'spec.chart.values',
    }

def new_schema(file, expected=None):
    """ Get the proper schema object for the given file's kind/version """

    with open(file) as fp:
        data = fp.read()
    # Scrub out any possible jinja items so it can load as valid yaml
    scrubbed = re.sub(r'\{\{(.*)\}\}', r'\1', data)
    # Use this to parse version/kind
    temp_schema = BaseSchema(yaml.safe_load(scrubbed))

    kind = temp_schema.kind()
    version = temp_schema.version()

    if expected and kind not in expected:
        raise Exception("Expected {} file, got {}".format(expected, kind))

    if kind == "schema":
        if version == 'v1':
            raise Exception("Schema v1 has been deprecated and is no longer supported.")
        else:
            return SchemaV2(file)
    elif kind == "manifests":
        if version == 'v1':
            return ManifestV1(file)
        else:
            return Manifest(file)
    elif kind == "customizations":
        if version == 'v1':
            return CustomizationsV1(file)
        else:
            return Customizations(file)

    raise Exception("Unable to deteremine schema version: {}".format(file))
