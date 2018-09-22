"""Module to insert data into the tables"""
import aws_credentials
import argparse
from boto3.dynamodb.conditions import Key, Attr
from boto3.session import Session

TABLE = "timeseries"

dynamodb_session = Session(aws_access_key_id=aws_credentials.AWS_ACCESS_KEY_ID,
                           aws_secret_access_key=aws_credentials.AWS_SECRET_KEY,
                           region_name=aws_credentials.AWS_REGION)
dynamodb = dynamodb_session.resource('dynamodb')
table = dynamodb.Table(TABLE)

parser = argparse.ArgumentParser()
parser.add_argument("timeserie", help="Timeserie name")
parser.add_argument("start", help="Unix timestamp start")
parser.add_argument("end", help="Unix timestamp end")
args = parser.parse_args()
timeserie = args.timeserie
start = args.start
end = args.end

response = table.query(
    KeyConditionExpression=Key('timeserie').eq(timeserie) & Key('time').between(start, end)
)
item_count = response['Count']
items = response['Items']

print 'Items returned: %s' % item_count

data = [(int(item['time']), float(item['value'])) for item in items]

for d in data:
    print d
