""" I/O utilities """

import yaml

def str_presenter(dumper, data):
    "Use the | scalar syntax for yaml"
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

yaml.add_representer(str, str_presenter)

load = yaml.safe_load
dump = yaml.safe_dump
