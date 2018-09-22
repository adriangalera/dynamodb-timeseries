# !/usr/bin/env python

"""Integration test of lambda, dynamodb and dynamodb streams"""
import json
import logging
import unittest
import time

import boto3
from boto3.dynamodb.conditions import Key

from baselocalstack import BaseLocalStackTest
from rollup import constants, granularities, aggregations

logging.basicConfig(level=logging.DEBUG)


class TestMultipleGranularitiesTTL(BaseLocalStackTest):
    """Integration test of Lambda, dynamodb and dynamodb streams using multiple
    granularities"""

    seriename = 'test' + constants.CHAR_AGG + aggregations.AGGREGATION_SUM

    @staticmethod
    def compute_start_end(time1, time3, granularity):
        """Compute the start and end period"""
        start = time1

        if granularity == granularities.MINUTE:
            start = start - 60
        elif granularity == granularities.HOUR:
            start = start - 3600
        elif granularity == granularities.DAY:
            start = start - (3600 * 24)
        elif granularity == granularities.MONTH:
            start = start - (3600 * 24 * 35)
        elif granularity == granularities.YEAR:
            start = start - (3600 * 24 * 400)

        end = time3
        end = end + 1

        return start, end

    def generic_test(self, time1, time2, time3, granularity):
        """Generic test"""
        value = 1

        input_data = {
            self.seriename: [(time1, value), (time2, value), (time3, value)],
        }

        start, end = self.compute_start_end(time1, time3, granularity)

        client = boto3.client('lambda', endpoint_url=self.LAMBDA_ENDPOINT)

        # Test insert and rollup aggregations
        response = client.invoke(
            FunctionName=self.LAMBDA_FUNCTION_PUT,
            InvocationType='Event',
            Payload=json.dumps(input_data)
        )

        logging.debug(response)
        # Give some time, so that the reader can receive the message
        time.sleep(10)

        event_granularity = {
            'timeseries': input_data.keys(),
            'start': start,
            'end': end,
            'granularity': granularity
        }

        response = client.invoke(
            FunctionName=self.LAMBDA_FUNCTION_GET,
            InvocationType='RequestResponse',
            Payload=json.dumps(event_granularity)
        )
        logging.debug(response)

        return json.loads(response['Payload'].read())

    def assert_ttl(self, time1, time3, granularity):
        """Assert TTL"""
        dynamodb = boto3.resource('dynamodb', endpoint_url=self.DYNAMODB_ENDPOINT)
        table = dynamodb.Table(granularities.get_granularity_table_text(granularity))

        start, end = self.compute_start_end(time1, time3, granularity)

        response = table.query(
            KeyConditionExpression=Key('timeserie').eq(self.seriename) & Key(
                'time').between(str(start), str(end))
        )

        items = response['Items']
        for item in items:
            real_ttl = int(item["ttl"]) - int(item["time"])
            expected_ttl = granularities.RETENTIONS_GRANULARITY[granularity]
            self.assertEquals(real_ttl, expected_ttl)

    def test_second_hour(self):
        """Test second to hour aggregation"""
        # write two values on the same hour and one value on other hour to check the
        # aggregation
        time1 = 1513616400
        time2 = 1513616460
        time3 = 1513620000

        expected_data = [[1513616400, 2], [1513620000, 1]]

        data = self.generic_test(time1, time2, time3, granularities.HOUR)
        self.assertEquals(data[self.seriename], expected_data)

        self.assert_ttl(time1, time3, granularities.HOUR)

    def test_second_day(self):
        """Test second to day aggregation"""
        # write two values on the same day and one value on other day to check the
        # aggregation
        time1 = 1513580400
        time2 = 1513627200
        time3 = 1514182366

        expected_data = [[1513551600, 2], [1514156400, 1]]

        data = self.generic_test(time1, time2, time3, granularities.DAY)
        self.assertEquals(data[self.seriename], expected_data)

        self.assert_ttl(time1, time3, granularities.DAY)

    def test_second_month(self):
        """Test second to month aggregation"""
        # write two values on the same month and one value on other month to check the
        # aggregation
        time1 = 1507173154
        time2 = 1508605954
        time3 = 1509861492

        expected_data = [[1506808800, 2], [1509490800, 1]]

        data = self.generic_test(time1, time2, time3, granularities.MONTH)
        self.assertEquals(data[self.seriename], expected_data)

        self.assert_ttl(time1, time3, granularities.MONTH)

    def test_second_year(self):
        """Test second to year aggregation"""
        # write two values on the same year and one value on other year to check the
        # aggregation
        time1 = 1415586314
        time2 = 1418178314
        time3 = 1444440314

        expected_data = [[1388530800, 2], [1420066800, 1]]

        data = self.generic_test(time1, time2, time3, granularities.YEAR)
        self.assertEquals(data[self.seriename], expected_data)

        self.assert_ttl(time1, time3, granularities.YEAR)


if __name__ == '__main__':
    unittest.main()
