import binascii
import hashlib
from pathlib import Path
import json
from time import time


import Crypto
import Crypto.Random
from Crypto.Hash import  SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

from src.blockchain.merkle_tree import Merkle_tree
from src.blockchain.transaction import Transaction

class Block:
    def __init__(self, index, timestamp, data, prev_hash, difficulty = 4) -> None:
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.difficulty = difficulty
        
        self.merkle_root = Merkle_tree(data).get_root_leaf()

        self.prev_hash = prev_hash
        self.nonce = 0
        self.hash = ""   # Needed
        self.set_block()
        self.hash = self.get_hash()

    def set_block(self):
        tmp_tx = []
        for item in self.data:
            tmp_tx.append(item.tx_item)

        self.block_item = {
            "index": self.index,
            "timestamp": str(self.timestamp),
            "data": json.dumps(tmp_tx),
            "difficulty": self.difficulty,
            "merkle_root": self.merkle_root,
            "prev_hash": self.prev_hash,
            "nonce": self.nonce,
            "hash": self.hash
        }

    @classmethod
    def get_blk_object(self, el):
        txs = []
        for tx in json.loads(el[2]):
            i = Transaction.get_tx_object(tx)
            txs.append(i)

        blk = Block(int(el[0]), el[1], txs, el[5], int(el[3]))
        blk.merkle_root = el[4]
        blk.hash = el[7]
        blk.nonce = int(el[6])

        blk.set_block()
        return blk

    def get_hash(self):
        str_val = str(self.index) + str(self.timestamp) + json.dumps(self.block_item['data']) + str(self.difficulty) + self.prev_hash + str(self.nonce) + self.merkle_root
        
        return hashlib.sha256(str_val.encode()).hexdigest()

    def mine_block(self, dif):
        dif_str = "".join(["0" for x in range(dif)])
        while self.hash[:dif] != dif_str:
            self.nonce +=1
            self.hash = self.get_hash()
        self.set_block()

    @classmethod
    def is_valid(self, block, last_block):


        if float( block['timestamp']) > time() :
            return False

        if block['prev_hash'] != last_block['hash']:
            return False

        for tx in block['data']:
            if Transaction.is_valid(tx) == False:
                return False

        
        return True
