import random
import socket
import time
from _thread import *
import threading
from datetime import datetime
import json
import ast
import requests

clients_lock = threading.Lock()
connected = 0

maxHealth = 100
numPlayersInGame = 3
maxMatchedGame = 3
curMatchedGame = 0
clients = {}
clients_in_queue = []
clients_in_removed = []
game_id = 0

players = {}

api_get_players = "https://10gcbr5ugl.execute-api.us-east-1.amazonaws.com/default/get_players"
api_play_game = "https://dsp56r4abi.execute-api.us-east-1.amazonaws.com/default/play_game"


def sendToClient(sock, address, message):
    if sock != None:
        m = json.dumps(message)
        print("Send to " + str(address) + " : " + m)
        sock.sendto(bytes(m, 'utf-8'), address)



def connectionLoop(sock):
    while True:
        data, addr = sock.recvfrom(1024)
        data = ast.literal_eval(data.decode('utf-8'))
        print(str(addr) + " : " + str(data))
        is_error = False
        if 'cmd' in data:
            cmd = data['cmd']
            if cmd == 'connect':
                if addr not in clients:
                    clients[addr] = {}
                    if 'user_id' in data:
                        user_id = data['user_id']
                        if user_id in players:
                            clients[addr]['player'] = players[user_id]
                        else:
                            msg = {"cmd": "error", "message": "user not found"}
                            sendToClient(sock, addr, msg)
                            is_error = True

                if is_error == False:
                    clients[addr]['connected'] = True
                    clients[addr]['timestamp'] = str(datetime.now())
                    msg = {"cmd": "connected", "data": clients[addr]}
                    sendToClient(sock, addr, msg)
            elif cmd == 'newGame':
                if addr in clients:
                    client = clients[addr]
                    if client not in clients_in_queue:
                        clients_in_queue.append( ( addr, client ) )
                        print("Waiting queue " + str(len(clients_in_queue)) + " : " + str(clients_in_queue))
                    else:
                        msg = {"cmd": "error", "message": "player is already in queue : " + client['player']['user_id']}
                        sendToClient(sock, addr, msg)
                else:
                    msg = {"cmd": "error", "message": "client is not in the list : " + str(addr)}
                    sendToClient(sock, addr, msg)

def playGame(sock, clients):
    global game_id
    # random winner
    user_ids = [data['player']['user_id'] for addr, data in clients]
    print(user_ids)
    r = requests.post(url=api_play_game, data = json.dumps( { "user_ids" : user_ids } ) )
    data = json.loads(r.text)
    print(data)
    for addr, client in clients:
        sendToClient(sock, addr, data)


def gameLoop(sock):
    global clients_in_queue
    global clients_in_removed
    global curMatchedGame
    global maxMatchedGame
    while True:
        if curMatchedGame < maxMatchedGame:
            if len(clients_in_queue) > numPlayersInGame:
                # no matchmaking, just linear ordering
                clients_in_playing = clients_in_queue[0:numPlayersInGame]
                playGame(sock, clients_in_playing)
                clients_in_removed.extend( clients_in_playing )
                clients_in_queue = clients_in_queue[numPlayersInGame:]
                curMatchedGame += 1

def cleanClients(sock):
    global clients_in_removed
    while True:
        while clients_in_removed:
            addr, data = clients_in_removed.pop(0)
            message = {"cmd": "disconnected", "data": str(data) }
            sendToClient(sock, addr, message )
            del clients[addr]

def main():
    r = requests.post(url=api_get_players, data='{}')
    data = json.loads(r.text)
    players_dict = data['Items']

    for player in players_dict:
        user_id = player['user_id']
        players[user_id] = player
    print(str(players.values()))

    port = 12345
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', port))

    start_new_thread(connectionLoop, (s,))
    start_new_thread(gameLoop, (s,))
    start_new_thread(cleanClients,(s,))
    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()
