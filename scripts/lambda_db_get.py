"""Script to insert data directly calling the lambda database.
This is used to simulated the behaviour of the real callers of the lambda
"""
import boto3
import time
import json

client = boto3.client('lambda')
lambda_name = 'test_ts_db'
timeserie = 'test-manual'

start = 1517396400
end = 1517403600

granularies = ["minute", "hour", "day"]

for gran in granularies:
    get_payload = {
        'timeseries': [timeserie],
        'start': start,
        'end': end,
        'granularity': gran
    }

    event = {
        'operation': 'get', 'payload': get_payload
    }

    event = json.dumps(event)

    #print 'Invoking lambda %s with event %s' % (lambda_name, event)

    response = client.invoke(
        FunctionName=lambda_name,
        InvocationType='RequestResponse',
        Payload=event,
    )

    print gran + ": " + str(response['Payload'].read())
