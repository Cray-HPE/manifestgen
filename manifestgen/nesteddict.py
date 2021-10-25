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
""" Nested Dict class """

from collections.abc import Mapping
from copy import deepcopy


def deepupdate(self, other, shallow=False):
    """Recursivley updates `self` with items from `other`.

    By default, values from `other` will be deepcopy-ed into `self`. If
    `shallow=True`, values will simply be assigned, resulting in a "shallow"
    copy.
    """
    # pylint: disable=invalid-name
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
        return f"{type(self).__name__}({dictrepr})"

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
        # pylint: disable=invalid-name
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

        # pylint: disable=invalid-name
        for k, v in self.items():
            found[k] = v
        for k in keys:
            if not isinstance(found, dict):
                return default
            found = found.get(k)
            if found is None:
                return default
        return found
