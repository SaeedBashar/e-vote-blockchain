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

    def sign(self, keyPair):

        if(keygen.hex_key(keyPair.publickey().exportKey(format='DER')) == self.from_addr):
            private_key = RSA.importKey(keygen.unhex_key(private_key))
            signer = PKCS1_v1_5.new(private_key)
            h = self.hash()
            sig = signer.sign(h)
            return keygen.hex_key(sig)
    
    def hash(self):
        str_val : str = self.from_addr + self.to_addr + str(self.value) + str(self.gas) + str(self.args) + str(self.timestamp)
        return SHA256.new(str_val.encode('utf8'))

    def set_transaction(self):
        self.tx_item = {
            'from_addr': self.from_addr,
            'to_addr': self.to_addr,
            'value': self.value,
            'gas': self.gas,
            'args': self.args,
            'timestamp': self.timestamp,
            'tx_hash' : self.tx_hash
        }

    @classmethod
    def is_valid(self, tx, state):
        if tx['from_addr'] == "" or tx['to_addr'] == "":
            print('failed first')
            return False

        if int(tx['value']) < 0:
            print('failed second')
            return False

        if int(tx['gas']) < 0:
            print('failed thir')
            return False

        if (state[tx['from_addr']]['balance'] if state[tx['from_addr']] != None else 0) < int(tx['value']) + int(tx['gas']):
            print('failed forth')
            return False
    
        return True

    