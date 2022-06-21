import binascii
import hashlib

import Crypto
import Crypto.Random
from Crypto.Hash import  SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

import time as tm
from time import time

import keygen

keys = keygen.gen_key_pair()

private_key = keys['private_key']
public_key = keys['pubic_key']
KEY_PAIR = keys['key_pair']

class Transaction:
    def __init__(self, from_addr, to_addr, value, gas = 1, args = [], timestamp = time()) -> None:
        self.from_addr = from_addr
        self.to_addr = to_addr
        self.value = value
        self.gas = gas
        self.args = args
        self.timestamp = timestamp

        self.set_transaction()

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
            'timestamp': self.timestamp
        }

    def is_valid(self, tx, state):
        if tx['from_addr'] == "" or tx.to_addr == "":
            return False

        if tx.value < 0:
            return False

        if tx.gas < 1:
            return False

        if (state[tx['from_addr']].balance if state[tx['from_addr']] else 0) < tx.amount + tx.gas:
            return False
         
        if tx['from_addr'] != public_key:
            return False

        return True

    