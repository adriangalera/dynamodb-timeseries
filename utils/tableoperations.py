"""Script to initialize the time series data"""
import argparse
import logging

import os, sys, inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

import rollup.granularities, rollup.constants


def create_configuration_table(cli):
    """Create the configuration table"""
    response = cli.create_table(
        AttributeDefinitions=[
            {
                'AttributeName': 'timeserie',
                'AttributeType': 'S'
            }
        ],
        TableName=rollup.constants.get_configuration_table(),
        KeySchema=[
            {
                'AttributeName': 'timeserie',
                'KeyType': 'HASH'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 1,
            'WriteCapacityUnits': 1
        }
    )
    logging.debug(response)
    logging.info('Created table %s', rollup.constants.get_configuration_table())


def create_table(cli, tables, rcu=1, wcu=1):
    """Method to create the table"""

    # Since DynamoDB is schemaless, we only specify the key attributes
    # (timeserie and time)
    for table in tables:
        logging.info('Creating table %s', table)
        stream_spec = {'StreamEnabled': False}

        if table == rollup.granularities.get_granularity_table_text(rollup.granularities.GRANULARITIES[0]):
            stream_spec = {'StreamEnabled': True,
                           'StreamViewType': 'NEW_AND_OLD_IMAGES'}

        response = cli.create_table(
            AttributeDefinitions=[
                {
                    'AttributeName': 'timeserie',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'time',
                    'AttributeType': 'S'
                },
            ],
            TableName=table,
            KeySchema=[
                {
                    'AttributeName': 'timeserie',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'time',
                    'KeyType': 'RANGE'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': rcu,
                'WriteCapacityUnits': wcu
            },
            StreamSpecification=stream_spec
        )
        logging.debug(response)
        logging.info('Created table %s', table)


def enable_ttl(cli, tables):
    for table in tables:
        logging.info('Enabling TTL on table %s', table)
        response = cli.update_time_to_live(
            TableName=table,
            TimeToLiveSpecification={
                "Enabled": True,
                "AttributeName": "ttl"
            }
        )
        logging.debug(response)
        logging.info('TTL Enabled on table %s', table)


def delete_table(cli, tables):
    """Method to delete the table"""
    for table in tables:
        logging.info('Deleting table %s', table)
        response = cli.delete_table(
            TableName=table
        )
        logging.debug(response)
        logging.info('Table %s deleted', table)


def list_tables(cli):
    """List tables"""
    return cli.list_tables()


def get_stream_arn(seconds_tbl):
    ddbstreamcli = boto3.client('dynamodbstreams')
    streams = ddbstreamcli.list_streams(TableName=seconds_tbl)['Streams']
    stream_arn = streams[0]['StreamArn']
    logging.debug('Stream ARN is: %s', stream_arn)
    return stream_arn


def wait_tables(cli, tables, expect):
    """Blocks until tables are in the desired status"""

    def is_tbl_in_status(tbl_name):
        response = cli.describe_table(TableName=tbl_name)
        status = response['Table']['TableStatus']
        return status == expect

    while not all(is_tbl_in_status(table) for table in tables):
        time.sleep(5)


def link_stream_with_lambda(stream_arn, lambda_function='dynamodb-rollup'):
    logging.info('Linking stream %s with lambda %s', stream_arn, lambda_function)
    lambda_cli = boto3.client('lambda')
    response = lambda_cli.create_event_source_mapping(
        EventSourceArn=stream_arn,
        FunctionName=lambda_function,
        Enabled=True,
        BatchSize=100,
        StartingPosition='LATEST',
    )

    logging.debug(response)
    logging.info('Lambda %s linked with stream %s', lambda_function, stream_arn)


if __name__ == '__main__':
    import boto3
    import aws_credentials
    import time

    logging.basicConfig(level=logging.INFO)

    client = boto3.client('dynamodb',
                          aws_access_key_id=aws_credentials.AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=aws_credentials.AWS_SECRET_KEY,
                          region_name=aws_credentials.AWS_REGION
                          )

    parser = argparse.ArgumentParser()
    parser.add_argument("operation",
                        help="Operation to perform. Accepted: "
                             "create, delete, create-configuration")
    parser.add_argument("table_prefix", help="Include a table prefix to separate use cases")
    args = parser.parse_args()

    os.environ[rollup.constants.TABLE_PREFIX_ENV_VAR] = args.table_prefix

    TABLES = [rollup.granularities.get_granularity_table_text(gran) for gran in
              rollup.granularities.GRANULARITIES]

    if args.operation == "create":
        create_table(client, TABLES)
        logging.info('Waiting tables to be created ...')
        wait_tables(client, TABLES, "ACTIVE")
        enable_ttl(client, TABLES)

        lambda_function_name = args.table_prefix + "_ts_rollup"

        seconds_stream_arn = get_stream_arn(TABLES[0])
        link_stream_with_lambda(seconds_stream_arn, lambda_function=lambda_function_name)
    elif args.operation == "delete":
        delete_table(client, TABLES)
    elif args.operation == 'create-configuration':
        create_configuration_table(client)
    else:
        print 'Accepted operations: create, delete'
