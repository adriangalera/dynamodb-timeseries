"""Script to insert data directly calling the lambda database.
This is used to simulated the behaviour of the real callers of the lambda

This script simulates inserting all the values for an hour

"""
import boto3
import random
import time
import json

client = boto3.client('lambda')
lambda_name = 'test_ts_db'
timeserie = 'test-manual'

cur_time = long(time.time())
tsdata = []
for minute in xrange(60):
    values = random.randint(-100, 100)
    val_time = cur_time + (minute * 60)
    tsdata.append((val_time, values))

event = {
    'operation': 'post', 'payload': {timeserie: tsdata}
}

event = json.dumps(event)

print 'Invoking lambda %s with event %s' % (lambda_name, event)

response = client.invoke(
    FunctionName=lambda_name,
    InvocationType='Event',
    Payload=event,
)

print str(response['Payload'].read())
