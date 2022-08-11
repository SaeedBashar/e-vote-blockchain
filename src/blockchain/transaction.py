import binascii
import hashlib
import json

import Crypto
import Crypto.Random
from Crypto.Hash import  SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

import time as tm
from time import time

from src.blockchain import keygen


class Transaction:
    def __init__(self, from_addr, to_addr, value, gas = 1, args = [], timestamp=0) -> None:
        self.from_addr = from_addr
        self.to_addr = to_addr
        self.value = value
        self.gas = gas
        self.args = args
        self.timestamp = timestamp
        self.tx_hash = self.get_hash()

        self.set_transaction()

    def get_hash(self):
        str_val = str(self.from_addr) + str(self.to_addr) + str(self.value) + str(self.gas) + json.dumps(self.args) + str(self.timestamp)
        return hashlib.sha256(str_val.encode()).hexdigest()

    
    def hash(self):
        str_val : str = self.from_addr + self.to_addr + str(self.value) + str(self.gas) + str(self.args) + str(self.timestamp)
        return SHA256.new(str_val.encode('utf8'))

    def set_transaction(self):
        self.tx_item = {
            'from_addr': self.from_addr,
            'to_addr': self.to_addr,
            'value': self.value,
            'gas': self.gas,
            'args': json.dumps(self.args),
            'timestamp': self.timestamp,
            'tx_hash' : self.tx_hash
        }

    @classmethod
    def get_tx_object(self, el):
        if type(el) == dict:
            tx = Transaction(el['from_addr'], el['to_addr'], int(el['value']), int(el['gas']), el['args'], el['timestamp'])
            tx.tx_hash = el['tx_hash']
            tx.set_transaction()
        else:
            if el[4] == None or el[4] == "" or el[4] == "[]":
                args = []
            else:
                args = json.loads(el[4])

            tx = Transaction(el[0], el[1], el[2], el[3], args, el[5])
            tx.tx_hash = el[6]
            tx.set_transaction()

        return tx

    @classmethod
    def is_valid(self, tx):
       
        if int(tx['value']) < 0 or int(tx['gas']) < 0:
    
            return False
    
        return True

    