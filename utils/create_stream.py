"""Script to create a Kinesis stream"""
import boto3
import argparse
import os, sys, inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

import rollup.constants

parser = argparse.ArgumentParser()
parser.add_argument("table_prefix", help="Include a table prefix to separate use cases")
args = parser.parse_args()

os.environ[rollup.constants.TABLE_PREFIX_ENV_VAR] = args.table_prefix
stream_name = rollup.constants.get_kinesis_stream()

try:
    client = boto3.client('kinesis')
    stream = client.create_stream(StreamName=stream_name, ShardCount=5)
except Exception:
    pass
