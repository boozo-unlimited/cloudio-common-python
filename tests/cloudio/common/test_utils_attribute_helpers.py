#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest

from tests.cloudio.common.paths import update_working_directory
from cloudio.common.utils import attribute_helpers

update_working_directory()  # Needed when: 'pipenv run python -m unittest tests/cloudio/common/{this_file}.py'


class TestCloudioCommonUtilsAttributeHelpers(unittest.TestCase):
    """Tests attribute_helpers module.
    """

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
