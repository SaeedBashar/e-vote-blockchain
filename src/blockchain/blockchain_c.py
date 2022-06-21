
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

from src.blockchain.transaction_c import Transaction
from src.blockchain.block_c import Block

keys = keygen.gen_key_pair()
private_key = keys['private_key']
public_key = keys['pubic_key']
KEY_PAIR = keys['key_pair']

tmp_public_key = '30819f300d06092a864886f70d010101050003818d0030818902818100a9433cc207ef9a748188014eddf20d12433c3b15f4c1827fa6fff37061887de1a9ebb8f58821402c35aedf2a195bcf1bc5b6ea7d0a45f5bcc81a9b2fe1ec693c881aa0ad1a69dd81cd4f985ec30526885a0a629ccd6e630d9152a96b42e6b8d0df305b918d50c60ce4fe9d6694746b4343e6fc93fa5e0def1bef06098a2cad2f0203010001'

class Blockchain:
    def __init__(self):
        self.initial_coin_release = Transaction(None, tmp_public_key, 100000000000, 0, [], "")
        self.chain = [self.create_genesis_block()]
        self.difficulty = 4
        self.transactions = []

        self.block_time = 30000
        self.reward = 297

        self.state = {
            tmp_public_key : {
                'balance': 100000000000,
                'body': "",
                'timestamps': [],
                'storage': {}
            }
        }

    def create_genesis_block(self):
        block = Block(len(self.chain), '123456789', [self.initial_coin_release], self.difficulty)
        block.prev_hash = '0' * 64
        block.mine_block(self.difficulty)
        self.chain.append(block)

    def add_transaction(self, trans):
        balance = self.get_balance(trans['from']) - trans['value'] - trans['gas']

        for tx in self.transactions:
            if tx['from'] == trans['from']:
                balance -= (tx['value'] + tx['gas'])

        if Transaction.is_valid(trans, self.state) and balance >= 0:
            self.transactions.append(trans)


    def get_balance(self, address):
        return self.state[address]['balance'] if self.state[address] else 0