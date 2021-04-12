#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest

from tests.cloudio.common.paths import update_working_directory
from cloudio.common.utils import attribute_helpers

update_working_directory()  # Needed when: 'pipenv run python -m unittest tests/cloudio/common/{this_file}.py'


class TestCloudioCommonUtilsAttributeHelpers(unittest.TestCase):
    """Tests attribute_helpers module.
    """

    def test_generate_attribute_names_by_name(self):
        attribute_name = 'power'
        attribute_names = attribute_helpers.generate_attribute_names_by_name(attribute_name)
        self.assertTrue(isinstance(attribute_names, tuple))
        self.assertTupleEqual(attribute_names, ('_power', 'power'))

        attribute_name = 'powerForMoreFreedom'
        attribute_names = attribute_helpers.generate_attribute_names_by_name(attribute_name)
        self.assertTrue(isinstance(attribute_names, tuple))
        self.assertTupleEqual(attribute_names, ('_power_for_more_freedom', 'power_for_more_freedom'))

        attribute_name = '_powerForMoreFreedom'
        attribute_names = attribute_helpers.generate_attribute_names_by_name(attribute_name)
        self.assertTrue(isinstance(attribute_names, tuple))
        self.assertTupleEqual(attribute_names, ('_power_for_more_freedom', 'power_for_more_freedom'))

        attribute_name = 'flowers_and_bees'
        attribute_names = attribute_helpers.generate_attribute_names_by_name(attribute_name)
        self.assertTrue(isinstance(attribute_names, tuple))
        self.assertTupleEqual(attribute_names, ('_flowers_and_bees', 'flowers_and_bees'))

        attribute_name = 'trees-and-flowers'
        attribute_names = attribute_helpers.generate_attribute_names_by_name(attribute_name)
        self.assertTrue(isinstance(attribute_names, tuple))
        self.assertTupleEqual(attribute_names, ('_trees_and_flowers', 'trees_and_flowers'))

    def test_generate_attribute_names_by_name_coverage(self):
        attribute_name = ''
        attribute_names = attribute_helpers.generate_attribute_names_by_name(attribute_name)
        self.assertTupleEqual(attribute_names, tuple())

    def test_generate_setters_from_attribute_name(self):
        attribute_name = 'power'
        setter_method_names = attribute_helpers.generate_setters_from_attribute_name(attribute_name)
        self.assertTrue(isinstance(setter_method_names, tuple))
        self.assertTupleEqual(setter_method_names, ('set_power', 'setPower'))

        attribute_name = 'powerForMoreFreedom'
        setter_method_names = attribute_helpers.generate_setters_from_attribute_name(attribute_name)
        self.assertTrue(isinstance(setter_method_names, tuple))
        self.assertTupleEqual(setter_method_names, ('set_power_for_more_freedom', 'setPowerForMoreFreedom'))

        attribute_name = 'power_for_more_freedom'
        setter_method_names = attribute_helpers.generate_setters_from_attribute_name(attribute_name)
        self.assertTrue(isinstance(setter_method_names, tuple))
        self.assertTupleEqual(setter_method_names, ('set_power_for_more_freedom', 'setPowerForMoreFreedom'))

        attribute_name = '_power_for_more_freedom'
        setter_method_names = attribute_helpers.generate_setters_from_attribute_name(attribute_name)
        self.assertTrue(isinstance(setter_method_names, tuple))
        self.assertTupleEqual(setter_method_names, ('set_power_for_more_freedom', 'setPowerForMoreFreedom'))

    def test_generate_setters_from_attribute_name_coverage(self):
        attribute_name = ''
        attribute_names = attribute_helpers.generate_setters_from_attribute_name(attribute_name)
        self.assertTupleEqual(attribute_names, tuple())
