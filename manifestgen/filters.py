""" Custom Jinja2 Filters """
import yaml


def load(env):
    """Helper to load custom filters into a Jinja2 Environment"""
    env.filters["toYaml"] = to_yaml


def to_yaml(obj):
    """ to yaml filter """
    return yaml.safe_dump(obj, default_flow_style=False)
