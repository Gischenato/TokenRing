from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM, SHUT_RDWR, timeout
import json
import pprint
import threading
import sys

IP = '192.168.56.1'
PORT = 5000

SOCKET = socket(AF_INET, SOCK_DGRAM)
SOCKET.bind((IP, PORT))
TOKEN = 9000

error_control = {
    'naoexiste': 'naoexiste',
    'NACK': 'NACK',
    'ACK': 'ACK',
}


def send_message():
    pass

handle(msg, addr):
    pass

def listen_udp(self, socket:socket):
    socket.settimeout(2)
    print(f'listening udp on {socket.getsockname()}')
    while True:
        try:
            message, clientAddress = socket.recvfrom(2048)
            handle(message, clientAddress)
        except:
            if not threading.main_thread().is_alive():
                socket.close() 
                return