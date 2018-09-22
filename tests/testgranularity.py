# !/usr/bin/env python

"""Utils test"""
from datetime import datetime
from dateutil import tz
import calendar
import logging
import time
import unittest

from rollup import granularities

logging.basicConfig(level=logging.DEBUG)


class TestGranularity(unittest.TestCase):
    """Utils Test Class"""

    def test_sec_2_min(self):
        """Testing second to minute conversion"""
        now = long(time.time())
        now_min = (now / 60) * 60
        min_candidate = granularities.seconds_to_minute(now, None)
        self.assertEqual(min_candidate, now_min)

    def test_sec_2_hour(self):
        """seconds -> hour"""
        now = long(time.time())
        now_hour = (now / 3600) * 3600
        hour_candidate = granularities.seconds_to_hour(now, None)
        self.assertEqual(hour_candidate, now_hour)

    def test_sec_2_day(self):
        """seconds -> day"""
        cur_tz = 'America/New_York'
        now = long(time.time())
        gmt_date = datetime.utcfromtimestamp(long(now))
        gmt_date = gmt_date.replace(tzinfo=tz.gettz('UTC'))
        tz_date = gmt_date.astimezone(tz.gettz(cur_tz))
        tz_date = tz_date.replace(hour=0, minute=0, second=0, microsecond=0)
        start_day = calendar.timegm(tz_date.utctimetuple())
        day_candidate = granularities.seconds_to_day(now, cur_tz)
        self.assertEqual(day_candidate, start_day)

    def test_sec_2_month(self):
        """seconds -> month"""
        cur_tz = 'America/New_York'
        now = long(time.time())
        gmt_date = datetime.utcfromtimestamp(long(now))
        gmt_date = gmt_date.replace(tzinfo=tz.gettz('UTC'))
        tz_date = gmt_date.astimezone(tz.gettz(cur_tz))
        tz_date = tz_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_month = calendar.timegm(tz_date.utctimetuple())
        month_candidate = granularities.seconds_to_month(now, cur_tz)
        self.assertEqual(month_candidate, start_month)

    def test_sec_2_year(self):
        """seconds -> year"""
        cur_tz = 'America/New_York'
        now = long(time.time())
        gmt_date = datetime.utcfromtimestamp(long(now))
        gmt_date = gmt_date.replace(tzinfo=tz.gettz('UTC'))
        tz_date = gmt_date.astimezone(tz.gettz(cur_tz))
        tz_date = tz_date.replace(month=1, day=1, hour=0, minute=0, second=0,
                                  microsecond=0)
        start_year = calendar.timegm(tz_date.utctimetuple())
        year_candidate = granularities.seconds_to_year(now, cur_tz)
        self.assertEqual(year_candidate, start_year)

    def test_cv_time(self):
        """Testing convert time function"""
        now = long(time.time())
        now_min = (now / 60) * 60
        min_candidate = granularities.convert_time(granularities.MINUTE, now,
                                                   timezone=None)
        self.assertEqual(min_candidate, now_min)

        ex = False
        try:
            granularities.convert_time('abcd', 1, timezone=None)
        except ValueError:
            ex = True

        self.assertTrue(ex)

    def test_get_interval_month(self):
        """Test get interval for month"""
        now = long(1513789666)
        expected_start = 1512082800
        expected_end = 1514761200
        start, end = granularities.get_interval(
            granularities.GRANULARITY_TEXT_VALUE[granularities.MONTH],
            now,
            timezone='Europe/Madrid')
        self.assertEquals(start, expected_start)
        self.assertEquals(end, expected_end)

    def test_get_interval_year(self):
        """Test get interval for year"""
        now = long(1513789666)
        expected_start = 1483225200
        expected_end = 1514761200
        start, end = granularities.get_interval(
            granularities.GRANULARITY_TEXT_VALUE[granularities.YEAR],
            now,
            timezone='Europe/Madrid')
        self.assertEquals(start, expected_start)
        self.assertEquals(end, expected_end)


if __name__ == '__main__':
    unittest.main()
