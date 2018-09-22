# !/usr/bin/env python

"""Integration test of lambda, dynamodb and dynamodb streams"""
import json
import logging
import time
import unittest
import random

import boto3
from boto3.dynamodb.conditions import Key

from baselocalstack import BaseLocalStackTest
from rollup import constants, granularities, aggregations

logging.basicConfig(level=logging.DEBUG)


class TestAggregation(BaseLocalStackTest):
    """Integration test of Lambda, dynamodb and dynamodb streams using multiple
    aggregation methods"""

    def generic_test(self, input_data, start, end, expected_seconds_data,
                     expected_minute_data, time_wait=15):
        """Generic test"""

        client = boto3.client('lambda', endpoint_url=self.LAMBDA_ENDPOINT)

        # Test insert and rollup aggregations
        response = client.invoke(
            FunctionName=self.LAMBDA_FUNCTION_PUT,
            InvocationType='Event',
            Payload=json.dumps(input_data)
        )

        logging.debug(response)

        # Sleep a little time to make sure the values are inserted
        time.sleep(time_wait)

        event_seconds = {
            'timeseries': input_data.keys(),
            'start': start,
            'end': end,
            'granularity': granularities.SECOND
        }

        # Test querying different granularities

        response = client.invoke(
            FunctionName=self.LAMBDA_FUNCTION_GET,
            InvocationType='RequestResponse',
            Payload=json.dumps(event_seconds)
        )
        logging.debug(response)

        # Since JSON does not support tuples (use lists instead) and zip function
        # returns tuples, we need to manually construct a list of list instead of a
        # list of tuples to compare with the results

        returned_data = json.loads(response['Payload'].read())

        self.assertDictEqual(expected_seconds_data, returned_data)

        # Testing rollup aggregation to minutes

        event_minute = {
            'timeseries': input_data.keys(),
            'start': start,
            'end': start + 1,
            'granularity': granularities.MINUTE
        }

        # Sleep a little time to make sure the rollup aggregations are done
        # time.sleep(time_wait)

        response = client.invoke(
            FunctionName=self.LAMBDA_FUNCTION_GET,
            InvocationType='RequestResponse',
            Payload=json.dumps(event_minute)
        )
        logging.debug(response)

        returned_data = json.loads(response['Payload'].read())

        self.assertDictEqual(expected_minute_data, returned_data)

    def test_lambdas_sum(self):
        """Test the basic usage using lambdas"""

        size = 10

        start = (long(time.time()) / 60) * 60
        end = start + size
        times = range(start, end)
        values1 = [1] * size
        values2 = [2] * size

        timeserie1 = 'time-serie-test-1' + constants.CHAR_AGG + "sum"
        timeserie2 = 'time-serie-test-2' + constants.CHAR_AGG + "sum"

        event = {
            timeserie1: zip(times, values1),
            timeserie2: zip(times, values2)
        }

        # Since JSON does not support tuples (use lists instead) and zip function
        # returns tuples, we need to manually construct a list of list instead of a
        # list of tuples to compare with the results

        expected_data = {
            timeserie1: [[times[cur], float(values1[cur])] for cur in range(size)],
            timeserie2: [[times[cur], float(values2[cur])] for cur in range(size)]
        }

        expected_data_minutes = {
            timeserie1: [[start, float(1 * size)]],
            timeserie2: [[start, float(2 * size)]]
        }

        self.generic_test(event, start, end, expected_data, expected_data_minutes)

    def test_lambdas_last(self):
        """Test last aggregation method"""

        size = 10

        start = (long(time.time()) / 60) * 60
        end = start + size
        times = range(start, end)
        values1 = range(size)
        values2 = map(lambda x: x * 2, range(size))

        timeserie1 = 'timeserie-1' + constants.CHAR_AGG + 'last'
        timeserie2 = 'timeserie-2' + constants.CHAR_AGG + 'last'

        event = {
            timeserie1: zip(times, values1),
            timeserie2: zip(times, values2)
        }

        expected_data = {
            timeserie1: [[times[cur], float(values1[cur])] for cur in range(size)],
            timeserie2: [[times[cur], float(values2[cur])] for cur in range(size)]
        }

        expected_data_minutes = {
            timeserie1: [[start, float(values1[-1])]],
            timeserie2: [[start, float(values2[-1])]]
        }

        self.generic_test(event, start, end, expected_data, expected_data_minutes)

    def test_lambdas_max(self):
        """Test max aggregation method"""

        size = 10
        start = (long(time.time()) / 60) * 60
        end = start + size
        times = range(start, end)
        values1 = map(lambda x: x * 3, range(size))
        values2 = map(lambda x: x * 4, range(size))

        timeserie1 = 'timeserie-1' + constants.CHAR_AGG + aggregations.AGGREGATION_MAX
        timeserie2 = 'timeserie-2' + constants.CHAR_AGG + aggregations.AGGREGATION_MAX

        expected_data = {
            timeserie1: [[times[cur], float(values1[cur])] for cur in range(size)],
            timeserie2: [[times[cur], float(values2[cur])] for cur in range(size)]
        }

        expected_data_minutes = {
            timeserie1: [[start, float(max(values1))]],
            timeserie2: [[start, float(max(values2))]]
        }

        event = {
            timeserie1: zip(times, values1),
            timeserie2: zip(times, values2)
        }

        self.generic_test(event, start, end, expected_data, expected_data_minutes)

    def test_lambdas_min(self):
        """Test min aggregation method"""

        size = 10
        start = (long(time.time()) / 60) * 60
        end = start + size
        times = range(start, end)
        values1 = random.sample(xrange(100), size)
        values2 = random.sample(xrange(100), size)

        timeserie1 = 'timeserie-1' + constants.CHAR_AGG + aggregations.AGGREGATION_MIN
        timeserie2 = 'timeserie-2' + constants.CHAR_AGG + aggregations.AGGREGATION_MIN

        expected_data = {
            timeserie1: [[times[cur], float(values1[cur])] for cur in range(size)],
            timeserie2: [[times[cur], float(values2[cur])] for cur in range(size)]
        }

        expected_data_minutes = {
            timeserie1: [[start, float(min(values1))]],
            timeserie2: [[start, float(min(values2))]]
        }

        event = {
            timeserie1: zip(times, values1),
            timeserie2: zip(times, values2)
        }

        self.generic_test(event, start, end, expected_data, expected_data_minutes)

    def test_lambdas_max_abs(self):
        """Test max abs aggregation method"""

        size = 10
        start = (long(time.time()) / 60) * 60
        end = start + size
        times = range(start, end)
        values1 = random.sample(range(-100, 100), size)
        values2 = random.sample(range(-100, 100), size)

        timeserie1 = 'timeserie-1' + constants.CHAR_AGG + aggregations.AGGREGATION_ABS_MAX
        timeserie2 = 'timeserie-2' + constants.CHAR_AGG + aggregations.AGGREGATION_ABS_MAX

        expected_data = {
            timeserie1: [[times[cur], float(values1[cur])] for cur in range(size)],
            timeserie2: [[times[cur], float(values2[cur])] for cur in range(size)]
        }

        expected_data_minutes = {
            timeserie1: [[start, float(max(values1, key=abs))]],
            timeserie2: [[start, float(max(values2, key=abs))]]
        }

        event = {
            timeserie1: zip(times, values1),
            timeserie2: zip(times, values2)
        }

        self.generic_test(event, start, end, expected_data, expected_data_minutes)

        start = (long(time.time()) / 60) * 60
        end = start + size
        times = range(start, end)

        values3 = [-55, -75, -77, -72, -40, -20, -26, -35, 59, -34]
        timeserie3 = 'timeserie-3' + constants.CHAR_AGG + aggregations.AGGREGATION_ABS_MAX

        expected_data = {
            timeserie3: [[times[cur], float(values3[cur])] for cur in range(size)],
        }

        expected_data_minutes = {
            timeserie3: [[start, float(max(values3, key=abs))]],
        }

        event = {
            timeserie3: zip(times, values3),
        }

        self.generic_test(event, start, end, expected_data, expected_data_minutes)

    def test_lambdas_min_abs(self):
        """Test min abs aggregation method"""

        size = 10
        start = (long(time.time()) / 60) * 60
        end = start + size
        times = range(start, end)
        values1 = random.sample(range(-100, 100), size)
        values2 = random.sample(range(-100, 100), size)

        timeserie1 = 'timeserie-1' + constants.CHAR_AGG + aggregations.AGGREGATION_ABS_MIN
        timeserie2 = 'timeserie-2' + constants.CHAR_AGG + aggregations.AGGREGATION_ABS_MIN

        expected_data = {
            timeserie1: [[times[cur], float(values1[cur])] for cur in range(size)],
            timeserie2: [[times[cur], float(values2[cur])] for cur in range(size)]
        }

        expected_data_minutes = {
            timeserie1: [[start, float(min(values1, key=abs))]],
            timeserie2: [[start, float(min(values2, key=abs))]]
        }

        event = {
            timeserie1: zip(times, values1),
            timeserie2: zip(times, values2)
        }

        self.generic_test(event, start, end, expected_data, expected_data_minutes)

        start = (long(time.time()) / 60) * 60
        end = start + size
        times = range(start, end)

        values3 = [-55, -75, -77, -72, -40, -20, -26, -35, 59, -34]
        timeserie3 = 'timeserie-3' + constants.CHAR_AGG + aggregations.AGGREGATION_ABS_MIN

        expected_data = {
            timeserie3: [[times[cur], float(values3[cur])] for cur in range(size)],
        }

        expected_data_minutes = {
            timeserie3: [[start, float(min(values3, key=abs))]],
        }

        event = {
            timeserie3: zip(times, values3),
        }

        self.generic_test(event, start, end, expected_data, expected_data_minutes)

    def test_lambdas_average(self):
        """Perform the average testing"""

        size = 10
        start = (long(time.time()) / 60) * 60
        end = start + size
        times = range(start, end)

        values1 = random.sample(range(-100, 100), size)
        values2 = random.sample(range(-100, 100), size)

        def compute_avg(values):
            """Compute the average"""
            return sum(values) / float(len(values))

        timeserie1 = 'timeserie-1' + constants.CHAR_AGG + aggregations.AGGREGATION_AVG
        timeserie2 = 'timeserie-2' + constants.CHAR_AGG + aggregations.AGGREGATION_AVG

        expected_data = {
            timeserie1: [[times[cur], float(values1[cur])] for cur in range(size)],
            timeserie2: [[times[cur], float(values2[cur])] for cur in range(size)]
        }

        expected_data_minutes = {
            timeserie1: [[start, compute_avg(values1)]],
            timeserie2: [[start, compute_avg(values2)]]
        }

        event = {
            timeserie1: zip(times, values1),
            timeserie2: zip(times, values2)
        }

        self.generic_test(event, start, end, expected_data, expected_data_minutes)

    def test_lambdas_average_zeros(self):
        """Perform the average without zeros testing"""

        size = 6
        start = (long(time.time()) / 60) * 60
        end = start + size
        times = range(start, end)

        values1 = [0, 100, 20, 30, 0, 10]

        def compute_avg(values):
            """Compute the average"""
            values = [value for value in values if value != 0]
            return sum(values) / float(len(values))

        timeserie1 = 'timeserie-1' + constants.CHAR_AGG + aggregations.AGGREGATION_AVG_ZERO

        expected_data = {
            timeserie1: [[times[cur], float(values1[cur])] for cur in range(size)]
        }

        expected_data_minutes = {
            timeserie1: [[start, compute_avg(values1)]]
        }

        event = {
            timeserie1: zip(times, values1),
        }

        self.generic_test(event, start, end, expected_data, expected_data_minutes)

    def test_lambdas_average_zeros_all_zeroes(self):
        """Perform the average without zeros testing"""

        size = 6
        start = (long(time.time()) / 60) * 60
        end = start + size
        times = range(start, end)

        values1 = [0, 0, 0, 0, 0, 0]

        timeserie1 = 'timeserie-allzeros' + constants.CHAR_AGG + aggregations.AGGREGATION_AVG_ZERO

        expected_data = {
            timeserie1: [[times[cur], float(values1[cur])] for cur in range(size)]
        }

        expected_data_minutes = {
            timeserie1: []
        }

        event = {
            timeserie1: zip(times, values1),
        }

        self.generic_test(event, start, end, expected_data, expected_data_minutes)

    def test_count(self):
        """Perform the count aggregation"""

        size = 10
        start = (long(time.time()) / 60) * 60
        end = start + size
        times = range(start, end)

        values1 = random.sample(range(-100, 100), size)
        values2 = random.sample(range(-100, 100), size)

        timeserie1 = 'timeserie-1' + constants.CHAR_AGG + aggregations.AGGREGATION_COUNT
        timeserie2 = 'timeserie-2' + constants.CHAR_AGG + aggregations.AGGREGATION_COUNT

        expected_data = {
            timeserie1: [[times[cur], float(values1[cur])] for cur in range(size)],
            timeserie2: [[times[cur], float(values2[cur])] for cur in range(size)]
        }

        expected_data_minutes = {
            timeserie1: [[start, size]],
            timeserie2: [[start, size]]
        }

        event = {
            timeserie1: zip(times, values1),
            timeserie2: zip(times, values2)
        }

        self.generic_test(event, start, end, expected_data, expected_data_minutes)

    def test_invalid_values(self):
        """Test passing invalid values to the aggregations module"""
        ex = False
        try:
            aggregations.aggregate(None, 'abcd', granularities.MINUTE, 'abcd', 0, 0, 0, None)
        except ValueError:
            ex = True
        self.assertTrue(ex)

        ex = False
        try:
            aggregations.aggregate(None, aggregations.AGGREGATION_SUM, 'abcd', 'abcd', 0, 0, 0, None)
        except ValueError:
            ex = True
        self.assertTrue(ex)


if __name__ == '__main__':
    unittest.main()
