"""Lambda related with timeserie configurations"""

import logging
import os
import boto3
import json
from boto3.dynamodb.conditions import Key

import aggregations, granularities, constants

LOGGER = logging.getLogger()
DDB = None
SECONDS_HOUR = 3600


def configure_logging():
    """Configure logging"""
    # Configure logging
    if constants.DEBUG_LOGS in os.environ:
        LOGGER.setLevel(logging.DEBUG)
    else:
        LOGGER.setLevel(logging.INFO)


def configure_dynamodb():
    """Configure DynamoDB connection"""
    global DDB
    if constants.DDB_LOCAL_ENV_VAR in os.environ:
        LOGGER.info('Connecting to local dynamo DB')
        DDB = boto3.resource('dynamodb',
                             endpoint_url=os.environ[constants.DDB_LOCAL_ENV_VAR],
                             aws_access_key_id='foobar', aws_secret_access_key='foobar',
                             aws_session_token='foobar', region_name='us-west-2')
    else:
        DDB = boto3.resource('dynamodb')


class Configuration(object):
    """Object that define the configuration parameters for a timeserie"""

    def __init__(self, timezone, aggregation_method, retentions):
        self.timezone = timezone
        self.aggregation_method = aggregation_method
        self.retentions = {}
        self.default = False
        self.timeserie = None

        for k, v in retentions.iteritems():
            self.retentions[k] = int(v)

    @classmethod
    def from_ddb(cls, item):
        """Builds a Configuration object from an entry in the database"""
        item_tz = item['timezone']
        item_agg = item['aggregation']
        item_ret = item['retentions']
        item_default = item['default']
        item_serie_name = item['timeserie']

        conf = Configuration(item_tz, item_agg, item_ret)
        conf.default = item_default
        conf.timeserie = item_serie_name
        return conf

    @classmethod
    def from_dict(cls, item):
        return Configuration.from_ddb(item)

    def to_dict(self):
        return {
            'timezone': self.timezone,
            'aggregation': self.aggregation_method,
            'retentions': self.retentions,
            'default': self.default,
            'timeserie': self.timeserie
        }


def get_timeserie_configure(dynamo_cli, timeserie_name):
    """Query the table timeserie_configuration for the timeserie, if it's not there,
    it inserts the default values"""
    table = dynamo_cli.Table(constants.get_configuration_table())
    response = table.query(KeyConditionExpression=Key('timeserie').eq(timeserie_name))
    items = response['Items']
    if items:
        configuration_item = items[0]
        return Configuration.from_ddb(configuration_item)
    else:
        if 'ADD_DEFAULT' in os.environ:
            tz = granularities.DEFAULT_TIMEZONE
            agg = aggregations.DEFAULT_AGGREGATION
            if constants.CHAR_AGG in timeserie_name:
                agg = timeserie_name.split(constants.CHAR_AGG)[-1]
            retentions = granularities.RETENTIONS_GRANULARITY
            LOGGER.info('Creating default configuration for %s ', timeserie_name)
            update_timeserie_configuration(dynamo_cli, timeserie_name, tz, agg, retentions,
                                           table=table, default=True)
            response = table.query(KeyConditionExpression=Key('timeserie').eq(timeserie_name))
            items = response['Items']
            if items:
                configuration_item = items[0]
                return Configuration.from_ddb(configuration_item)
            else:
                raise ValueError('Configuration cannot be inserted!')
        else:
            # Do not add default configuration
            return None


def update_timeserie_configuration(dynamo_cli, timeserie_name, tz, agg, retentions,
                                   table=None, default=False):
    """Updates the configuration for a timeserie"""

    if not table:
        table = dynamo_cli.Table(constants.get_configuration_table())

    configuration = {
        'timeserie': timeserie_name,
        'timezone': str(tz),
        'aggregation': str(agg),
        'retentions': retentions,
        'default': default
    }

    LOGGER.info('Setting configuration %s for %s ', configuration, timeserie_name)

    response = table.put_item(Item=configuration)
    LOGGER.debug(response)


def get_all_configurations(dynamo_cli):
    """Performs a scan over the configuration table"""
    table = dynamo_cli.Table(constants.get_configuration_table())
    response = table.scan()
    configuration_data = response['Items']

    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        configuration_data.extend(response['Items'])

    return [Configuration.from_ddb(conf) for conf in configuration_data]


def delete_configurations(dynamo_cli, timeseries):
    """Delete configurations"""
    table = dynamo_cli.Table(constants.get_configuration_table())
    LOGGER.info("Deleting configuration %s", timeseries)
    for timeserie in timeseries:
        response = table.delete_item(
            Key={
                'timeserie': timeserie
            }
        )
        LOGGER.debug(response)


def get_configuration_handler(event, __context):
    """Lambda handler to get configuration"""

    configure_logging()
    configure_dynamodb()

    timeseries = None
    configurations = []
    if 'timeseries' in event:
        timeseries = event['timeseries']
        timeseries = timeseries.split(",")

    try:
        if timeseries is not None:
            for ts in timeseries:
                conf = get_timeserie_configure(DDB, ts)
                if conf:
                    configurations.append(conf)
        else:
            configurations = get_all_configurations(DDB)
    except Exception, ex:
        LOGGER.error(ex)
        raise ex
    if configurations:
        configurations = [conf.__dict__ for conf in configurations]

    return configurations


def update_configuration_handler(event, context):
    """Lambda handler to update the configuration"""

    configure_logging()
    configure_dynamodb()

    configuration = None
    try:
        conf = json.loads(event)
        timeserie = conf['timeserie']
        aggregation = conf['aggregation_method']
        retention = conf['retentions']
        timezone = conf['timezone']

        if not retention:
            LOGGER.info('Setting default granularity')
            retention = granularities.RETENTIONS_GRANULARITY

        if aggregation not in aggregations.AGG_FUNC_DICT.keys():
            LOGGER.error('Aggregation %s not implemented', aggregation)
        else:
            update_timeserie_configuration(DDB, timeserie, timezone, aggregation,
                                           retention)
            configuration = get_timeserie_configure(DDB, timeserie)

    except (KeyError, Exception), err:
        LOGGER.error(err)
        raise err

    body_msg = None
    if configuration:
        body_msg = json.dumps(configuration.__dict__)

    return body_msg


def delete_configuration_handler(event, context):
    """Lambda handler to delete the configuration"""
    configure_logging()
    configure_dynamodb()

    try:
        # event is a list with the timeseries configuration to delete
        delete_configurations(DDB, event['timeseries'])

    except (KeyError, Exception), err:
        LOGGER.error(err)
        raise err

    body_msg = True

    return body_msg

def map_post_api_event(event):
    return event["body"]

def handler(event, __context__):
    """Timeseries configuration lambda handler"""
    # event format:
    # event {
    # 'operation' : 'get|post'
    # payload: payload
    # }
    is_api_request = False

    # The request comes from an API    
    if not 'operation' in event and 'httpMethod' in event:
        is_api_request = True
        httpMethod = event["httpMethod"].lower()
        if  httpMethod in ["post", "put"]:
            httpMethod = "post"
        event['operation'] = httpMethod
        event['payload'] = {}
    LOGGER.debug('Received event %s', event)

    if 'operation' in event:
        operation = event['operation']
        payload = event['payload']
        if operation == "get":
            response = get_configuration_handler(payload, __context__)
            if is_api_request:
                return {"statusCode": 200, "body": json.dumps(response)}
            else:
                return response

        elif operation == "post":
            if is_api_request:
                payload = map_post_api_event(event)
            response =  update_configuration_handler(payload, __context__)
            if is_api_request:
                return {"statusCode": 200, "body": response}
            else:
                return response
        elif operation == "delete":
            response = delete_configuration_handler(payload, __context__)
            if is_api_request:
                return {"statusCode": 200, "body" : json.dumps(response)}
            else:
                return response            
        else:
            raise ValueError('Invalid operation')
    else:
        raise ValueError('Invalid event format')
