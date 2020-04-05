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
numUpdatePerSeconds = 10
clients = {}
clients_in_queue = []

players = {}

api_get_players = "https://10gcbr5ugl.execute-api.us-east-1.amazonaws.com/default/get_players"


def sendToClient(sock, address, message):
    if sock != None:
        m = json.dumps(message)
        print("Send to " + str(address) + " : " + m)
        sock.sendto(bytes(m, 'utf-8'), address)


def playGame(sock, clients):
    # random winner
    players = random.shuffle(clients.values())
    rankings = [p['user_id'] for p in players]
    msg = {"cmd": "result", "ranking": str(rankings)}
    for addr, player in clients:
        sendToClient(sock, addr, msg)


def connectionLoop(sock):
    while True:
        data, addr = sock.recvfrom(1024)
        data = ast.literal_eval(data.decode('utf8'))
        print(str(addr) + " : " + str(data))
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
                            return

                clients[addr]['connected'] = True
                clients[addr]['timestamp'] = str(datetime.now())
                msg = {"cmd": "connected", "data": clients[addr]}
                sendToClient(sock, addr, msg)
            elif cmd == 'newGame':
                if addr in clients:
                    client = clients[addr]
                    if client not in clients_in_queue:
                        clients_in_queue.append(player)
                    else:
                        msg = {"cmd": "error", "message": "player is already in queue : " + client['player']['user_id']}
                        sendToClient(sock, addr, msg)
                else:
                    msg = {"cmd": "error", "message": "client is not in the list : " + str(addr)}
                    sendToClient(sock, addr, msg)


def cleanClients(sock):
    while True:
        for c in list(clients.keys()):
            if (datetime.now() - clients[c]['timestamp']).total_seconds() > 10:
                print('Dropped Client: ', c)
                clients_lock.acquire()
                del clients[c]
                clients_lock.release()
                message = {"cmd": 3, "player": {"id": str(c)}}
                m = json.dumps(message)
                for c in clients:
                    sock.sendto(bytes(m, 'utf8'), (c[0], c[1]))
        time.sleep(1)


def gameLoop(sock):
    while True:
        if clients_in_queue != None and len(clients_in_queue) > numPlayersInGame:
            # no matchmaking, just linear ordering
            clientsInGame = clients_in_queue[0:numPlayersInGame]
            playGame(clientsInGame)
            clients_in_queue = clients_in_queue[numPlayersInGame:]


def main():
    r = requests.post(url=api_get_players, data='{}')

    data = json.loads(r.text)
    players_dict = data['Items']
    print(players_dict)
    for player in players_dict:
        user = player['user_id']
        players[user] = user
    print(str(players.values()))

    port = 12345
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', port))

    start_new_thread(connectionLoop, (s,))
    start_new_thread(gameLoop, (s,))
    # start_new_thread(cleanClients,(s,))
    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()
