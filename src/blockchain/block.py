import hashlib
import json

from src.blockchain.merkle_tree import Merkle_tree

####################################
## Block Class
class Block():
    def __init__(self, timestamp, transactions, prevhash='') -> None:

        ###########################
        ## Block header
        self.timestamp = int(timestamp)
        self.nonce = 0
        self.merkle_tree = Merkle_tree(transactions).get_root_leaf()
        self.prev_hash = prevhash

        self.transactions = transactions

        self.hash = self.get_hash()
        self.set_block()
    
    def set_block(self):
        tmp_tx = []
        # for tx in self.transactions:
        for item in self.transactions:
            tmp_tx.append(item.tx_item)

        self.block_item = {
            "timestamp": str(self.timestamp),
            "nonce": self.nonce,
            "merkle_tree": self.merkle_tree,
            "prev_hash": self.prev_hash,
            "hash": self.hash,
            "transactions": tmp_tx
        }

    def get_hash(self):
        str_val = str(self.timestamp) + str(self.transactions) + str(self.prev_hash) + str(self.nonce)
        return hashlib.sha256(str_val.encode()).hexdigest()

    def mine_block(self, dif):
        dif_str = "".join(["0" for x in range(dif)])
        while self.hash[:dif] != dif_str:
            self.nonce +=1
            self.hash = self.get_hash()
        self.set_block()
        # print("Block successfull mined!!")
    
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)

    def __str__(self):
        return self.toJSON()
        


