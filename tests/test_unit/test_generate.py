""" Test the validator """
import os
import tempfile

import pytest
from ruamel import yaml

from manifestgen import generate

def test_generate():
    """ Test `manifestgen` """
    # pylint: disable=protected-access

    chart_name = 'testing'
    docker_repo = 'asdf'
    helm_repo = 'lkjh'

    with tempfile.NamedTemporaryFile(suffix='.yaml') as fp:
        args = {
            'charts': os.path.join(os.path.dirname(__file__), '..', 'files'),
            'out': fp.name,
            'docker_repo': docker_repo,
            'helm_repo': helm_repo,
            'name': chart_name
        }
        generate.generate(**args)
        fp.seek(0)
        data = yaml.safe_load(fp)

    assert data['name'] == chart_name
    assert data['repositories']['docker'] == docker_repo
    assert data['repositories']['helm'] == helm_repo
    assert len(data['charts']) == 2
    for c in data['charts']:
        assert c['name'] in ['cray-istio', 'cray-etcd-operator']
