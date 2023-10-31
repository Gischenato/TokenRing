from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM, SHUT_RDWR, timeout
import json
import pprint
import threading
import sys

IP = '192.168.56.1'
PORT = 5000

SOCKET = socket(AF_INET, SOCK_DGRAM)
SOCKET.bind((IP, PORT))

error_control = {
    'naoexiste': 'naoexiste',
    'NACK': 'NACK',
    'ACK': 'ACK',
}

NAME = 'giovanni' 

MENSAGENS = []
TOKEN = False
MESSAGE_SENT = False

def send_message():
    pass

def handle(msg, addr):
    pass

def addMessage(msg):
    if len(MENSAGENS) >= 10:
        print('Fila de mensagens cheia')
        return
    print(f'Adding message {msg}')
    MENSAGENS.append(msg)

def getMessage():
    if len(MENSAGENS) == 0:
        print('Fila de mensagens vazia')
        return None
    return MENSAGENS.pop(0)



def generateMsg(msg, to):
    crc = 0 # TODO GERAR CRC
    return f'7777:naoexiste;{NAME};{to};{crc};{msg}'

def listen_keyboard():
    while True:
        new_message = input().split(' ')
        control = new_message.pop(0)
        print(new_message)
        print(control)
        HANDLER = {
            'pm': create_pm,
            'br': create_broadcast,
            'send': send_message,
            # 'token': create_token
        }
        HANDLER[control](new_message)

def send_message(a):
    msg = getMessage()
    if msg == None:
        return


def create_pm(new_message):
    to = new_message.pop(0)
    msg = ' '.join(new_message)
    addMessage(generateMsg(msg, to))

def create_broadcast(new_message):
    to = 'TODOS'
    msg = ' '.join(new_message)
    addMessage(generateMsg(msg, to))

def main():
    global TOKEN, MESSAGE_SENT, MENSAGENS, SOCKET
    # threading.Thread(target=listen_udp).start()
    listen_keyboard()

def listen_udp():
    SOCKET.settimeout(2)
    print(f'listening udp on {SOCKET.getsockname()}')
    while True:
        try:
            message, clientAddress = SOCKET.recvfrom(2048)
            handle(message, clientAddress)
        except:
            if not threading.main_thread().is_alive():
                SOCKET.close() 
                return

main()