import hashlib
import json

####################################
## Block Class
class Block():
    def __init__(self, timestamp, transactions, prevhash='') -> None:
        self.timestamp = timestamp
        self.transactions = transactions,
        self.prev_hash = prevhash,
        self.nonce = 0
        self.hash = self.getHash()
        self.setBlock()
    
    def setBlock(self):
        tmp_tx = []
        for tx in self.transactions:
            for item in tx:
                # if item['type'] == 'init_tx':
                #     tmp_tx.append(tx)
                # if item['type'] == 'block_tx':
                #     tmp_tx.append(item.tx_item)
                tmp_tx.append(item.tx_item)


        self.block_item = {
            "timestamp": str(self.timestamp),
            "transactions": tmp_tx,
            "prev_hash": self.prev_hash,
            "hash": self.hash
        }

    def getHash(self):
        str_val = str(self.timestamp) + str(self.transactions) + str(self.prev_hash) + str(self.nonce)
        return hashlib.sha256(str_val.encode()).hexdigest()

    def mineBlock(self, dif):
        dif_str = "".join(["0" for x in range(dif)])
        while self.hash[:dif] != dif_str:
            self.nonce +=1
            self.hash = self.getHash()
        # print("Block successfull mined!!")
    
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)

    def __str__(self):
        # return {
        #     'timestamp': str(self.block_item['timestamp']),
        #     'transaction': str(self.block_item['transactions']),
        #     'prev_hash':   str(self.block_item['prev_hash'])
        # }
        return self.toJSON()
        


