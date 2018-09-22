"""Base Test that enables local stack"""
import logging
import os
import threading
import unittest

import boto3
import botocore.config
import sfdockertest

import utils.tableoperations
from rollup import constants, granularities, lambda_database
from kinesisconsumer.consumer import KinesisDynamoConsumer


class BaseLocalStackTest(unittest.TestCase):
    """Class to perform the initialization of local stack when testing AWS services"""

    create_tables_enabled = True
    create_lambda_enabled = True
    create_kinesis_enabled = True

    DYNAMODB_ENDPOINT = "http://localhost:4569"
    LAMBDA_ENDPOINT = "http://localhost:4574"
    DYNAMODB_STREAM_ENDPOINT = "http://localhost:4570"
    KINESIS_ENDPOINT = "http://localhost:4568"

    LAMBDA_FUNCTION_PUT = "ddb-timeseries-insert"
    LAMBDA_FUNCTION_GET = "ddb-timeseries-get"

    docker_container = None
    reader = None
    reading_thread = None

    @classmethod
    def create_tables(cls):
        """Create the dynamodb tables"""
        logging.debug('Creating dynamo db tables')
        client = boto3.client('dynamodb', endpoint_url=cls.DYNAMODB_ENDPOINT)

        tables = [granularities.get_granularity_table_text(gran) for gran in granularities.GRANULARITIES]

        utils.tableoperations.create_table(client, tables, rcu=1000, wcu=1000)
        utils.tableoperations.create_configuration_table(client)
        logging.info('DynamoDB tables created')

        # Get stream ARN from seconds table
        client = boto3.client('dynamodbstreams',
                              endpoint_url=cls.DYNAMODB_STREAM_ENDPOINT)
        return client.list_streams()['Streams'][0]['StreamArn']

    @classmethod
    def create_lambdas(cls, stream_arn):
        """Create the lambda function"""
        client = boto3.client('lambda', endpoint_url=cls.LAMBDA_ENDPOINT,
                              region_name='us-west-2')
        cur_dir = os.path.dirname(__file__)
        zip_file = os.path.join(cur_dir, 'lambda.zip')

        response = client.create_function(
            FunctionName='ddb-timeseries-rollup',
            Runtime='python2.7',
            Role='r1',
            Handler='lambda_database.process_stream_event',
            Code={
                'ZipFile': open(zip_file, 'r').read(),
            },
            Description='string',
            Publish=True,
        )
        logging.debug(response)

        response = client.create_function(
            FunctionName=cls.LAMBDA_FUNCTION_PUT,
            Runtime='python2.7',
            Role='r1',
            Handler='lambda_database.put_items',
            Code={
                'ZipFile': open(zip_file, 'r').read(),
            },
            Description='string',
            Publish=True,
        )
        logging.debug(response)

        response = client.create_function(
            FunctionName=cls.LAMBDA_FUNCTION_GET,
            Runtime='python2.7',
            Role='r1',
            Handler='lambda_database.query',
            Code={
                'ZipFile': open(zip_file, 'r').read(),
            },
            Description='string',
            Publish=True,
        )
        logging.debug(response)

        response = client.create_event_source_mapping(
            EventSourceArn=stream_arn,
            FunctionName='ddb-timeseries-rollup',
            Enabled=True,
            BatchSize=100,
            StartingPosition='LATEST',
        )
        logging.debug(response)

    @classmethod
    def create_stream(cls):
        """Create a Kinesis stream"""
        shards = len(granularities.GRANULARITIES)
        client = boto3.client('kinesis', endpoint_url=cls.KINESIS_ENDPOINT, region_name='us-west-2')
        try:
            stream = client.create_stream(StreamName=constants.get_kinesis_stream(), ShardCount=shards)
            logging.debug(stream)
        except Exception, err:
            raise err

        print client.describe_stream(StreamName=constants.get_kinesis_stream())

    @classmethod
    def setUpClass(cls):
        # Make sure everything is stopped

        granularities.enable_all_granularities()

        os.environ[constants.DDB_LOCAL_ENV_VAR] = cls.DYNAMODB_ENDPOINT
        os.environ[constants.KIN_LOCAL_ENV_VAR] = cls.KINESIS_ENDPOINT
        os.environ[constants.TABLE_PREFIX_ENV_VAR] = "test"
        os.environ["ADD_DEFAULT"] = "true"

        lambda_database.configure_dynamodb()

        docker_os_env = {
            'SERVICES': 'dynamodb,lambda,dynamodbstreams,kinesis,cloudwatch',
            'AWS_ACCESS_KEY_ID': 'foo',
            'AWS_SECRET_KEY': 'foo',
            'AWS_SECRET_ACCESS_KEY': 'foo',
            'AWS_DEFAULT_REGION': 'eu-west-1',
            constants.DEBUG_LOGS: "1",
            "DEBUG": "1",
            constants.DDB_LOCAL_ENV_VAR: cls.DYNAMODB_ENDPOINT,
            constants.KIN_LOCAL_ENV_VAR: cls.KINESIS_ENDPOINT,
            constants.AGG_IN_SERIE: "1",
            constants.ENABLE_ALL_GRAN_ENV_VAR: "1",
            constants.TABLE_PREFIX_ENV_VAR: "test",
            "ADD_DEFAULT": "true"
        }

        os.environ.update(docker_os_env)

        cur_dir = os.path.dirname(__file__)
        zip_file = os.path.join(cur_dir, 'lambda.zip')

        lambda_database_files = os.path.join(cur_dir, '../rollup/*.py')

        # Create zip file
        os.system(
            "zip -r -9 -j %s %s" % (zip_file, lambda_database_files))

        # Need kinesis to work with dynamodb streams

        def check_ready():
            """check the docker container is up and running"""
            try:
                # Need to fine tune connection parameters to enhance the speed of testing
                config = botocore.config.Config(connect_timeout=10, read_timeout=10,
                                                retries={'max_attempts': 0})

                client = boto3.client('lambda', endpoint_url=cls.LAMBDA_ENDPOINT,
                                      region_name='us-west-2', config=config)
                response = client.list_functions()

                empty_functions = response['Functions'] == []
                client = boto3.client('dynamodb', endpoint_url=cls.DYNAMODB_ENDPOINT,
                                      region_name='us-west-2', config=config)

                response = client.list_tables()
                empty_tables = response['TableNames'] == []

                return empty_functions and empty_tables

            except Exception, e:
                return False

        cls.docker_container = sfdockertest.DockerContainer(
            "localstack/localstack:latest", {4569: 4569, 4574: 4574, 4570: 4570, 4568: 4568},
            env_var=docker_os_env)
        cls.docker_container.start(check=check_ready)

        try:
            seconds_stream_arn = None

            if cls.create_tables_enabled:
                logging.info('Creating tables')
                seconds_stream_arn = cls.create_tables()
                logging.info('Tables created')

            if cls.create_lambda_enabled:
                logging.info('Creating lambdas')
                cls.create_lambdas(seconds_stream_arn)
                logging.info('Lambdas created')

            if cls.create_kinesis_enabled:
                logging.info('Creating Kinesis stream')
                cls.create_stream()
                logging.info('Kinesis stream created')

                # Wait to kinesis to be created
                client = boto3.client('kinesis', endpoint_url=cls.KINESIS_ENDPOINT, region_name='us-west-2')
                shards = []
                while not shards:
                    shards = client.describe_stream(StreamName=constants.get_kinesis_stream())['StreamDescription'][
                        'Shards']

            # Disable botocore logging:
            logging.getLogger('boto3').setLevel(logging.CRITICAL)
            logging.getLogger('botocore').setLevel(logging.CRITICAL)

            cls.reader = KinesisDynamoConsumer(constants.get_kinesis_stream(), batch_size=25)

            def start_reader(kinesis_reader):
                """Starts a new thread execution with the kinesis consumer"""
                kinesis_reader.start()

            cls.reading_thread = threading.Thread(target=start_reader, args=(cls.reader,))
            # Set as daemon, so when the main thread dies, this dies too
            cls.reading_thread.daemon = True
            cls.reading_thread.start()


        except Exception, e:
            cls.docker_container.stop()
            logging.error('Error initializing localstack')
            raise e

    @classmethod
    def tearDownClass(cls):
        if cls.reader:
            cls.reader.stop()
        # Join reading thread
        if cls.reading_thread:
            cls.reading_thread.join()
        cls.docker_container.stop()
        cur_dir = os.path.dirname(__file__)
        filename = os.path.join(cur_dir, 'lambda.zip')
        os.system("rm %s" % filename)
