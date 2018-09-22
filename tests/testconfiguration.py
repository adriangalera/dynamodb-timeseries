# !/usr/bin/env python

"""Test of configuration table"""
import logging
import unittest
import os
import boto3
import json

from baselocalstack import BaseLocalStackTest
from rollup import granularities, aggregations, timeserie_configuration, constants

logging.basicConfig(level=logging.INFO)


class TestConfigurationTable(BaseLocalStackTest):
    """Test configuration table"""

    @staticmethod
    def get_local_dynamo_cli():
        return boto3.resource('dynamodb',
                              endpoint_url=os.environ[constants.DDB_LOCAL_ENV_VAR],
                              aws_access_key_id='foobar', aws_secret_access_key='foobar',
                              aws_session_token='foobar', region_name='us-west-2')

    def test_insert_without_conf(self):
        """Insert default configuration on non-existent timeserie"""
        configuration = timeserie_configuration.get_timeserie_configure(
            self.get_local_dynamo_cli(), 'test-not-exist')
        self.assertTrue(configuration.default)
        self.assertEquals(configuration.retentions, granularities.RETENTIONS_GRANULARITY)
        self.assertEquals(configuration.timezone, granularities.DEFAULT_TIMEZONE)
        self.assertEquals(configuration.aggregation_method,
                          aggregations.DEFAULT_AGGREGATION)

    def test_update_configuration(self):
        """Test for updating a configuration"""

        ts_name = 'test-update-1'
        configuration = timeserie_configuration.get_timeserie_configure(
            self.get_local_dynamo_cli(), ts_name)
        self.assertTrue(configuration.default)
        self.assertEquals(configuration.retentions, granularities.RETENTIONS_GRANULARITY)
        self.assertEquals(configuration.timezone, granularities.DEFAULT_TIMEZONE)
        self.assertEquals(configuration.aggregation_method,
                          aggregations.DEFAULT_AGGREGATION)

        custom_tz = 'America/New_York'
        custom_agg = aggregations.AGGREGATION_LAST
        custom_ret = granularities.RETENTIONS_GRANULARITY
        custom_ret[granularities.SECOND] = 3 * 365 * 12 * 30 * 24 * 60 * 60
        timeserie_configuration.update_timeserie_configuration(
            self.get_local_dynamo_cli(), ts_name, custom_tz, custom_agg, custom_ret)

        configuration = timeserie_configuration.get_timeserie_configure(
            self.get_local_dynamo_cli(), ts_name)
        self.assertFalse(configuration.default)
        self.assertEquals(configuration.retentions, custom_ret)
        self.assertEquals(configuration.timezone, custom_tz)
        self.assertEquals(configuration.aggregation_method, custom_agg)

    def test_get_all_configurations(self):
        """Test to retrieve all the configurations"""

        time_series = ['test-all-conf-1', 'test-all-conf-2', 'test-all-conf-3']
        [timeserie_configuration.get_timeserie_configure(self.get_local_dynamo_cli(),
                                                         ts) for ts in time_series]

        all_configurations = timeserie_configuration.get_all_configurations(
            self.get_local_dynamo_cli())
        self.assertEquals(3, len(all_configurations))
        self.assertTrue(all([conf.default for conf in all_configurations]))

    def test_configuration_handler(self):
        """Test configuration lambda handler"""
        time_series = ['test-handler-1', 'test-handler-1', 'test-handler-2']
        # Calling get to force the creation of the configurations
        [timeserie_configuration.get_timeserie_configure(self.get_local_dynamo_cli(),
                                                         ts) for ts in time_series]

        # Test handler to get the configuration
        event = {
            'operation': 'get',
            'payload': {
                'timeseries': ",".join(time_series)
            }
        }
        handler_get_confs = timeserie_configuration.handler(event, None)
        self.assertEquals(3, len(handler_get_confs))
        self.assertTrue(all([conf['default'] for conf in handler_get_confs]))

        # Test modify configuration via handler
        tz = "America/Adak"
        agg = 'sum'
        ret = granularities.RETENTIONS_GRANULARITY
        new_configuration = timeserie_configuration.Configuration(tz, agg, ret)
        new_configuration.timeserie = 'test-handler-1'

        event = {
            'operation': 'post',
            'payload': json.dumps(new_configuration.__dict__)
        }

        db_new_configuration = timeserie_configuration.handler(event, None)
        self.assertTrue(db_new_configuration)

        # Validate the changes in the configuration
        event = {
            'operation': 'get',
            'payload': {
                'timeseries': 'test-handler-1'
            }
        }
        db_conf = timeserie_configuration.handler(event, None)
        self.assertEquals(1, len(db_conf))
        self.assertEqual(db_conf[0]['timezone'], tz)

    def test_delete_configuration_handler(self):
        """Test configuration lambda handler"""
        time_series = ['test-handler-1', 'test-handler-1', 'test-handler-2']
        # Calling get to force the creation of the configurations
        [timeserie_configuration.get_timeserie_configure(self.get_local_dynamo_cli(), ts) for ts in time_series]

        # Test handler to get the configuration
        event = {
            'operation': 'get',
            'payload': {
                'timeseries': ",".join(time_series)
            }
        }
        handler_get_confs = timeserie_configuration.handler(event, None)
        self.assertEquals(3, len(handler_get_confs))
        self.assertTrue(all([conf['default'] for conf in handler_get_confs]))

        # Test modify configuration via handler
        tz = "America/Adak"
        agg = 'sum'
        ret = granularities.RETENTIONS_GRANULARITY
        new_configuration = timeserie_configuration.Configuration(tz, agg, ret)
        new_configuration.timeserie = 'test-handler-1'

        event = {
            'operation': 'post',
            'payload': json.dumps(new_configuration.__dict__)
        }

        db_new_configuration = timeserie_configuration.handler(event, None)
        self.assertTrue(db_new_configuration)

        # Validate the changes in the configuration
        event = {
            'operation': 'get',
            'payload': {
                'timeseries': 'test-handler-1'
            }
        }
        db_conf = timeserie_configuration.handler(event, None)
        self.assertEquals(1, len(db_conf))
        self.assertEqual(db_conf[0]['timezone'], tz)

        # Delete the configuration
        event = {
            'operation': 'delete',
            'payload': {
                'timeseries': ['test-handler-1', 'test-handler-1', 'test-handler-2']
            }
        }
        response = timeserie_configuration.handler(event, None)
        self.assertTrue(response)

        event = {
            'operation': 'get',
            'payload': {
                'timeseries': ",".join(time_series)
            }
        }
        del os.environ['ADD_DEFAULT']
        handler_get_confs = timeserie_configuration.handler(event, None)
        self.assertEquals(0, len(handler_get_confs))
        os.environ['ADD_DEFAULT'] = "true"

    def setUp(self):
        """Delete all configuration before the test"""
        table = self.get_local_dynamo_cli().Table(constants.get_configuration_table())
        response = table.scan()

        timeseries = [item['timeserie'] for item in response['Items']]

        for ts in timeseries:
            table.delete_item(Key={'timeserie': ts})


if __name__ == '__main__':
    unittest.main()
