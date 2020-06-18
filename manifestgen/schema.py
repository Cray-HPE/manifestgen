""" Various Schema objects that are passed in via yaml files """
# pylint: disable=invalid-name,no-else-raise,no-else-return,unnecessary-pass
import re
from collections.abc import MutableMapping, MutableSequence

import jinja2
import yaml

from manifestgen import validator, nesteddict, filters

jinjaEnv = jinja2.Environment()
filters.load(jinjaEnv)


def str_presenter(dumper, data):
    "Use the | scalar syntax for yaml"
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

yaml.add_representer(str, str_presenter)


def render(obj, ctx, rerun):
    """recursively attempt to render the given object via jinja"""
    if isinstance(obj, str):
        # We only want to render a string with the special keys. Otherwise,
        # would could inadvertently lose newlines.
        if re.search(r'\{\{(.*)\}\}', obj):
            s = jinjaEnv.from_string(obj).render(ctx)
            try:
                _obj = yaml.safe_load(s)
            except yaml.error.YAMLError:
                _obj = s
            else:
                # If there is a # in the string the yaml load strips it.
                # Which is why _obj will be nothing here. So revert
                # back to the rendered string instead.
                if _obj is None:
                    _obj = s
            return (_obj, True)
        else:
            # Return original object since there was nothing to render
            return (obj, rerun)
    if isinstance(obj, MutableMapping):
        for key in obj:
            obj[key], rerun = render(obj[key], ctx, rerun)
    elif isinstance(obj, MutableSequence):
        for idx, item in enumerate(obj):
            obj[idx], rerun = render(item, ctx, rerun)
    return (obj, rerun)


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
        rendered = self._render(path, fixme)
        super().__init__(rendered)
        # Validate to ensure the rendering didn't affect anything
        self.validate()

    @classmethod
    def _render(cls, path, fixme):
        data = ""
        found_fixmes = []
        with open(path) as fp:
            for num, line in enumerate(fp, 1):
                try:
                    strippedl = line.lstrip()
                    if strippedl and strippedl[0] != "#" and fixme in line:
                        found_fixmes.append("Line {}: {}".format(num, line))
                except IndexError:
                    print(line)
                    raise
                data += line
        if found_fixmes:
            raise Exception("{} key found in {}:\n{}".format(fixme, path, ''.join(found_fixmes)))

        yaml_data = yaml.safe_load(data)

        rerun = True
        while rerun:
            yaml_data['spec'], rerun = render(yaml_data['spec'], yaml_data['spec'], False)

        return yaml_data

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
