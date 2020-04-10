import json
import decimal
import boto3
from botocore.exceptions import ClientError


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return int(o)
        if isinstance(o, set):  #<---resolving sets as lists
            return list(o)
        return super(DecimalEncoder, self).default(o)
        
def lambda_handler(event, context):
    result = ''
    statusCode = 200
    
    try:
        dynamodb = boto3.resource('dynamodb')
        player_table = dynamodb.Table('player_db')
        response = player_table.scan()
        players = response['Items']
        print(players)
        for i in range(len(players)):
            player = players[i]
            player_table.update_item(
                Key = {'user_id' : player['user_id'] },
                UpdateExpression="set point = :p, win = :w, loss = :l",
                ExpressionAttributeValues={
                    ':p': 1000 + i * 20,
                    ':w': 0,
                    ':l': 0
                },
                ReturnValues="UPDATED_NEW"
            )
        result = "player db updated"
    except ClientError as e:
        statusCode = 400
        result = e.response['Error']['Code']
            
    return {
        'statusCode': statusCode,
        'body': json.dumps(result, cls=DecimalEncoder)
    }
    
