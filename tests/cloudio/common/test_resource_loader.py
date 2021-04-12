#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import unittest

from tests.cloudio.common.paths import update_working_directory
from cloudio.common.utils import path_helpers
from cloudio.common.utils.resource_loader import ResourceLoader

update_working_directory()  # Needed when: 'pipenv run python -m unittest tests/cloudio/common/{this_file}.py'


class TestCloudioCommonUtilsResourceLoader(unittest.TestCase):
    """Tests path_helpers module.
    """

    def test_load_from_locations(self):
        config_file = 'test.config'
        locations = ['/home/python', 'C:/']     # Bad location format
        result = ResourceLoader.load_from_locations(config_file, locations)
        self.assertDictEqual(result, dict())

        locations = ['home://home/python', 'file://C:/', 'https://cloudio.hevs.ch']
        result = ResourceLoader.load_from_locations(config_file, locations)
        self.assertDictEqual(result, dict())

    def test_load_from_path(self):
        import contextlib
        config_file = 'test.config'
        working_path = path_helpers.path_from_file(__file__)

        # Create tiny config file
        config_file_path = os.path.join(working_path, config_file)
        with contextlib.suppress(FileNotFoundError):
            os.remove(config_file_path)
        file = open(config_file_path, 'a')
        file.write('[test]\nparam1 = true')
        file.close()

        # Load tiny config file
        locations = ['file://' + path_helpers.prettify(working_path), ]
        result = ResourceLoader.load_from_locations(config_file, locations)
        self.assertDictEqual(result, {'test': {'param1': 'true'}})

        # Tidy up
        with contextlib.suppress(FileNotFoundError):
            os.remove(config_file_path)

    def test_load_from_home(self):
        import contextlib

        config_file = 'test.config'
        home_dir = path_helpers.home_directory()

        # Create tiny config file
        config_file_path = os.path.join(home_dir, config_file)
        with contextlib.suppress(FileNotFoundError):
            os.remove(config_file_path)
        file = open(config_file_path, 'a')
        file.write('[date]\nyear = 2020')
        file.close()

        # Load tiny config file
        locations = ['home://', ]
        result = ResourceLoader.load_from_locations(config_file, locations)
        self.assertDictEqual(result, {'date': {'year': '2020'}})

        # Tidy up
        with contextlib.suppress(FileNotFoundError):
            os.remove(config_file_path)
