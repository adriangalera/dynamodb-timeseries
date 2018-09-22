"""Test Kinesis based functionality"""
import logging
import sys
import time
import unittest

from baselocalstack import BaseLocalStackTest
from rollup import lambda_database, constants, granularities, aggregations

logging.basicConfig(level=logging.DEBUG)


class TestLambdaDatabaseQuery(BaseLocalStackTest):

    def test_kinesis_consumer(self):
        """Test the values are correctly inserted in the DynamoDB database via the Kinesis consumer app"""

        ts1 = 'timeseriexxx1' + constants.CHAR_AGG + aggregations.AGGREGATION_SUM
        ts2 = 'timeseriexxx2' + constants.CHAR_AGG + aggregations.AGGREGATION_SUM

        # 1513581045 => 2017-12-18 08:10:45
        # 1513628120 => 2017-12-18 21:15:20

        ts_data = {
            ts1: [(1513581045, 100), (1513628120, 100)],
            ts2: [(1513581045, 100), (1513628120, 100)],
        }

        lambda_database.put_items(ts_data, None)

        time.sleep(1)

        # Check if the data is there
        start_granularity = granularities.GRANULARITIES[0]

        event = {
            'timeseries': [ts1, ts2],
            'start': 1413580300,
            'end': 1613628200,
            'granularity': start_granularity
        }

        # Since this is executed outside the lambda env, we must configure dynamodb
        # manually

        lambda_database.configure_dynamodb()
        query_response = lambda_database.query(event, None)
        self.assertEqual(ts_data, query_response)

        # Give time to perform the aggregations and close the reader
        time.sleep(5)

        # Check aggregations

        expected_granularities = {
            granularities.MINUTE: {
                ts1: [(1513581000, 100), (1513628100, 100)],
                ts2: [(1513581000, 100), (1513628100, 100)]
            },
            granularities.HOUR: {
                ts1: [(1513580400, 100), (1513627200, 100)],
                ts2: [(1513580400, 100), (1513627200, 100)]
            },
            granularities.DAY: {
                ts1: [(1513551600, 200)],
                ts2: [(1513551600, 200)]
            },
            granularities.MONTH: {
                ts1: [(1512082800, 200)],
                ts2: [(1512082800, 200)]
            },
            granularities.YEAR: {
                ts1: [(1483225200, 200)],
                ts2: [(1483225200, 200)]
            },
        }

        lambda_database.configure_dynamodb()

        for granularity in granularities.GRANULARITIES[1:]:
            event = {
                'timeseries': [ts1, ts2],
                'start': -sys.maxint,
                'end': sys.maxint,
                'granularity': granularity
            }
            expected = expected_granularities[granularity]
            query_response = lambda_database.query(event, None)
            self.assertTrue(expected, query_response)


if __name__ == '__main__':
    unittest.main()
