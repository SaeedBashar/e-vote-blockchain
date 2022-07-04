import binascii
import hashlib
from pathlib import Path
import json

import Crypto
import Crypto.Random
from Crypto.Hash import  SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5


from src.blockchain import keygen

from src.blockchain.merkle_tree import Merkle_tree
from src.blockchain.transaction import Transaction

class Block:
    def __init__(self, index, timestamp, data, prev_hash, difficulty = 1) -> None:
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
            "data": tmp_tx,
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

        return blk

    def get_hash(self):
        str_val = str(self.index) + str(self.timestamp) + json.dumps(self.block_item['data']) + str(self.difficulty) + self.prev_hash + str(self.nonce) + self.merkle_root
        # str_val = str(self.timestamp) + str(self.transactions) + str(self.prev_hash) + str(self.nonce)
        return hashlib.sha256(str_val.encode()).hexdigest()

    # def get_hash(self):
    #     str_val : str = str(self.index) + str(self.timestamp) + str(self.data) + str(self.difficulty) + self.prev_hash + str(self.nonce) + self.merkle_tree
    #     return SHA256.new(str_val.encode('utf8'))
    
    def mine_block(self, dif):
        dif_str = "".join(["0" for x in range(dif)])
        while self.hash[:dif] != dif_str:
            self.nonce +=1
            self.hash = self.get_hash()
        self.set_block()

    def has_valid_transactions(self, block, state):

        path = Path('keypair/keypair.json')
        pub_key = json.loads(path.read_text())['public_key']

        gas = 0
        reward = 0
        balances = {}

        for tx in block['data']:
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
