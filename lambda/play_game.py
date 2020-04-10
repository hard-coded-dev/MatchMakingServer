import json
import boto3
import decimal
import random
from botocore.exceptions import ClientError
from datetime import datetime

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        if isinstance(o, set):  #<---resolving sets as lists
            return list(o)
        return super(DecimalEncoder, self).default(o)

def calc_elo( rating1, rating2, isPlayer1Won ):
    kfactor = 32
    p1 = 1.0 / ( 1.0 + pow( 10, ( rating2 - rating1 ) / 400 ) )
    p2 = 1.0 / ( 1.0 + pow( 10, ( rating1 - rating2 ) / 400 ) )
    print( "%d-%f vs %d-%f" % ( rating1, p1, rating2, p2 ) )
    
    new_rating1 = rating1
    new_rating2 = rating2
    if isPlayer1Won:
        new_rating1 += ( 1 - p1 ) * kfactor
        new_rating2 += ( 0 - p2 ) * kfactor
    else:
        new_rating1 += ( 0 - p1 ) * kfactor
        new_rating2 += ( 1 - p2 ) * kfactor
    return new_rating1, new_rating2


# calculates average of elo scores among all players
def calc_scores( scores ):
    numPlayers = len(scores)
    new_scores = [0] * numPlayers
    print("calc_scores = " + str(scores))
    
    for i in range( numPlayers - 1 ):
        for j in range( i + 1, numPlayers ):
            # i-th player wins the game
            new_score1, new_score2 = calc_elo( scores[i], scores[j], True )
            new_scores[i] += new_score1
            new_scores[j] += new_score2
    print(new_scores)
    new_scores = [ int(s / (numPlayers-1)) for s in new_scores ]
    print("calced_scores = " + str(new_scores))
    return new_scores


def play_game(user_ids):
    result = ''
    try:
        dynamodb = boto3.resource('dynamodb')
        response = dynamodb.batch_get_item(
            RequestItems = {
                'player_db' :
                { 'Keys' : [ { 'user_id' : id } for id in user_ids] }
            }
        )
        print(response)
        if 'Responses' in response:
            if 'player_db' in response['Responses']:
                res = response['Responses']
                players = res['player_db']
                print(players)
                # random player win the game
                random.shuffle( players )
                
                player_table = dynamodb.Table('player_db')
   
                ranks = []
                user_previous_points = []
                user_points = []
                for i in range(len(players)):
                    user_previous_points.append( int(players[i]['point']) )
                user_points = calc_scores( user_previous_points )
                
                for i in range(len(players)):
                    player = players[i]
                    ranks.append( player['user_id'] )

                    if i == 0:
                        player['win'] += 1
                    else:
                        player['loss'] += 1

                    #update player db
                    player_table.update_item(
                        Key = {'user_id' : player['user_id'] },
                        UpdateExpression="set point = :p, win = :w, loss = :l",
                        ExpressionAttributeValues={
                            ':p': user_points[i],
                            ':w': player['win'],
                            ':l': player['loss']
                        },
                        ReturnValues="ALL_NEW"
                    )

                game_table = dynamodb.Table('game_db')
                game_time = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S") )
                print(ranks, game_time, user_points, user_previous_points)
                next_game_id = game_table.scan( 
                    Select = 'COUNT'
                    )['Count']
                print("time = " + game_time + ", game_id = " + str(next_game_id) )
            
                # update game db
                game_data = {
                    "game_id" : next_game_id,
                    "game_time" : game_time,
                    "user_ids" : ranks,
                    "user_points" : user_points,
                    "user_previous_points" : user_previous_points,
                }
                game_table.put_item(
                    Item = game_data
                )
                result = { "cmd" : "result", "ranks" : ranks, "user_points" : user_points, "user_previous_points" : user_previous_points }
                print(result)
                
                
    except ClientError as e:
        result = e.response['Error']['Code']
        
    return result

def lambda_handler(event, context):
    result = ''
    statusCode = 200
    if 'body' in event:
        print(event['body'])
        body = json.loads(event['body'])
        try:
            if 'user_ids' in body:
                user_ids = body['user_ids']
                result = play_game( user_ids )
            else:
                statusCode = 400
                result = { 'message' : 'user ids required' }
        except ClientError as e:
            result = e.response['Error']['Code']
            
    return {
        'statusCode': statusCode,
        'body': json.dumps(result, cls=DecimalEncoder)
    }
    
