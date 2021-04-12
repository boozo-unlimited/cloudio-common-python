#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from tests.cloudio.common.paths import update_working_directory
from cloudio.common.utils import timestamp_helpers

update_working_directory()  # Needed when: 'pipenv run python -m unittest tests/cloudio/common/{this_file}.py'


class TestCloudioCommonUtilsTimestampHelpers(unittest.TestCase):
    """Tests timestamp_helpers module.
    """

    def test_get_time_in_milliseconds(self):
        import datetime

        time_ms = timestamp_helpers.get_time_in_milliseconds()
        self.assertTrue(time_ms > 1609459200000)  # 2021-01-01

        a_date_time = datetime.datetime(2021, 1, 1)
        time_ms = timestamp_helpers.get_time_in_milliseconds(a_date_time)
        self.assertTrue(time_ms == 1609459200000)
