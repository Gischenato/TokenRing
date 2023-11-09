from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM, SHUT_RDWR, timeout
from time import sleep, time
import threading
import sys
import datetime
from binascii import crc32
from random import randint
import Config


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

class Timer:
    def __init__(self):
        self.start_time = None
    
    def start(self):
        self.start_time = time()
    
    def elapsed_time(self):
        if self.start_time == None:
            return 0
        return time() - self.start_time


TIMER = Timer()

IP = Config.MEU_IP
PORT = Config.MINHA_PORTA

NEXT_USER_IP = Config.IP_DESTINO_DO_TOKEN.split(':')[0]
NEXT_USER_PORT = Config.IP_DESTINO_DO_TOKEN.split(':')[1]

SOCKET = socket(AF_INET, SOCK_DGRAM)
SOCKET.bind((IP, PORT))

NAME = Config.APELIDO_DA_MAQUINA_ATUAL

HOST = Config.TOKEN

MENSAGENS = []
TOKEN = False
MESSAGE_SENT = False


ATTEMPT = 0

ERROR_CHANCE = Config.CHANCE_DE_ERRO
TIME_OUT = Config.TEMPO_TOKEN
RING_SIZE = Config.QUANTIDADE_DE_USERS
TOKEN_MIN_TIME = TIME_OUT * RING_SIZE
TOKEN_MAX_TIME = TIME_OUT * RING_SIZE * RING_SIZE



ONLY_MESSAGES = False
KILL_TOKEN = False


def calc_crc(msg):
    if randint(0, 100) < ERROR_CHANCE:
        return randint(0, 2**32)
    return crc32(msg.encode()) & 0xFFFFFFFF

def hour():
    return datetime.datetime.now().strftime("%H:%M:%S")

def log(msg, message=False):
    if ONLY_MESSAGES and not message:
        return
    print(f'{bcolors.BLACK}[{hour()}]{bcolors.ENDC}', end=' ')
    print(msg, end='')
    print(bcolors.ENDC)

def pass_token(_=None):
    global TOKEN, KILL_TOKEN
    # passa o token caso ele não esteja bloqueado
    if KILL_TOKEN:
        KILL_TOKEN = False
        log(f'{bcolors.BLACK}token blocked')
        return
    TOKEN = False
    log(f'{bcolors.ORANGE}passing token')
    # log(f'{bcolors.BLACK}--------------------')
    socket_send('9000')
    # inicia o timer para verificar o tempo que o token demora para voltar
    TIMER.start()

def handle(msg):
    global TOKEN, MESSAGE_SENT, ATTEMPT, TIMER, TOKEN_MIN_TIME, KILL_TOKEN
    # trata a mensagem recebida

    msg = msg.decode()
    decode = msg.split(':')
    
    # timeout do token 
    sleep(TIME_OUT)

    # caso seja um token
    if decode[0] == '9000':
        # se o token estiver bloqueado, passa o token e retorna
        if KILL_TOKEN:
            pass_token()
            return
        # se for o host checa o tempo que o token demorou para voltar
        if HOST:
            elapsed_time = TIMER.elapsed_time()
            log(f'{bcolors.BLACK}elapsed time: {elapsed_time}')
            # se o tempo for menor que o tempo mínimo, ignora o token
            if elapsed_time < TOKEN_MIN_TIME:
                log(f'{bcolors.RED}token received before {TOKEN_MIN_TIME} seconds: ignoring token')
                return
    
        # se estiver esperando um ack, passa o token e retorna
        if MESSAGE_SENT: 
            log(f'{bcolors.RED}received token but was waiting for ack')
            MESSAGE_SENT = False
            pass_token()
            return
        log(f'{bcolors.BLACK}--------------------')
        log(f'{bcolors.ORANGE}received token')
        
        # marca que a maquina esta com o token e tenta enviar uma mensagem
        TOKEN = True
        did_send, data = send_message()
        # caso nao tenha mensagem para enviar, passa o token e retorna
        if not did_send:
            log(f'{bcolors.YELLOW}no message to send')
            pass_token()
            TOKEN = False
        else:
            to, content = data
            log(f'{bcolors.CYAN}message {bcolors.MAGENTA}{content} {bcolors.CYAN}to {bcolors.MAGENTA}{to} {bcolors.CYAN}sent: waiting for ack', message=True)
        return
    
    # caso seja uma mensagem

    data = decode[1].split(';')
    controle, from_user, to_user, crc, msg = data

    # se a mensagem for para mim
    if from_user == NAME:
        
        if controle == 'ACK':
            log(f'{bcolors.GREEN}received ack from {to_user}')
        elif controle == 'NACK':
            # caso seja um nack, tenta enviar a mensagem novamente
            log(f'{bcolors.RED}received nack from {to_user}', message=True)
            if ATTEMPT == 0:
                # caso seja a primeira tentativa, envia a mensagem novamente e retorna
                log(f'{bcolors.CYAN}sending the message again', message=True)
                ATTEMPT += 1
                did_send, data = send_message()
                return
            else:
                # caso seja a segunda tentativa, passa o token
                log(f'{bcolors.RED}max attempts reached', message=True)
                ATTEMPT = 0
                
        elif controle == 'naoexiste':
            if to_user == 'TODOS':
                log(f'{bcolors.GREEN}broadcast message received by everyone')
            else:
                log(f'{bcolors.RED}user {to_user} not found', message=True)

        # retira a mensagem da fila e passa o token
        popMessage()
        pass_token()
        MESSAGE_SENT = False
        return
    
    if MESSAGE_SENT and from_user != NAME:
        log(f'{bcolors.RED}received message but was waiting for ack')
    
    # se for uma mensagem para mim, verifica o crc
    # se o crc estiver correto, mostra a mensagem
    if to_user == NAME:
        new_crc = calc_crc(msg)
        if new_crc != int(crc):
            log(f'{bcolors.RED}msg from {from_user} with crc error')
            controle = 'NACK'
        else:
            log(f'{bcolors.MAGENTA}{from_user}{bcolors.GREEN}: {msg}', message=True)
            controle = 'ACK'

    # se for um broadcast, mostra a mensagem
    elif to_user == 'TODOS':
        log(f'{bcolors.GREEN}(broadcast) {bcolors.MAGENTA}{from_user}{bcolors.GREEN}: {msg}', message=True)
    else:
        log(f'{bcolors.BLUE}message to {to_user}')
    new_msg = f'7777:{controle};{from_user};{to_user};{crc};{msg}'
    socket_send(new_msg)

def addMessage(msg):
    # adiciona uma mensagem na fila caso ela não esteja cheia
    if len(MENSAGENS) >= 10:
        log(f'{bcolors.RED}Fila de mensagens cheia', message=True)
        return
    log(f'{bcolors.MAGENTA}Adding message {msg}', message=True)
    MENSAGENS.append(msg)

def getMessage():
    # retorna a primeira mensagem da fila
    if len(MENSAGENS) == 0:
        return None
    return MENSAGENS[0]

def popMessage():
    # remove a primeira mensagem da fila
    if len(MENSAGENS) > 0: 
        MENSAGENS.pop(0)

def generateMsg(msg, to):
    return f'7777:naoexiste;{NAME};{to};{calc_crc(msg)};{msg}'

def listen_keyboard():
    global ONLY_MESSAGES
    # fica escutando o teclado e chama a função correspondente
    while True:
        new_message = input().split(' ')
        control = new_message.pop(0)
        HANDLER = {
            'pm': store_pm,
            'br': store_broadcast,
            'token': generateToken,
            'kill': kill_token,
            'logs': show_logs,
        }
        if control not in HANDLER:
            log(f'{bcolors.RED}Comando {control} não existe')
            continue
        HANDLER[control](new_message)

def show_logs(_):
    global ONLY_MESSAGES
    # mostra apenas logs marcados como mensagem
    ONLY_MESSAGES = not ONLY_MESSAGES

def generateToken(_):
    # gera um novo token
    pass_token()

def send_message(_=None):
    global MESSAGE_SENT
    data = getMessage()
    
    # se não tiver nenhuma mensagem na fila, retorna
    if data == None:
        return False, (None, None)
    
    text, to = data
    # gera a mensagem com o formato 7777:naoexiste;from;to;crc;msg
    msg = generateMsg(text, to)
    
    # seta a flag para indicar que uma mensagem foi enviada
    MESSAGE_SENT = True

    # envia a mensagem
    socket_send(msg)

    # retorna o destinatário e o conteúdo da mensagem
    _, _, to, _, content = msg.split(';')
    return True, (to, content)

def socket_send(msg):
    global SOCKET
    # envia uma mensagem com o socket para o próximo usuário no anel
    SOCKET.sendto(msg.encode(), (NEXT_USER_IP, NEXT_USER_PORT))

def store_pm(new_message):
    # guarda a mensagem privada na fila
    to = new_message.pop(0)
    msg = ' '.join(new_message)
    addMessage((msg, to))

def store_broadcast(new_message):
    # guarda a mensagem de broadcast na fila
    to = 'TODOS'
    msg = ' '.join(new_message)
    addMessage((msg, to))

def kill_token(_):
    # seta a flag para bloquear o token
    global KILL_TOKEN
    log(f'{bcolors.BLACK}next token will be blocked')
    KILL_TOKEN = True

def listen_udp():
    SOCKET.settimeout(2)
    log(f'listening udp on {SOCKET.getsockname()}')
    if HOST:
        pass_token() # se for o host, inicia passando o token
    while True:
        try:
            if HOST:
                # caso seja o host e o token não tenha sido passado em TOKEN_MAX_TIME segundos, gera um novo token
                elapsed_time = TIMER.elapsed_time()
                if elapsed_time > TOKEN_MAX_TIME:
                    log(f'{bcolors.RED}token time exceeded: generating new token')
                    pass_token()
            # se a thread principal não estiver mais ativa, fecha o socket e encerra a thread
            if not threading.main_thread().is_alive():
                SOCKET.close() 
                return
            message, _ = SOCKET.recvfrom(2048)
            handle(message)
        except:
            pass

def main():
    # inicia o servidor e fica escutando o teclado
    threading.Thread(target=listen_udp).start()
    listen_keyboard()
 

main()