#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest

import time

from tests.cloudio.common.paths import update_working_directory
from cloudio.common.utils import datetime_helpers

update_working_directory()  # Needed when: 'pipenv run python -m unittest tests/cloudio/common/{this_file}.py'


class TestCloudioCommonUtilsDatetimeHelpers(unittest.TestCase):
    """Tests datetime_helpers module.
    """

    def test_get_current_timestamp(self):
        value = datetime_helpers.get_current_timestamp()
        self.assertTrue(value > 0)
        self.assertTrue(isinstance(value, int))

        # Must be older then 1970
        self.assertTrue(value > datetime_helpers.get_timestamp(datetime_helpers.EPOCH))

        time.sleep(0.2)
        value2 = datetime_helpers.get_current_timestamp()
        self.assertTrue(value2 > value)

    def test_get_timestamp(self):
        import datetime

        current_datetime = datetime.datetime.utcnow()
        timestamp = datetime_helpers.get_timestamp(current_datetime)
        self.assertTrue(timestamp > 0)
        self.assertTrue(isinstance(timestamp, int))
        # Must be older then 1970
        self.assertTrue(timestamp > datetime_helpers.get_timestamp(datetime_helpers.EPOCH))

    def test_unix_time_millis(self):
        import datetime

        a_date_time = datetime.datetime(2021, 11, 28, 23, 55, 59, 347504)
        time_ms = datetime_helpers._unix_time_millis(a_date_time)
        self.assertTrue(time_ms == 1638143759347)

        a_date_time = a_date_time + datetime.timedelta(milliseconds=1)
        time_ms_next = datetime_helpers._unix_time_millis(a_date_time)
        self.assertTrue(time_ms + 1 == time_ms_next)


