# -*- coding: utf-8 -*-

from cloudio.common.utils import string_helpers


def generate_attribute_names_by_name(name: str) -> tuple[str, str]:
    """Generates attribute names according to our coding standards.
    """
    if len(name) == 0:
        return tuple()

    if name[0] == '_':
        name = name[1:]

    if '_' in name:
        words = list(filter(None, name.split('_')))
    elif '-' in name:
        words = list(filter(None, name.split('-')))
    else:
        words = string_helpers.camel_case_split(name, lower_camel_case=True)

    public_attribute_name = '_'.join((map(lambda x: x.lower(), words)))
    private_attribute_name = '_' + public_attribute_name

    return private_attribute_name, public_attribute_name


def generate_setters_from_attribute_name(attribute_name: str) -> tuple[str, str]:
    """Generates method setter names according to our coding standards.
    """
    if len(attribute_name) == 0:
        return tuple()

    if attribute_name[0] == '_':
        attribute_name = attribute_name[1:]

    if '_' in attribute_name:
        words = list(filter(None, attribute_name.split('_')))
    else:
        words = string_helpers.camel_case_split(attribute_name, lower_camel_case=True)

    setter_name = '_'.join((map(lambda x: x.lower(), words)))
    setter01 = 'set_' + setter_name

    setter_name = ''.join((map(lambda x: x.capitalize(), words)))
    setter02 = 'set' + setter_name

    return setter01, setter02
