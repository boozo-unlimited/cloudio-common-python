#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest

import time

from tests.cloudio.common.paths import update_working_directory
from cloudio.common.utils import path_helpers

update_working_directory()  # Needed when: 'pipenv run python -m unittest tests/cloudio/common/{this_file}.py'


class TestCloudioCommonUtilsPathHelpers(unittest.TestCase):
    """Tests path_helpers module.
    """

    def test_prettify(self):
        path = 'C:\\Users\\Python\\'
        prettified = path_helpers.prettify(path)
        self.assertTrue(prettified == 'C:/Users/Python/')

        path = '~/in/home/directory'
        prettified = path_helpers.prettify(path)
        # Check if Windows or Linux home directory
        self.assertTrue('Users' in prettified or 'home' in prettified)
