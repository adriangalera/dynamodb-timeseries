"""Script to add a configuration entry"""
import json
import boto3

lambda_function = 'test_ts_conf'
client = boto3.client('lambda')

event = {
    'operation': 'post',
    'payload': json.dumps({
        'timeserie': 'test-manual',
        'aggregation_method': 'sum',
        'timezone': 'Europe/Madrid',
        'retentions': {}
    })
}

event = json.dumps(event)

print 'Invoking lambda %s with event %s' % (lambda_function, event)

response = client.invoke(
    FunctionName=lambda_function,
    InvocationType='Event',
    Payload=event,
)

print str(response['Payload'].read())
