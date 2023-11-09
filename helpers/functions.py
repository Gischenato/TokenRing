def log(msg):
    print(f'{BColors.BLACK}[{hour()}]{BColors.ENDC}', end=' ')
    print(msg, end='')
    print(BColors.ENDC)

def crc(msg):
    return crc32(msg.encode()) & 0xFFFFFFFF

def hour():
    return datetime.datetime.now().strftime("%H:%M:%S")