# -*- coding: utf-8 -*-

import os


def prettify(path_name: str) -> str:
    """Makes all necessary stuff to get a usable path (specially under Windows)

    :param path_name: Path to make pretty
    """

    if path_name:
        # Remove backslashes from path
        path_name = path_name.replace('\\', '/')

        if path_name[0] == '~':
            base_path = os.path.expanduser(path_name[0])
            remaining_path = path_name[2:] if path_name[1] == '/' else path_name[1:]
            path_name = os.path.join(base_path, remaining_path)

        # and again
        path_name = path_name.replace('\\', '/')

    return path_name


def home_directory():
    home_dir = os.path.expanduser('~')
    return home_dir


def path_from_file(path_file_name: str) -> str:
    """Returns the path of the given file location string.
    """
    path = os.path.abspath(os.path.dirname(path_file_name))
    return path


def create_directory_structure(path: str):
    """Creates one or more directories.
    """
    os.makedirs(path, exist_ok=True)


def remove_directory(path):
    from shutil import rmtree

    rmtree(path, ignore_errors=True)
