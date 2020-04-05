import ast
import socket
import _thread
import json
import time
import requests

host = '127.0.0.1'
port = 12345
server_address = (host, port)

api_login_player = "https://3dhgtxnyjb.execute-api.us-east-1.amazonaws.com/default/login_player"


class matchClient:
    user_id = ''
    wins = 0
    loss = 0
    points = 0
    is_connected = False
    sock = None

    def __init__(self, userId, win, loss, point):
        self.user_id = userId
        self.wins = int(win)
        self.loss = int(loss)
        self.points = int(point)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def connect(self):
        message = {"cmd": "connect", "user_id": self.user_id}
        self.is_connected = True
        self.sendToServer(message)

    def disconnect(self):
        self.is_connected = False

    def askNewGame(self):
        message = {"cmd": "newGame", "user_id": str(self.user_id), "point": str(self.points)}
        self.sendToServer(message)

    def sendToServer(self, message):
        if self.sock != None:
            m = json.dumps(message)
            print(self.user_id + " send to server : " + str(m))
            self.sock.sendto(bytes(m, 'utf8'), server_address)

    def gameLoop(self):
        if self.sock != None and self.is_connected == True:
            data, addr = self.sock.recvfrom(1024)
            data = json.loads(data.decode('utf-8'))
            print(self.user_id + " received from server : " + str(data))
            if 'cmd' in data:
                cmd = data['cmd']
                if cmd == 'connected':
                    self.is_connected = True
                elif cmd == 'waiting':
                    pass
                elif cmd == 'result':
                    pass
                elif cmd == 'disconnected':
                    self.disconnect()
                elif cmd == 'error':
                    print('error : ' + data['message'])

def main():
    user_id = 'Bo'
    message = {"user_id": user_id}
    r = requests.post(url=api_login_player, data=json.dumps(message))
    player = json.loads(r.text)
    client = matchClient(player['user_id'], player['win'], player['loss'], player['point'])
    client.connect()
    client.askNewGame()
    while True:
        client.gameLoop()
        time.sleep(1)


if __name__ == '__main__':
    main()