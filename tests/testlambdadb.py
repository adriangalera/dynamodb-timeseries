# !/usr/bin/env python

"""Utils test"""

import logging
import time
import unittest

from rollup import lambda_database, granularities

logging.basicConfig(level=logging.DEBUG)


class TestLambdaDatabaseRollup(unittest.TestCase):
    """Utils Test Class"""

    def test_parse_stream(self):
        """Test that lambda can parse correctly the dynamodb stream format"""
        now = long(time.time())
        value_serie = 'test'
        value_timestamp = str(now)
        value_value = '100'
        value_dict = {
            'timeserie': {'S': value_serie},
            'time': {'S': value_timestamp},
            'value': {'N': value_value},
        }
        record_dict = {'eventName': 'INSERT', 'dynamodb': {'NewImage': value_dict}}
        insert_item = lambda_database.parse_ddb_stream_record(record_dict)

        self.assertEqual(insert_item.timestamp, value_timestamp)
        self.assertEqual(insert_item.value, value_value)
        self.assertEqual(insert_item.seriename, value_serie)

    def test_parse_query(self):
        """Test to parse the input parameters of the query function"""

        event = {}
        ex = False
        try:
            lambda_database.parse_query_item(event)
        except KeyError:
            ex = True
        self.assertTrue(ex)

        event = {'timeseries': ['abcd']}
        ex = False
        try:
            lambda_database.parse_query_item(event)
        except KeyError:
            ex = True

        self.assertTrue(ex)

        event = {'timeseries': ['abcd'], 'start': 0, 'end': 1, 'granularity': 'abcd'}
        ex = False
        try:
            lambda_database.parse_query_item(event)
        except ValueError:
            ex = True

        self.assertTrue(ex)

        event = {
            'timeseries': ['abcd'],
            'start': 0, 'end': 1,
            'granularity': granularities.SECOND
        }
        ex = False
        query_item = None
        try:
            query_item = lambda_database.parse_query_item(event)
        except ValueError:
            ex = True
        self.assertTrue(query_item)
        self.assertFalse(ex)

        self.assertEqual(query_item.timeseries, ['abcd'])
        self.assertEqual(query_item.start, 0)
        self.assertEqual(query_item.end, 1)
        self.assertEqual(query_item.granularity, granularities.SECOND)

    def test_parse_insert_item(self):
        """Testing the insert item parser"""

        event = {
            'timeserie1': [(1, 100), (2, 100)],
            'timeserie2': [(3, 100), (4, 100)],
        }
        items_expected = {
            lambda_database.InsertItem(1, 'timeserie1', 100),
            lambda_database.InsertItem(2, 'timeserie1', 100),
            lambda_database.InsertItem(3, 'timeserie2', 100),
            lambda_database.InsertItem(4, 'timeserie2', 100),
        }
        insertitems = lambda_database.parse_insert_item(event)
        self.assertEqual(4, len(insertitems))
        self.assertEqual(set(insertitems), items_expected)


if __name__ == '__main__':
    unittest.main()
