""" Nested Dict class """

from collections.abc import Mapping
from copy import deepcopy


def deepupdate(self, other, shallow=False):
    """Recursivley updates `self` with items from `other`.

    By default, values from `other` will be deepcopy-ed into `self`. If
    `shallow=True`, values will simply be assigned, resulting in a "shallow"
    copy.
    """
    # pylint: disable=C0103
    for k, v in other.items():
        # Cases: (self.get(k), v) is
        #   * (Mapping, Mapping) -> deepupdate(self[k], v)
        #   * (Mapping, not Mapping) -> self[k] = v
        #   * (not Mapping, Mapping) -> self[k] = v
        #   * (not Mapping, not Mapping) -> self[k] = v
        self_k = self.get(k)
        if isinstance(self_k, Mapping) and isinstance(v, Mapping):
            deepupdate(self_k, v)
        else:
            self[k] = v if shallow else deepcopy(v)
    return self


class NestedDict(dict):
    """dict object that allows for period separated gets:
    a_config.get('some.key', default) ==
        a_config.get('some', {}).get('key', default)
    given:
        a_config == {"some": {"key": "some value"}}"""

    def __repr__(self):
        dictrepr = dict.__repr__(self)
        return '%s(%s)' % (type(self).__name__, dictrepr)

    @classmethod
    def to_yaml(cls, representer, node):
        """ How to represent for yaml lib """
        return representer.represent_dict(dict(node))

    def set_deep(self, key, value, update=False):
        """ Deep set a value. \n
        Ex: `d.set_deep('a.b.c', 'foo')` is the same as: \n
        `d.setdefault('a', {}).setdefault('b', {})['c'] = 'foo'`
        """
        setter = self
        keys = key.split('.')
        last = keys.pop()
        for k in keys:
            setter = setter.setdefault(k, {})
        if update and last in setter:
            deepupdate(setter[last], value)
        else:
            setter[last] = deepcopy(value)

    def get(self, key, default=None):
        """ Deep get a value. \n
        E: `d.get('a.b.c', 'bar')` is the same as: \n
        `d.get('a', {}).get('b', {}).get('c', 'bar')`
        """
        keys = key.split('.')
        found = {}
        for k in self.keys():
            found[k] = self[k]
        for k in keys:
            if not isinstance(found, dict):
                return default
            found = found.get(k)
            if found is None:
                return default
        return found
