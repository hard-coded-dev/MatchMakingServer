import json
import boto3
import decimal
from botocore.exceptions import ClientError, UnknownKeyError

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return int(o)
        if isinstance(o, set):  #<---resolving sets as lists
            return list(o)
        return super(DecimalEncoder, self).default(o)


def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('player_db')
    statusCode = 200
    try:
        response = table.scan()
        statusCode = 400
        item = response
    except UnknownKeyError as e:
        statusCode = 400
        item = e.response['Error']['Code']
    except ClientError as e:
        statusCode = 400
        item = e.response['Error']['Code']
    
    return {
        'statusCode': statusCode,
        'body': json.dumps(item, cls = DecimalEncoder)
    }
