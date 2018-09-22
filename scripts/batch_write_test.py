import boto3
from decimal import Decimal

client = boto3.client('dynamodb')

batch = [
    {'PutRequest': {
        'Item': {'ttl': '1529052960', 'timeserie': u'test-manual', 'value': Decimal('-57'), 'time': '1526374560'}}
    },
    {'PutRequest': {
        'Item': {'ttl': '1529052960', 'timeserie': u'test-manual', 'value': Decimal('58'), 'time': '1526374560'}}
    }
]
