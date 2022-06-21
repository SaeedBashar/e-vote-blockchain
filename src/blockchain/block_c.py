import binascii
import hashlib
from pathlib import Path
import json

import Crypto
import Crypto.Random
from Crypto.Hash import  SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5


import keygen

from src.blockchain.merkle_tree import Merkle_tree
from src.blockchain.transaction_c import Transaction

class Block:
    def __init__(self, index, timestamp, data, difficulty = 1) -> None:
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.difficulty = difficulty
        
        self.merkle_tree = Merkle_tree(data).get_root_leaf()

        self.prev_hash = ''
        self.nonce = 0
        self.hash = keygen.hex_key(self.get_hash())
        self.set_block()

    def set_block(self):
        tmp_tx = []
        for item in self.data:
            tmp_tx.append(item.tx_item)

        self.block_item = {
            "index": self.index,
            "difficulty": self.difficulty,
            "timestamp": str(self.timestamp),
            "nonce": self.nonce,
            "merkle_tree": self.merkle_tree,
            "prev_hash": self.prev_hash,
            "hash": self.hash,
            "data": tmp_tx
        }

    def get_hash(self):
        str_val : str = self.index + self.timestamp + self.data + self.difficulty + self.prev_hash + self.nonce
        return SHA256.new(str_val.encode('utf8'))
    
    def mine_block(self, dif):
        dif_str = "".join(["0" for x in range(dif)])
        while self.hash[:dif] != dif_str:
            self.nonce +=1
            self.hash = keygen.hex_key(self.get_hash())
        self.set_block()

    def has_valid_transactions(self, block, state):

        path = Path('keypair/keypair.json')
        pub_key = json.loads(path.read_text())['public_key']

        gas = 0
        reward = 0
        balances = {}

        for tx in block.data:
            if tx['from_addr'] != pub_key:
                if balances[tx['from_add']] is None:
                    balances[tx['from_addr']] = (state[tx['from_addr']]['balance'] if state[tx['from_addr']] else 0) - tx['value'] - tx['gas']
                else:
                    balances[tx['from']] -= tx['value'] + tx['gas']
                gas += tx['gas']
            else:
                reward = tx['value']


        for tx in block.data:
            if Transaction.is_valid(tx) == False:
                return False
            
        return True
