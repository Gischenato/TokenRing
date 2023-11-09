class PackageData:
    def __init__(self, controle, from_user, to_user, crc, msg):
        self.controle = controle
        self.from_user = from_user
        self.to_user = to_user
        self.crc = crc
        self.msg = msg

class BColors:
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
