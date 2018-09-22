# !/usr/bin/env python

"""Utils test"""

import logging
import time
import unittest

import boto3

from baselocalstack import BaseLocalStackTest
from rollup import lambda_database, constants, granularities

logging.basicConfig(level=logging.INFO)


class TestLambdaDatabaseQuery(BaseLocalStackTest):
    """Utils Test Class"""

    @staticmethod
    def item_to_dynamo_db_item(item):
        """Convert each item into DynamoDB format"""
        now = long(time.time())
        return {
            'timeserie': {'S': item['timeserie']},
            'time': {'S': str(item['time'])},
            'value': {'N': str(item['value'])},
            'ttl': {'N': str(now + (1 * 60))},
        }

    def test_query(self):
        """Test real query, in order to do not depend on the implementation,
        use dynamodb cli to insert values"""

        size = 10

        start = (long(time.time()) / 60) * 60
        end = start + size
        times = range(start, end)
        values1 = [1] * size
        values2 = [2] * size

        curr = start
        items = []
        timeserie1 = 'test-serie-1'
        timeserie2 = 'test-serie-2'
        for index in range(size):
            items.append({
                'timeserie': timeserie1,
                'time': curr,
                'value': values1[index]
            })
            items.append({
                'timeserie': timeserie2,
                'time': curr,
                'value': values2[index]
            })
            curr += 1

        client = boto3.client('dynamodb', endpoint_url=self.DYNAMODB_ENDPOINT)
        for item in items:
            response = client.put_item(
                TableName=granularities.get_granularity_table_text(granularities.SECOND),
                Item=self.item_to_dynamo_db_item(item)
            )
            logging.debug(response)
            time.sleep(0.5)

        event = {
            'timeseries': [timeserie1, timeserie2],
            'start': start,
            'end': end,
            'granularity': granularities.SECOND
        }
        # Since this is executed outside the lambda env, we must configure dynamodb
        # manually

        lambda_database.configure_dynamodb()
        query_response = lambda_database.query(event, None)

        self.assertEqual(query_response.get(timeserie1), zip(times, values1))
        self.assertEqual(query_response.get(timeserie2), zip(times, values2))

    def test_lambda_handler(self):
        """Test lambda handler"""

        event_put = {
            'operation': 'post',
            'payload': {
                'timeseriex': [(1, 100), (2, 100)],
                'timeseriey': [(3, 100), (4, 100)],
            }
        }

        lambda_database.handler(event_put, None)
        get_payload = {
            'timeseries': ['timeseriex'],
            'start': 1,
            'end': 2,
            'granularity': granularities.SECOND
        }

        # Give some time, so message can arrive to the consumer
        time.sleep(0.5)

        event_get = {
            'operation': 'get',
            'payload': get_payload
        }

        data = lambda_database.handler(event_get, None)
        self.assertEqual(data['timeseriex'], event_put['payload']['timeseriex'])

    def test_last_values(self):
        """Test obtaining the last values"""
        event_put = {
            'operation': 'post',
            'payload': {
                'timeseriex': [(1, 100), (2, 100)],
                'timeseriey': [(3, 100), (4, 100)],
            }
        }

        lambda_database.handler(event_put, None)
        last_payload = {
            'timeseries': ['timeseriex'],
            'granularity': granularities.SECOND
        }

        # Give some time, so message can arrive to the consumer
        time.sleep(0.5)

        event_last = {
            'operation': 'last',
            'payload': last_payload
        }

        data = lambda_database.handler(event_last, None)
        self.assertEqual(data['timeseriex'][0], event_put['payload']['timeseriex'][-1])


if __name__ == '__main__':
    unittest.main()
