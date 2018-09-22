"""Module to configure constants"""
import os

DDB_LOCAL_ENV_VAR = 'DYNAMO_DB_LOCAL_ENDPOINT'
KIN_LOCAL_ENV_VAR = 'KINESIS_LOCAL_ENDPOINT'
DEBUG_LOGS = 'DEBUG_LOGS'
AGG_IN_SERIE = 'AGG_IN_SERIE'
CHAR_AGG = '____'
ENABLE_ALL_GRAN_ENV_VAR = 'ALL_GRAN'
TABLE_CONFIGURATION = 'timeserie_configuration'
TABLE_PREFIX_ENV_VAR = 'TABLE_PREFIX'
KINESIS_STREAM = 'ts_stream'
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "100"))


def get_configuration_table():
    """Return the configuration table modified by the env var"""
    if TABLE_PREFIX_ENV_VAR in os.environ:
        return os.environ.get(TABLE_PREFIX_ENV_VAR, "") + "_" + TABLE_CONFIGURATION
    return TABLE_CONFIGURATION


def get_kinesis_stream():
    """Return the name of the kinesis stream"""
    if TABLE_PREFIX_ENV_VAR in os.environ:
        return os.environ.get(TABLE_PREFIX_ENV_VAR, "") + "_" + KINESIS_STREAM
    return KINESIS_STREAM
