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
""" Various Schema objects that are passed in via yaml files """
# pylint: disable=invalid-name,no-else-raise,no-else-return,unnecessary-pass
import re
from collections.abc import MutableMapping, MutableSequence

import jinja2
import yaml

from manifestgen import filters, ioutils
from manifestgen.schema import BaseSchema


jinjaEnv = jinja2.Environment()
filters.load(jinjaEnv)


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


class Customizations(BaseSchema):
    """ Customizations """

    @classmethod
    def load(cls, fp, fixme="~FIXME~"):
        """ Load customizations """
        # Read lines looking for fixme values
        data = ""
        found_fixmes = []
        for num, line in enumerate(fp, 1):
            try:
                strippedl = line.lstrip()
                if strippedl and strippedl[0] != "#" and fixme in line:
                    found_fixmes.append(f"Line {num}: {line}")
            except IndexError:
                print(line)
                raise
            data += line
        if found_fixmes:
            raise ValueError("{} detected:\n{}".format(fixme, ''.join(found_fixmes)))
        # Load data
        obj = ioutils.load(data)
        # Recursively render templated values in obj
        rerun = True
        while rerun:
            obj['spec'], rerun = render(obj['spec'], obj['spec'], False)
        return cls(obj)

    CHARTS_REF = 'spec.kubernetes.services'

    def get_chart(self, name):
        """ Get an embedded chart dict from the given name """
        return self.get(f'{self.CHARTS_REF}.{name}', {})
