from enum import Enum

class ENumericSequence(Enum):
    Token = '9999'
    Message = '7777'

class EControlDirective(Enum):
    NACK = 'NACK'
    ACK  = 'ACK'
    NOT_EXIST = 'naoexiste'