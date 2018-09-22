"""Module that performs aggregations"""
import logging
from decimal import Decimal
from granularities import convert_time, GRANULARITY_TEXT_VALUE, get_granularity_table, get_interval, \
    get_granularity_table_text
from boto3.dynamodb.conditions import Key

AGGREGATION_AVG = 'average'
AGGREGATION_SUM = 'sum'
AGGREGATION_LAST = 'last'
AGGREGATION_MAX = 'max'
AGGREGATION_MIN = 'min'
# This implementation does not take into account the zeros in the average
AGGREGATION_AVG_ZERO = 'average_zero'
AGGREGATION_ABS_MAX = 'abs_max'
AGGREGATION_ABS_MIN = 'abs_min'
# TODO: Think about this implementation, is it possible to detect the holes add it zeroes?
# AGGREGATION_MIN_ZERO = 'min_zero'
AGGREGATION_COUNT = "count"

DEFAULT_AGGREGATION = AGGREGATION_SUM

LOGGER = logging.getLogger(__name__)


class Aggregation(object):
    """Aggregation object"""

    def __init__(self, table, timeserie, item_time, value, ttl, timezone, granularity=None,
                 dynamo_cli=None):
        self.table = table
        self.timeserie = timeserie
        self.item_time = item_time
        self.value = value
        self.ttl = ttl
        self.granularity = granularity
        self.dynamo_cli = dynamo_cli
        self.old_value = None
        self.time_original = None
        self.timezone = timezone


def add_increment_ddb(aggregation):
    """Add value directly in the dynamo DB query"""

    if aggregation.old_value is not None:
        # Subtract the values and sum this difference to the result
        aggregation.value = float(aggregation.value) - float(aggregation.old_value)

    response = aggregation.table.update_item(
        Key={
            'timeserie': aggregation.timeserie,
            'time': str(aggregation.item_time),
        },
        UpdateExpression="SET #value = if_not_exists(#value, :start) + :increment, "
                         "#ttl = :ttl",
        ExpressionAttributeNames={'#value': 'value', '#ttl': 'ttl'},
        ExpressionAttributeValues={
            ':increment': Decimal(aggregation.value),
            ':start': 0,
            ':ttl': long(aggregation.ttl)
        },
        ReturnValues="UPDATED_NEW"
    )
    LOGGER.debug('Updating item %s-%s adding value %s', aggregation.timeserie,
                 aggregation.item_time, aggregation.value)
    LOGGER.debug('Response : %s', response)
    return True


def count(aggregation):
    """Add value directly in the dynamo DB query"""

    if aggregation.old_value is not None:
        # Do not count updates
        return True

    response = aggregation.table.update_item(
        Key={
            'timeserie': aggregation.timeserie,
            'time': str(aggregation.item_time),
        },
        UpdateExpression="SET #value = if_not_exists(#value, :start) + :increment, "
                         "#ttl = :ttl",
        ExpressionAttributeNames={'#value': 'value', '#ttl': 'ttl'},
        ExpressionAttributeValues={
            ':increment': Decimal(1), ':start': 0, ':ttl': long(aggregation.ttl)
        },
        ReturnValues="UPDATED_NEW"
    )
    LOGGER.debug('Updating item %s-%s adding value %s', aggregation.timeserie,
                 aggregation.item_time, aggregation.value)
    LOGGER.debug('Response : %s', response)
    return True


def set_last_value(aggregation):
    """Perform the aggregation last. The higher resolution always keep the last value
    inserted"""

    response = aggregation.table.update_item(
        Key={
            'timeserie': aggregation.timeserie,
            'time': str(aggregation.item_time),
        },
        UpdateExpression="SET #value = :cur_value, #ttl = :ttl, #last_time = :last_time",
        ConditionExpression=':last_time >= #last_time or attribute_not_exists('
                            '#last_time)',
        ExpressionAttributeNames={'#value': 'value', '#ttl': 'ttl',
                                  '#last_time': 'last_time'},
        ExpressionAttributeValues={':cur_value': Decimal(aggregation.value),
                                   ':ttl': long(aggregation.ttl),
                                   ':last_time': str(aggregation.time_original)
                                   },

        ReturnValues="UPDATED_NEW"
    )
    LOGGER.debug('Updating item %s-%s setting value %s', aggregation.timeserie,
                 aggregation.item_time, aggregation.value)
    LOGGER.debug('Response : %s', response)
    return True


def set_max_value(aggregation):
    """Updates the value only if the value is greater than the consolidated value"""
    response = aggregation.table.update_item(
        Key={
            'timeserie': aggregation.timeserie,
            'time': str(aggregation.item_time),
        },
        UpdateExpression="SET #value = :cur_value, #ttl = :ttl",
        ConditionExpression=':cur_value > #value or attribute_not_exists(#value)',
        ExpressionAttributeNames={'#value': 'value', '#ttl': 'ttl'},
        ExpressionAttributeValues={':cur_value': Decimal(aggregation.value),
                                   ':ttl': long(aggregation.ttl)},
        ReturnValues="UPDATED_NEW"
    )
    LOGGER.debug('Updating item %s-%s setting value %s', aggregation.timeserie,
                 aggregation.item_time, aggregation.value)
    LOGGER.debug('Response : %s', response)
    return True


def set_min_value(aggregation):
    """Updates the value only if the value is lower than the consolidated value"""
    response = aggregation.table.update_item(
        Key={
            'timeserie': aggregation.timeserie,
            'time': str(aggregation.item_time),
        },
        UpdateExpression="SET #value = :cur_value, #ttl = :ttl",
        ConditionExpression=':cur_value < #value or attribute_not_exists(#value)',
        ExpressionAttributeNames={'#value': 'value', '#ttl': 'ttl'},
        ExpressionAttributeValues={':cur_value': Decimal(aggregation.value),
                                   ':ttl': long(aggregation.ttl)},
        ReturnValues="UPDATED_NEW"
    )
    LOGGER.debug('Updating item %s-%s adding value %s', aggregation.timeserie,
                 aggregation.item_time, aggregation.value)
    LOGGER.debug('Response : %s', response)
    return True


def set_max_value_abs(aggregation):
    """Same as set_max_value but with absolute numbers"""

    # DynamoDB does not provide support for abs numbers, so we need to gather the data
    # for database and perform abs transformation

    response = aggregation.table.query(
        KeyConditionExpression=Key('timeserie').eq(str(aggregation.timeserie)) & Key(
            'time').eq(str(aggregation.item_time))
    )
    items = response['Items']
    if not items:
        cur_value = None
    else:
        cur_value = float(items[0]['value'])

    if cur_value:
        LOGGER.debug('New value %s vs Current value %s Result: %s', aggregation.value,
                     cur_value,
                     abs(float(aggregation.value)) > abs(float(cur_value)))

    if cur_value is None or abs(float(aggregation.value)) > abs(float(cur_value)):
        LOGGER.debug('Setting current value to %s', aggregation.value)
        response = aggregation.table.update_item(
            Key={
                'timeserie': aggregation.timeserie,
                'time': str(aggregation.item_time),
            },
            UpdateExpression="SET #value = :cur_value, #ttl = :ttl",
            ExpressionAttributeNames={'#value': 'value', '#ttl': 'ttl'},
            ExpressionAttributeValues={':cur_value': Decimal(aggregation.value),
                                       ':ttl': long(aggregation.ttl)},

            ReturnValues="UPDATED_NEW"
        )
        LOGGER.debug('Updating item %s-%s setting value %s', aggregation.timeserie,
                     aggregation.item_time, aggregation.value)
        LOGGER.debug('Response : %s', response)


def set_min_value_abs(aggregation):
    """Same as set_min_value but with absolute numbers"""

    # DynamoDB does not provide support for abs numbers, so we need to gather the data
    # for database and perform abs transformation

    response = aggregation.table.query(
        KeyConditionExpression=Key('timeserie').eq(str(aggregation.timeserie)) & Key(
            'time').eq(str(aggregation.item_time))
    )
    items = response['Items']
    if not items:
        cur_value = None
    else:
        cur_value = float(items[0]['value'])

    if cur_value:
        LOGGER.debug('New value %s vs Current value %s Result: %s', aggregation.value,
                     cur_value, abs(float(aggregation.value)) < abs(float(cur_value)))

    if cur_value is None or abs(float(aggregation.value)) < abs(float(cur_value)):
        LOGGER.debug('Setting current value to %s', aggregation.value)
        response = aggregation.table.update_item(
            Key={
                'timeserie': aggregation.timeserie,
                'time': str(aggregation.item_time),
            },
            UpdateExpression="SET #value = :cur_value, #ttl = :ttl",
            ExpressionAttributeNames={'#value': 'value', '#ttl': 'ttl'},
            ExpressionAttributeValues={':cur_value': Decimal(aggregation.value),
                                       ':ttl': long(aggregation.ttl)},

            ReturnValues="UPDATED_NEW"
        )
        LOGGER.debug('Updating item %s-%s setting value %s', aggregation.timeserie,
                     aggregation.item_time, aggregation.value)
        LOGGER.debug('Response : %s', response)


def get_data_from_table(tbl_name, aggregation, start, end):
    """Performs the query to extract the data from the given table"""
    low_gran_count = None
    low_gran_values = None
    LOGGER.debug('Querying table %s [%s,%s]', tbl_name, start, end)
    response = aggregation.dynamo_cli.Table(tbl_name).query(
        KeyConditionExpression=Key('timeserie').eq(aggregation.timeserie) & Key(
            'time').between(str(start), str(end))
    )
    low_gran_times = None
    if response:
        low_gran_count = response['Count']
        low_gran_values = [float(item['value']) for item in response['Items']]
        low_gran_times = [float(item['time']) for item in response['Items']]
    LOGGER.debug('%s Results: %s', low_gran_count, low_gran_values)
    return low_gran_count, low_gran_values, low_gran_times


def average(aggregation, discard_zeros=False):
    """Perform the average aggregation"""

    # This method take the data from the inmediate lower granularity and computes the
    # average, then it insert the new average
    try:
        # Calculate the inmediate lower granularity:
        LOGGER.debug('Requested granularity is %s', aggregation.granularity)
        gran_value = GRANULARITY_TEXT_VALUE[aggregation.granularity]
        LOGGER.debug('Converted to granularity with value %s', gran_value)
        tbl_lower_gran_name = get_granularity_table(gran_value - 1)
        LOGGER.debug('Will query table %s', tbl_lower_gran_name)

        # Need to compute the period to query
        start, end = get_interval(gran_value, aggregation.item_time, aggregation.timezone)
        LOGGER.debug('Compute period: %s %s', start, end)

    except KeyError, e:
        LOGGER.error('Exception configuring tables: %s', e)
        raise e

    low_gran_count, low_gran_values, __ = get_data_from_table(tbl_lower_gran_name,
                                                              aggregation, start, end)
    if discard_zeros:
        without_zeros = [value for value in low_gran_values if value != 0]
        low_gran_values = without_zeros
        low_gran_count = len(without_zeros)

    if low_gran_count and low_gran_values:

        LOGGER.debug('Going to perform average on %s', low_gran_values)

        # Compute the average
        avg_value = sum(low_gran_values) / float(low_gran_count)

        LOGGER.debug('Average value: %s', avg_value)

        # Set the computed average
        response = aggregation.table.update_item(
            Key={
                'timeserie': aggregation.timeserie,
                'time': str(aggregation.item_time),
            },
            UpdateExpression="SET #value = :value, #ttl = :ttl",
            ExpressionAttributeNames={'#value': 'value', '#ttl': 'ttl'},
            ExpressionAttributeValues={
                ':value': Decimal(str(avg_value)), ':ttl': long(aggregation.ttl)
            },
            ReturnValues="UPDATED_NEW"
        )
        LOGGER.debug('Updating item %s-%s adding value %s', aggregation.timeserie,
                     aggregation.item_time, avg_value)
        LOGGER.debug('Response : %s', response)
        return True

    else:
        LOGGER.debug('No data from lower granularity')


def average_without_zeroes(aggregation):
    """Perform average without zeros"""
    return average(aggregation, discard_zeros=True)


def aggregate(dynamo_cli, aggregation, granularity, item, time_converted, ts_conf,
              time_original, timezone):
    """Perform the aggregation based on the specified dictionary"""

    table = get_granularity_table_text(granularity)
    if not table:
        raise ValueError('No table associated to %s', granularity)
    agg_func = AGG_FUNC_DICT.get(aggregation, None)
    if not agg_func:
        raise ValueError('No function associated to %s', aggregation)
    ddb_table = dynamo_cli.Table(table)

    ttl = int(time_converted) + ts_conf.retentions[granularity]

    agg = Aggregation(ddb_table, item.seriename, time_converted, item.value, ttl, timezone,
                      granularity=granularity, dynamo_cli=dynamo_cli)
    agg.time_original = time_original
    if item.old_value:
        agg.old_value = item.old_value
    agg_func(agg)


# Define which function execute depending on the aggregation method
AGG_FUNC_DICT = {
    AGGREGATION_SUM: add_increment_ddb,
    AGGREGATION_LAST: set_last_value,
    AGGREGATION_MAX: set_max_value,
    AGGREGATION_MIN: set_min_value,
    AGGREGATION_ABS_MAX: set_max_value_abs,
    AGGREGATION_ABS_MIN: set_min_value_abs,
    AGGREGATION_AVG: average,
    AGGREGATION_AVG_ZERO: average_without_zeroes,
    AGGREGATION_COUNT: count
}


def rollup(dynamo_cli, granularity, insert_item, ts_conf):
    """Perform the rollup aggregation from seconds to all the available granularities"""
    try:
        aggregation = ts_conf.aggregation_method
        timezone = ts_conf.timezone
        LOGGER.debug('Rolling up %s with aggregation %s', granularity, aggregation)
        time_converted = convert_time(granularity, insert_item.timestamp, timezone)
        """
        debug = "***** %s %s %s at %s (%s)*****" % (
        insert_item.seriename, aggregation, insert_item.value, time_converted, granularity)
        print debug
        """
        aggregate(dynamo_cli, aggregation, granularity, insert_item, time_converted,
                  ts_conf, insert_item.timestamp, timezone)
    except Exception, ve:
        LOGGER.error('Aggregation failed. Reason: %s', ve)
