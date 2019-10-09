"""Script to insert data directly calling the lambda database.
This is used to simulated the behaviour of the real callers of the lambda
"""
import boto3
import random
import time
import json
session = boto3.Session(profile_name='gal', region_name="eu-west-1")
client = session.client('lambda')

lambda_name = 'test_ocado_ts_db'
timeserie = 'test-manual'

while True:
    values = random.randint(-100, 100)
    cur_time = int(time.time())

    val_tuple = (cur_time, values)

    event = {
        'operation': 'post', 'payload': {timeserie: [val_tuple]}
    }

    event = json.dumps(event)

    print ('Invoking lambda %s with event %s' % (lambda_name, event) )

    response = client.invoke(
        FunctionName=lambda_name,
        InvocationType='Event',
        Payload=event,
    )

    print ( str(response['Payload'].read()) )

    time.sleep(10)
