import random
import socket
import time
import _thread
import json
import ast
import requests
from matchClient import matchClient

api_get_players = "https://10gcbr5ugl.execute-api.us-east-1.amazonaws.com/default/get_players"
players = []
clients = []
clients_playing = []
clients_pool = []
max_game_requests = 100


def gameLoop():
    while True:
        if (len(clients_pool) > 0):
            c = clients_pool.pop()
            clients_playing.append(c)
            c.connect()
            c.askNewGame()
        time.sleep(1)


def cleanup():
    while True:
        disconnected = []
        for i in range(len(clients_playing)):
            c = clients_playing[i]
            if c.is_connected == False:
                disconnected.append(c)

        if len(disconnected) > 0:
            for c in disconnected:
                if c in clients_playing:
                    clients_playing.remove(c)
                    clients_pool.append(c)
            random.shuffle(clients_pool)
        time.sleep(1)


def main():
    r = requests.post(url=api_get_players)

    data = json.loads(r.text)
    players = data['Items']
    for player in players:
        c = matchClient(player['user_id'], player['win'], player['loss'], player['point'])
        clients.append(c)
        clients_pool.append(c)
    random.shuffle(clients_pool)
    print(str(clients))

    _thread.start_new_thread(gameLoop, ())
    _thread.start_new_thread(cleanup, ())
    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()
