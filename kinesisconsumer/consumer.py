"""This is the implementation of the consumer"""
import time
import os
import threading
import logging
import json

from rollup.lambda_database import InsertItem, configure_kinesis, configure_dynamodb
from rollup.timeserie_configuration import Configuration
from rollup import aggregations, granularities, constants


class KinesisDynamoConsumer(object):
    """Consumer Application that consume messages from Kinesis and insert them onto DynamoDB Tables"""
    DYNAMO_DB_MAX_BATCH = 25

    def __init__(self, stream_name, batch_size=10, sleep_time=0.2):
        self.stream_name = stream_name
        self.run = True
        self.kinesis = configure_kinesis()
        self.dynamodb = configure_dynamodb()
        self.logger = logging.getLogger("KinesisDynamoDB")
        self.batch_size = batch_size
        self.sleep_time = sleep_time
        reload_thread = threading.Thread(target=self.reload_parameters)
        reload_thread.daemon = True
        reload_thread.start()

    def reload_parameters(self):
        while True:
            time.sleep(10)
            self.read_set_parameters()

    def read_set_parameters(self):
        """Read an external configuration file"""
        self.logger.debug('**** Reading and setting parameters ****')
        parameter_file = os.path.dirname(os.path.realpath(__file__)) + "/parameters.json"
        with open(parameter_file, "r") as parameters:
            parameters_json = json.load(parameters)
            batch_size = int(parameters_json["BATCH_SIZE"])
            sleep_time = float(parameters_json["SLEEP_TIME"])

            if batch_size != self.batch_size:
                self.logger.info('**** New batch size: %s ****', batch_size)
                self.batch_size = batch_size
            if sleep_time != self.sleep_time:
                self.logger.info('**** New sleep time: %s ****', sleep_time)
                self.sleep_time = sleep_time

    def stop(self):
        self.logger.info("Stop KinesisDynamoDB consumer")
        self.run = False

    def start(self):
        """Start consuming messages"""
        self.logger.info("Start KinesisDynamoDB consumer")

        # Create one thread per shard. The data is partitioned in the stream by its table,
        # so all the data inside a shard will be stored into the same dynamo DB table
        shard_list = self.kinesis.describe_stream(StreamName=self.stream_name)['StreamDescription']['Shards']

        shard_threads = []
        for shard in shard_list:
            shard_id = shard['ShardId']
            self.logger.info("Creating worker for shard %s ...", shard_id)
            th = threading.Thread(target=self.process_shard, args=(shard_id,))
            th.daemon = True
            shard_threads.append(th)

        for shard_thread in shard_threads:
            shard_thread.start()

        while self.run:
            time.sleep(1)

    def process_shard(self, shard_id):
        """Function that process a shard"""
        shard_it = self.kinesis.get_shard_iterator(StreamName=self.stream_name,
                                                   ShardId=shard_id,
                                                   ShardIteratorType='LATEST')['ShardIterator']
        iterations = 0
        while self.run:
            try:
                iterations += 1
                # Obtain the records from the Kinesis stream shard
                time_get_records_1 = time.time()
                out = self.kinesis.get_records(ShardIterator=shard_it, Limit=self.batch_size)
                records = out["Records"]
                time_get_records_2 = time.time()
                gather_time = time_get_records_2 - time_get_records_1
                # Process the data
                items = []
                tjson1 = time.time()
                for record in records:
                    items.append(json.loads(record['Data']))
                tjson2 = time.time()
                tjson = tjson2 - tjson1

                # Store the obtained data in DynamoDB by batches (one thread per batch for max performance)
                dynamo_time_1 = time.time()
                table = self.process_ts_items(items, threaded=True, shard_id=shard_id)
                dynamo_time_2 = time.time()
                dynamo_time = dynamo_time_2 - dynamo_time_1

                # Get next shard iterator
                shard_it = out.get('NextShardIterator', None)
                if not shard_it:
                    self.logger.info("No next shard iterator, closing")
                    break

                # Print debugging info
                loop_time = self.sleep_time + gather_time + +tjson + dynamo_time
                wcu_output = len(records) / loop_time
                if records and table:
                    self.logger.info("[Table %s] Insert %d records in %s seconds. WCU = %f",
                                     table, len(records), loop_time, wcu_output)
                    time.sleep(self.sleep_time)
                else:
                    # Make sure to sleep even when there are no records,
                    # otherwise the provisioned throughput of the shard
                    # will be consumed instantaneously
                    # self.logger.info("[Table %s] Insert %d records in %s seconds. WCU = %f", info_tup)
                    time.sleep(0.5)

                # TODO: Implement dynamic change of BATCH_SIZE and SLEEP_TIME
                """
                if iterations % 10 == 0:
                    set_parameters()
                """
            except Exception, err:
                print err
                pass

    def split_into_batches(self, items):
        grouped = list(zip(*[iter(items)] * self.DYNAMO_DB_MAX_BATCH))
        non_batched = items[len(grouped) * self.DYNAMO_DB_MAX_BATCH:]
        if non_batched:
            grouped.append(non_batched)
        return grouped

    def process_ts_items(self, items, threaded=True, shard_id=None):
        """Split the user list into batches of 25, later insert them sequentially.

        If more performance is required, each batch can be inserted in a separate thread

        """

        def sequential_insert(batches):
            """Insert the batches one after the other"""
            for batch in batches:
                try:
                    response = self.dynamodb.batch_write_item(RequestItems=batch)
                    self.logger.debug(response)
                    while response['UnprocessedItems']:
                        response = self.dynamodb.batch_write_item(RequestItems=response['UnprocessedItems'])
                        self.logger.debug(response)
                except Exception, err:
                    self.logger.error(err)
                    pass

        def threaded_insert(batches):
            """Insert the batches simultaneously (one thread per batch)"""
            threads = []
            for batch in batches:
                th = threading.Thread(target=sequential_insert, args=([batch],))
                threads.append(th)
            for thread in threads:
                thread.start()
                thread.join()

        if items:
            batch_list = []
            table = None
            for item_batch in self.split_into_batches(items):
                items_db = []
                for item in item_batch:

                    # The assumption that all records belonging to the same shard belongs to the same table is false.
                    # Two tables with two different hashes can be put into the same shard.

                    # If we want to enable one stream / table, we have to manually set the correspondence
                    # table - partition key

                    granularity = item['granularity']

                    # Check if item has to be stored or aggregated
                    if 'aggregation' in item:
                        insert_item = InsertItem.from_dict(item['data'])
                        ts_conf = Configuration.from_dict(item['aggregation'])
                        aggregations.rollup(self.dynamodb, granularity, insert_item, ts_conf)
                    else:
                        # Here we can make the assumption, since all the non aggregated values will share the same
                        # hash, so the same shard
                        if not table:
                            table = granularities.get_granularity_table_text(granularity)
                        insert_item = InsertItem.from_dict(item['data'])
                        dyn_batch_item = {'PutRequest': {'Item': insert_item.to_dynamo_db()}}
                        items_db.append(dyn_batch_item)
                if items_db:
                    batch_list.append({table: items_db})

            if batch_list:
                if threaded:
                    threaded_insert(batch_list)
                else:
                    sequential_insert(batch_list)

            return table


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('boto3').setLevel(logging.CRITICAL)
    logging.getLogger('botocore').setLevel(logging.CRITICAL)
    stream_name = constants.get_kinesis_stream()
    KinesisDynamoConsumer(stream_name).start()
