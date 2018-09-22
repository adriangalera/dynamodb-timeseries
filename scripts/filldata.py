"""Module to insert data into the tables"""
import aws_credentials
import boto3
import argparse
import random
import time

TABLE = "timeseries_second"


def item_to_dynamo_db_item(item):
    """Convert each item into DynamoDB format"""
    now = long(time.time())
    return {
        'timeserie': {'S': item['timeserie']},
        'time': {'S': str(item['time'])},
        'value': {'N': str(item['value'])},
        'ttl': {'N': str(now + (1 * 60))},
    }


def item_to_dynamo_db_item_batch(item):
    """Convert each item into DynamoDB format"""
    now = long(time.time())
    return {
        'timeserie': item['timeserie'],
        'time': str(item['time']),
        'value': str(item['value']),
        'ttl': now + (1 * 60)
    }


def insert_values_one_by_one(items):
    client = boto3.client('dynamodb',
                          aws_access_key_id=aws_credentials.AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=aws_credentials.AWS_SECRET_KEY,
                          region_name=aws_credentials.AWS_REGION
                          )
    for item in items:
        response = client.put_item(
            TableName=TABLE,
            Item=item_to_dynamo_db_item(item)
        )
        print response
        time.sleep(0.5)


def insert_batch(items):
    dynamodb = boto3.resource('dynamodb',
                              aws_access_key_id=aws_credentials.AWS_ACCESS_KEY_ID,
                              aws_secret_access_key=aws_credentials.AWS_SECRET_KEY,
                              region_name=aws_credentials.AWS_REGION
                              )
    table = dynamodb.Table(TABLE)
    with table.batch_writer() as batch:
        for item in items:
            batch.put_item(
                Item=item_to_dynamo_db_item_batch(item)
            )
    print 'Inserted!'


parser = argparse.ArgumentParser()
parser.add_argument("timeserie", help="Timeserie name")
parser.add_argument("start", help="Unix timestamp start")
parser.add_argument("end", help="Unix timestamp end")
parser.add_argument("--batch", help="Enable batch writing", action='store_true')
args = parser.parse_args()
timeserie = args.timeserie
start = int(args.start)
end = int(args.end)
batch_mode = args.batch

total = (end - start)
print 'Creating %d items ...' % total
# values = [random.uniform(-100, 100) for __ in xrange(total)]
values = [1 for __ in xrange(total)]
items = []
curr = start
for index in range(total):
    items.append({
        'timeserie': timeserie,
        'time': curr,
        'value': values[index]
    })
    curr += 1

print 'Created %d items' % len(items)

if batch_mode:
    insert_batch(items)
else:
    insert_values_one_by_one(items)
