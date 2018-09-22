"""Script to delete data"""
import aws_credentials
import boto3

client = boto3.client('dynamodb',
                      aws_access_key_id=aws_credentials.AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=aws_credentials.AWS_SECRET_KEY,
                      region_name=aws_credentials.AWS_REGION
                      )

key = {'timeserie': {'S': "test"}}
client.delete_item(TableName='timeseries_second', Key=key)
