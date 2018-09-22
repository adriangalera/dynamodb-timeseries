"""Lambda to rollup"""
import logging
import os
from decimal import Decimal
import json
import time

import boto3
from boto3.dynamodb.conditions import Key

import aggregations
import constants
import granularities
import timeserie_configuration

LOGGER = logging.getLogger(__name__)
DDB = None
KIN = None
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
    return DDB


def configure_kinesis():
    """Configure kinesis connection"""
    global KIN
    if constants.KIN_LOCAL_ENV_VAR in os.environ:
        LOGGER.info('Connecting to local kinesis')
        KIN = boto3.client('kinesis',
                           endpoint_url=os.environ[constants.KIN_LOCAL_ENV_VAR],
                           aws_access_key_id='foobar', aws_secret_access_key='foobar',
                           aws_session_token='foobar', region_name='us-west-2')
    else:
        KIN = boto3.client('kinesis')
    return KIN


class InsertItem(object):
    """Class that define an inserted item"""

    def __init__(self, timestamp, seriename, value):
        self.timestamp = timestamp
        self.seriename = seriename
        self.value = value
        self.old_value = None
        self.ttl = None

    def __str__(self):
        return " ".join((self.seriename, str(self.timestamp), str(self.value)))

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return (self.timestamp, self.seriename, self.value) == \
               (other.timestamp, other.seriename, other.value)

    def __hash__(self):
        return hash((self.timestamp, self.seriename, self.value))

    def to_dynamo_db(self):
        """Convert this object to a dict to be able to store it in dynamoDB"""
        return {
            'timeserie': self.seriename,
            'time': str(self.timestamp),
            'value': Decimal(str(self.value)),
            'ttl': str(self.ttl)
        }

    def to_dict(self):
        return {
            'timeserie': self.seriename,
            'time': self.timestamp,
            'value': self.value,
            'ttl': self.ttl,
            'old_value': self.old_value
        }

    @classmethod
    def from_dict(cls, dict_data):
        timeserie = dict_data['timeserie']
        timestamp = dict_data['time']
        value = dict_data['value']
        ttl = dict_data['ttl']
        old_value = dict_data['old_value']
        item = InsertItem(timestamp, timeserie, value)
        item.ttl = ttl
        item.old_value = old_value
        return item


class QueryItem(object):
    """Class that define a query object"""

    def __init__(self, timeseries, start, end, granularity):
        self.timeseries = timeseries
        self.start = start
        self.end = end
        self.granularity = granularity
        self.last = None

    def __str__(self):
        return " ".join((str(self.timeseries), str(self.start), str(self.end), self.granularity))

    def __repr__(self):
        return self.__str__()


def dynamo_db_query(query_item):
    """Performs the query to DynamoDB"""

    LOGGER.info("Querying ... %s", query_item)

    table = DDB.Table(granularities.get_granularity_table_text(query_item.granularity))

    data = {}

    last_query = query_item.last

    # timeseries has to be a list
    for timeserie in query_item.timeseries:

        if not last_query:
            # Request timed values
            response = table.query(
                KeyConditionExpression=Key('timeserie').eq(timeserie) & Key('time').between(
                    str(query_item.start), str(query_item.end))
            )
        else:
            # Request last values
            response = table.query(KeyConditionExpression=Key('timeserie').eq(timeserie),
                                   Limit=1, ScanIndexForward=False)

        LOGGER.debug('Response has %d items', response['Count'])
        items = response['Items']
        if items:
            for item in items:
                timeserie = item['timeserie']
                item_time = long(item['time'])
                item_value = float(item['value'])

                item_tuple = (item_time, item_value)

                if timeserie in data:
                    data[timeserie].append(item_tuple)
                else:
                    item_data = [item_tuple]
                    data[timeserie] = item_data
        else:
            data[timeserie] = []

    return data


def dynamo_db_insert(insert_items):
    """Insert items in dynamo DB"""
    start_granularity = granularities.GRANULARITIES[0]
    table = granularities.get_granularity_table_text(start_granularity)

    # Enable batch put item to enhance the speed
    items = []

    for item in insert_items:
        LOGGER.debug('Insert item %s', item)

        configuration = timeserie_configuration.get_timeserie_configure(DDB,
                                                                        item.seriename)

        cur_tz = configuration.timezone
        item.timestamp = granularities.convert_time(start_granularity, item.timestamp,
                                                    cur_tz)
        item.ttl = item.timestamp + configuration.retentions[start_granularity]
        items.append(item)

    max_batch = 25
    # Group the requests in groups of 25 (max batch)
    grouped = list(zip(*[iter(items)] * max_batch))
    for group in grouped:
        LOGGER.debug("Saving batch ...")
        process_write_batch(table, group)
    LOGGER.debug("Saving the items that cannot be batched")
    outside_start = len(grouped) * max_batch
    process_write_batch(table, items[outside_start:])


def insert_stream(kinesis_records):
    """Insert the prepared records in the kinesis stream"""
    if kinesis_records:
        LOGGER.debug('Insert items %s on kinesis stream %s', kinesis_records, constants.get_kinesis_stream())
        put_record_result = KIN.put_records(StreamName=constants.get_kinesis_stream(), Records=kinesis_records)
        LOGGER.debug('Kinesis response: %s', put_record_result)
        # We are forced to wait between insertions
        time.sleep(0.01)


def kinesis_insert(insert_items):
    """Insert items on a Kinesis Queue to be later consumed and inserted in DynamoDB"""

    # Insert the data in the first available granularity
    granularity = granularities.GRANULARITIES[0]

    # Enable batch put item to enhance the speed
    items = []

    # Only get configuration once per serie. This will decrease a lot the number of reads for configuration
    series_configuration = {}
    for item in insert_items:
        if item.seriename not in series_configuration:
            configuration = timeserie_configuration.get_timeserie_configure(DDB, item.seriename)
            series_configuration[item.seriename] = configuration

    for item in insert_items:
        configuration = series_configuration.get(item.seriename)
        cur_tz = configuration.timezone
        item.timestamp = granularities.convert_time(granularity, item.timestamp,
                                                    cur_tz)
        item.ttl = item.timestamp + configuration.retentions[granularity]
        LOGGER.debug('Insert item %s', item)
        items.append(item)

    # The kinesis stream is partitioned in shards by table; so pass the value of the table as the partition key
    kinesis_records = []
    i = 0
    for item in items:
        data = json.dumps({'granularity': granularity, 'data': item.to_dict()})
        record = {'Data': data, 'PartitionKey': str(hash(granularity))}
        kinesis_records.append(record)
        i += 1
        if i % constants.BATCH_SIZE == 0:
            insert_stream(kinesis_records)
            kinesis_records = []

    if len(kinesis_records) <= constants.BATCH_SIZE:
        insert_stream(kinesis_records)


def process_write_batch(table, items):
    """Process a write batch retrying until all items are processed"""
    items_db = []

    for item in items:
        dyn_batch_item = {'PutRequest': {'Item': item.to_dynamo_db()}}
        items_db.append(dyn_batch_item)

    if items_db:
        request_items = {table: items_db}
        response = DDB.batch_write_item(RequestItems=request_items)
        LOGGER.debug(response)
        while response['UnprocessedItems']:
            response = DDB.batch_write_item(RequestItems=response['UnprocessedItems'])
            LOGGER.debug(response)


def parse_ddb_stream_record(record):
    """Parse insert record to get serie name, time and value"""
    try:
        dynamoobj = record['dynamodb']['NewImage']
        LOGGER.debug('Record %s', dynamoobj)
        seriename = dynamoobj['timeserie']['S']
        item_time = dynamoobj['time']['S']
        value = dynamoobj['value']['N']
        item = InsertItem(item_time, seriename, value)

        # In case of MODIFY, get old value
        if 'OldImage' in record['dynamodb']:
            item.old_value = record['dynamodb']['OldImage']['value']['N']

        return item
    except KeyError, err:
        LOGGER.error(err)
        return None


def parse_insert_item(event):
    """Parse the input for inserting items"""
    # Need to perform Float -> Decimal conversion to work with dynamoDB
    insertitems = []
    for timeserie, timeserie_tuples in event.iteritems():
        for timeserie_tuple in timeserie_tuples:
            insertitems.append(
                InsertItem(timeserie_tuple[0], timeserie, timeserie_tuple[1])
            )
    return insertitems


def parse_query_item(event, mandatory_time=True):
    """Parses event to generate a QueryItem"""
    if mandatory_time:
        mandatory_fields = ['timeseries', 'start', 'end', 'granularity']
    else:
        mandatory_fields = ['timeseries', 'granularity']
    if all([event_key in event for event_key in
            mandatory_fields]):
        timeseries = event['timeseries']
        start = None
        end = None
        if mandatory_time:
            start = event['start']
            end = event['end']
        granularity = event['granularity']

        if granularity not in granularities.GRANULARITIES:
            raise ValueError("Invalid granularity")

        return QueryItem(timeseries, start, end, granularity)
    else:
        LOGGER.error("Mandatory fields not present")
        raise KeyError('Missing mandatory fields: ' + ",".join(mandatory_fields))


def process_stream_event(event, __context):
    """Process a DynamoDB event to rollup the granularities"""

    configure_logging()
    configure_dynamodb()
    configure_kinesis()

    insert_items = []

    if 'Records' in event:

        LOGGER.info('Batch of %d records', len(event['Records']))

        for record in event['Records']:
            try:
                event_name = record['eventName']

                if event_name in ['INSERT', 'MODIFY']:
                    LOGGER.debug('Processing record %s', record)
                    insert_item = parse_ddb_stream_record(record)
                    if insert_item:
                        insert_items.append(insert_item)
                    else:
                        LOGGER.error('Cannot perform rollup aggregations')
                else:
                    LOGGER.debug('Ignoring record %s', event_name)
            except Exception, e:
                LOGGER.error('Exception raised while processing records from DynamoDB')
                LOGGER.error(e)

    kinesis_records = []
    i = 0
    series_configuration = {}
    for insert_item in insert_items:
        if insert_item.seriename not in series_configuration:
            ts_conf = timeserie_configuration.get_timeserie_configure(DDB, insert_item.seriename)
            series_configuration[insert_item.seriename] = ts_conf

    for insert_item in insert_items:
        item_conf = series_configuration[insert_item.seriename]
        if constants.AGG_IN_SERIE in os.environ:
            try:
                agg = insert_item.seriename.split(constants.CHAR_AGG)[1]
                item_conf.aggregation_method = agg
            except IndexError:
                pass

        for granularity in granularities.GRANULARITIES[1:]:
            # Delegate the aggregation on the kinesis consumer instead of
            # performing it here
            data = {'granularity': granularity,
                    'data': insert_item.to_dict(),
                    'aggregation': item_conf.to_dict()
                    }
            data = json.dumps(data)
            record = {'Data': data, 'PartitionKey': str(hash(granularity))}
            kinesis_records.append(record)
            # Write to kinesis on batches
            i += 1
            if i % constants.BATCH_SIZE == 0:
                insert_stream(kinesis_records)
                kinesis_records = []
    # Just in the case some batch is not full
    if len(kinesis_records) <= constants.BATCH_SIZE:
        insert_stream(kinesis_records)


def last(event, __context__):
    """Query last data for the DynamoDB timeseries database"""
    # Expected event format:
    # event = {
    #        'timeseries': [timeserie1, timeserie2],
    #        'granularity': constants.SECOND
    # }
    #

    configure_logging()
    configure_dynamodb()

    try:
        query_item = parse_query_item(event, mandatory_time=False)
        query_item.last = True
        return dynamo_db_query(query_item)
    except KeyError, e:
        raise e
    except ValueError, e:
        raise e


def query(event, __context):
    """Query the data from DynamoDB timeseries database"""

    # Expected event format:
    # event = {
    #        'timeseries': [timeserie1, timeserie2],
    #        'start': start,
    #        'end': end,
    #        'granularity': constants.SECOND
    # }
    #

    configure_logging()
    configure_dynamodb()

    try:
        query_item = parse_query_item(event)
        return dynamo_db_query(query_item)
    except KeyError, e:
        raise e
    except ValueError, e:
        raise e


def put_items(event, __context):
    """Put items in DynamoDB"""

    # Expected event format:
    # event = {
    #    'timeserie1': [(1, 100), (2, 100)],
    #    'timeserie2': [(3, 100), (4, 100)],
    # }

    configure_logging()
    configure_dynamodb()
    configure_kinesis()

    try:
        insert_items = parse_insert_item(event)
        # dynamo_db_insert(insert_items)
        kinesis_insert(insert_items)
    except (KeyError, ValueError, TypeError), e:
        LOGGER.error('Cannot parse event for putting items')
        raise e


def handler(event, __context__):
    """Handler function of the database lambda"""

    # Event format:
    # event = {
    # 'operation' : get|post
    # 'payload' : payload
    # }

    if 'operation' in event:
        operation = event['operation']
        payload = event['payload']
        if operation == "get":
            return query(payload, __context__)
        elif operation == "last":
            return last(payload, __context__)
        elif operation == "post":
            return put_items(payload, __context__)
        else:
            raise ValueError('Invalid operation')
    else:
        raise ValueError('Invalid event format')
