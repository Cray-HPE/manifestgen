""" Various Schema objects """
# pylint: disable=invalid-name,no-else-raise,no-else-return,unnecessary-pass

from manifestgen import ioutils, nesteddict, validator


class BaseSchema:
    """ Base schema """

    def __init__(self, data):
        self._data = nesteddict.NestedDict(data)
        self._schema = data.get('schema', data.get('apiVersion'))
        parts = data.get('schema', data.get('apiVersion', '')).split('/')
        if not parts:
            raise Exception("Schema Version Could Not Be Parsed")
        self._version = parts.pop().lower()
        self._kind = parts.pop().lower() if parts else "schema"

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self._dict())

    def __str__(self):
        return self.dump()

    def _dict(self):
        return dict(self._data)

    def dump(self, *args, **kwds):
        """ Dump data """
        return ioutils.dump(self._dict(), *args, **kwds)

    def validate(self):
        """ Validate manifest data """
        validator.validate(self.dump())

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


class Manifest(BaseSchema):
    """ Kind: Manifests, Version: v1 """

    CHARTS_REF = 'spec.releases'
    RELEASE_NAME_REF = 'metadata.name'
    RELEASE_VALUES_REF = 'spec.chart.values'

    def _dict(self):
        return dict(self._data)

    def get_releases(self):
        """ Get current manifest charts """
        return [nesteddict.NestedDict(i) for i in self.get(self.CHARTS_REF, [])]

    def set_releases(self, charts):
        """ Set the current manifest charts """
        charts = [dict(i) for i in charts]
        self.set(self.CHARTS_REF, charts)


class SchemaV2(Manifest):
    """ DEPRECATED: Old Style Schema """

    CHARTS_REF = 'charts'
    RELEASE_NAME_REF = 'name'
    RELEASE_VALUES_REF = 'values'


class ManifestV1Beta1(Manifest):
    """ Kind: Manifests, Version: v1beta1 """

    CHARTS_REF = 'spec.charts'
    RELEASE_NAME_REF = 'name'
    RELEASE_VALUES_REF = 'values'


class ManifestV1(Manifest):
    """ Kind: Manifests, Version: v1 """
    pass


def new_schema(data):
    """ Get the proper schema object for the given file's kind/version """
    # Use this to parse version/kind
    temp_schema = BaseSchema(data)

    kind = temp_schema.kind()
    version = temp_schema.version()

    if kind == "schema":
        if version == 'v1':
            raise ValueError("Schema v1 has been deprecated and is no longer supported.")
        else:
            return SchemaV2(data)
    elif kind == "manifests":
        if version == 'v1beta1':
            return ManifestV1Beta1(data)
        elif version == 'v1':
            return ManifestV1(data)
        else:
            return Manifest(data)

    raise ValueError("Unable to determine schema version")
