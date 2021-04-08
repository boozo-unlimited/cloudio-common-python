#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest

from cloudio.common.utils import string_helpers
from tests.cloudio.common.paths import update_working_directory

update_working_directory()  # Needed when: 'pipenv run python -m unittest tests/cloudio/common/{this_file}.py'


class TestCloudioCommonUtilsStringHelpers(unittest.TestCase):
    """Tests string_helpers module.
    """

    def test_camel_case_split(self):
        expression = 'ANiceDay'
        result = string_helpers.camel_case_split(expression)
        self.assertListEqual(result, ['A', 'Nice', 'Day'])

        result = string_helpers.camel_case_split(expression, lower_camel_case=False)
        self.assertListEqual(result, ['A', 'Nice', 'Day'])

        result = string_helpers.camel_case_split(expression, lower_camel_case=True)
        self.assertListEqual(result, ['A', 'Nice', 'Day'])

        # Lower camel-case
        expression = 'aNiceDay'

        result = string_helpers.camel_case_split(expression)
        self.assertListEqual(result, ['Nice', 'Day'])

        result = string_helpers.camel_case_split(expression, lower_camel_case=False)
        self.assertListEqual(result, ['Nice', 'Day'])

        result = string_helpers.camel_case_split(expression, lower_camel_case=True)
        self.assertListEqual(result, ['a', 'Nice', 'Day'])
