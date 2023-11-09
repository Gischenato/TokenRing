from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM, SHUT_RDWR, timeout
from time import sleep
from helpers.classes import PackageData, BColors
from helpers.enums import ENumericSequence, EControlDirective
from binascii import crc32
from helpers.functions import log, crc, hour
import threading
import sys
import datetime

## CURRENT MACHNE INFO
IP = '172.31.219.151'
PORT = int(sys.argv[1])
TIME_OUT = 2.5
NAME = sys.argv[3]
TOKEN = False

## NEXT MACHINE INFO
NEXT_USER_IP = '172.31.219.151'
NEXT_USER_PORT = int(sys.argv[2])

## GENERAL
SOCKET = socket(AF_INET, SOCK_DGRAM)
SOCKET.bind((IP, PORT))
MENSAGENS = []
MESSAGE_SENT = False
QUEUE_SIZE = 10
ATTEMPT = 0

## passa um token para maquina a direita
def pass_token(_=None):
    global TOKEN
    # log(f'{BColors.WARNING}Passing token')
    TOKEN = False
    socket_send('9000')

def handle_token():
    if MESSAGE_SENT: # esperando a mensagem de confirmacao voltar (ack)
        log(f'{BColors.RED}received token but was waiting for ack')
        return
    
    log(f'{BColors.ORANGE}received token')

    TOKEN = True
    did_send = send_message() ## checa se tem mensagem pra enviar e envia
    
    if not did_send:
        log(f'{BColors.YELLOW}no message to send, passing token')
        pass_token()
        TOKEN = False
    else:
        log(f'{BColors.CYAN}message sent, waiting for ack')\

def handle_new_message(decode):
    ## se veio ateh aqui eh porque enviou e precisa receber a confirmacao
 
    ##log(f'{BColors.MAGENTA}{data}')

    if MESSAGE_SENT:
        log(f'{BColors.ORANGE}{controle}  {from_user}  {to_user}  {crc}  {msg}')

        if from_user != NAME:
            log(f'{BColors.FAIL}received message but was waiting for ack')
        elif controle == EControlDirective.ACK: 
            log(f'{BColors.GREEN}received ack from {to_user}')
        elif controle == EControlDirective.NACK:
            log(f'{BColors.RED}received nack from {to_user}')
        elif controle == EControlDirective.NOT_EXIST:
            log(f'{BColors.RED}user {to_user} not found')
    
    pass_token()
    MESSAGE_SENT = False

## handle upcoming messages and tokens
def handle(msg, addr):
    global TOKEN, MESSAGE_SENT
    msg = msg.decode()
    decode = msg.split(':')
    numeric_sequence = decode[0]
    data = decode[1].split(';')
    controle, from_user, to_user, crc, msg = data

    sleep(TIME_OUT)

    ## se recebeu um token
    if numeric_sequence   == ENumericSequence.Token:
        handle_token()
    elif numeric_sequence == ENumericSequence.Message:
        handle_new_message(decode)
    else:
        if to_user == NAME:
            log(f'{BColors.GREEN}msg from {from_user}: {msg}')
            controle = 'ACK'
        else:
            log(f'{BColors.BLUE}message to {to_user}')
        # TODO: CHECAR CRC
        new_msg = f'7777:{controle};{from_user};{to_user};{crc};{msg}'
        socket_send(new_msg)

def addMessage(msg):
    if len(MENSAGENS) >= QUEUE_SIZE: 
        log(f'{BColors.RED}Fila de mensagens cheia')
        return
    log(f'{BColors.MAGENTA}Adding message {msg}')
    MENSAGENS.append(msg)

def getMessage():
    if len(MENSAGENS) == 0:
        # log('Fila de mensagens vazia')
        return None
    return MENSAGENS.pop(0)

def generateMsg(msg, to):
    return f'7777:naoexiste;{NAME};{to};{crc(msg)};{msg}'

def listen_keyboard():
    while True:
        new_message = input().split(' ')
        control = new_message.pop(0)
        HANDLER = {
            'pm': create_pm,
            'br': create_broadcast,
            'token': pass_token,
            's': send_message,
        }
        HANDLER[control](new_message)

def send_message(_=None):
    global MESSAGE_SENT
    msg = getMessage()
    if msg == None:
        return False
    MESSAGE_SENT = True
    log(f'sending: {msg}')
    socket_send(msg)
    return True

def send_message_after_nack(data):
    controle, from_user, to_user, crc, msg = data
    new_msg = f'7777:NACK;{from_user};{to_user};{crc(msg)};{msg}'
    socket_send(new_msg)

def socket_send(msg):
    global SOCKET
    SOCKET.sendto(msg.encode(), (NEXT_USER_IP, NEXT_USER_PORT))

def create_pm(new_message):
    to = new_message.pop(0)
    msg = ' '.join(new_message)
    addMessage(generateMsg(msg, to))

def create_broadcast(new_message):
    to = 'TODOS'
    msg = ' '.join(new_message)
    addMessage(generateMsg(msg, to))

def read_config(filename):
    with open(filename, 'r') as file:
    # Read all lines of the file into a list
        config = file.readlines()

    NEXT_USER_IP, NEXT_USER_PORT = config[0].strip().split(":")
    NAME = config[1]
    TIME_OUT = int(config[2])
    TOKEN = config[3].lower() in ("true", "1")
    IP, PORT = config[0].strip().split(":")

    NEXT_USER_PORT = int(NEXT_USER_PORT)
    PORT = int(NEXT_USER_PORT)

    if NEXT_USER_IP is None or NEXT_USER_PORT is None:
        print('You must insert IP and port number in the format ip:port in the config file')
        exit(1)

def current_machine_info():
    return f'#--Current_Machine--#\n\nMachine-IP: {IP}\nMachine-Port: {PORT}\nMachine-alias: {NAME}\nToken-Time: {TIME_OUT}s\nHas-Token: {TOKEN}\n'

def receiver_machine_info():
    return f'#--Receiver_Machine--#\n\nMachine-IP: {NEXT_USER_IP}\nMachine-Port: {NEXT_USER_PORT}\n'

def main():
    global TOKEN, MESSAGE_SENT, MENSAGENS, SOCKET
    filename = 'config'
    #read_config(filename);
    #print(current_machine_info());
    #print(receiver_machine_info());
    threading.Thread(target=listen_udp).start()
    listen_keyboard()

def listen_udp():
    SOCKET.settimeout(2)
    log(f'listening udp on {SOCKET.getsockname()}')
    while True:
        try:
            if not threading.main_thread().is_alive():
                SOCKET.close() 
                return
            message, clientAddress = SOCKET.recvfrom(2048)
            handle(message, clientAddress)
        except:
            pass

main()