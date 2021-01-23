""" Various Schema objects that are passed in via yaml files """
# pylint: disable=invalid-name,no-else-raise,no-else-return,unnecessary-pass
import re
from collections.abc import MutableMapping, MutableSequence

import jinja2
import yaml

from manifestgen import filters, io
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
        obj = io.load(data)
        # Recursively render templated values in obj
        rerun = True
        while rerun:
            obj['spec'], rerun = render(obj['spec'], obj['spec'], False)
        return cls(obj)

    CHARTS_REF = 'spec.kubernetes.services'

    def get_chart(self, name):
        """ Get an embedded chart dict from the given name """
        return self.get(f'{self.CHARTS_REF}.{name}', {})
