from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM, SHUT_RDWR, timeout
from time import sleep
import threading
import sys
import datetime

class bcolors:
    BLACK = '\033[90m'
    ORANGE = '\033[33m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    ENDC = '\033[0m'

IP = '172.27.80.1'
PORT = int(sys.argv[1])

TIME_OUT = 2.5
NEXT_USER_IP = '172.27.80.1'
NEXT_USER_PORT = int(sys.argv[2])

SOCKET = socket(AF_INET, SOCK_DGRAM)
SOCKET.bind((IP, PORT))

NAME = sys.argv[3]

MENSAGENS = []
TOKEN = False
MESSAGE_SENT = False

ATTEMPT = 0

def hour():
    return datetime.datetime.now().strftime("%H:%M:%S")

def log(msg):
    print(f'{bcolors.BLACK}[{hour()}]{bcolors.ENDC}', end=' ')
    print(msg, end='')
    print(bcolors.ENDC)

def pass_token(_=None):
    global TOKEN
    # log(f'{bcolors.WARNING}Passing token')
    TOKEN = False
    socket_send('9000')


def handle(msg, addr):
    global TOKEN, MESSAGE_SENT
    msg = msg.decode()
    # log(f'{bcolors.MAGENTA}{msg}')
    decode = msg.split(':')
    sleep(TIME_OUT)
    # log(decode)
    if decode[0] == '9000':
        if MESSAGE_SENT: 
            log(f'{bcolors.RED}received token but was waiting for ack')
            return
        log(f'{bcolors.ORANGE}received token')
        TOKEN = True
        did_send = send_message()
        if not did_send:
            log(f'{bcolors.YELLOW}no message to send, passing token')
            pass_token()
            TOKEN = False
        else:
            log(f'{bcolors.CYAN}message sent, waiting for ack')
        return
    
    # log(f'{bcolors.BLUE}received message {decode[1]}')
    data = decode[1].split(';')
    # log(f'{bcolors.MAGENTA}{data}')
    controle, from_user, to_user, crc, msg = data
    if MESSAGE_SENT:
        log(f'{bcolors.ORANGE}{controle}  {from_user}  {to_user}  {crc}  {msg}')
        # must be my message
        # log(f'{bcolors.BLUE}TO AQUI 1')
        if from_user != NAME:
            # log(f'{bcolors.BLUE}TO AQUI 2')
            log(f'{bcolors.FAIL}received message but was waiting for ack')
            return
        if controle == 'ACK':
            # log(f'{bcolors.BLUE}TO AQUI 3')
            log(f'{bcolors.GREEN}received ack from {to_user}')
            # pass_token()
        elif controle == 'NACK':
            # log(f'{bcolors.BLUE}TO AQUI 4')
            # TODO: RESEND MESSAGE HERE
            log(f'{bcolors.WARNING}received nack from {to_user}')
            # send_message()
        elif controle == 'naoexiste':
            # log(f'{bcolors.BLUE}TO AQUI 5')
            log(f'{bcolors.RED}user {to_user} not found')
        pass_token()
        # log(f'{bcolors.BLUE}TO AQUI 4')
        MESSAGE_SENT = False
        return

    if to_user == NAME:
        log(f'{bcolors.GREEN}msg from {from_user}: {msg}')
        controle = 'ACK'
    else:
        log(f'{bcolors.BLUE}message to {to_user}')
    # TODO: CHECAR CRC
    new_msg = f'7777:{controle};{from_user};{to_user};{crc};{msg}'
    socket_send(new_msg)


def addMessage(msg):
    if len(MENSAGENS) >= 10:
        log(f'{bcolors.RED}Fila de mensagens cheia')
        return
    log(f'{bcolors.MAGENTA}Adding message {msg}')
    MENSAGENS.append(msg)

def getMessage():
    if len(MENSAGENS) == 0:
        # log('Fila de mensagens vazia')
        return None
    return MENSAGENS.pop(0)

def generateMsg(msg, to):
    crc = 0 # TODO GERAR CRC
    return f'7777:naoexiste;{NAME};{to};{crc};{msg}'

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
    # log(f'sending: {msg}')
    socket_send(msg)
    return True

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

def main():
    global TOKEN, MESSAGE_SENT, MENSAGENS, SOCKET
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