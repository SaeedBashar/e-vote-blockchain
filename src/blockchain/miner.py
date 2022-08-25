
import math
from time import time
from src.blockchain.block import Block
from src.blockchain import keygen
from database.database import Database as db

def mine(chain):
    tmp_txs = chain.tx_to_add_block()
    if len(tmp_txs) != 0:
        length = len(db.get_data('blocks'))
        block = Block(length, time(), tmp_txs, chain.chain[-1].hash, chain.difficulty)
        dif_str = "".join(["0" for x in range(chain.difficulty)])
        while block.hash[:chain.difficulty] != dif_str:
            block.nonce +=1
            block.hash = block.get_hash()
        block.set_block()

        # Remove txs from non mined to mined txs
        chain_len = len(chain.chain)
        for t in tmp_txs:
            db.add_to_mined_tx(chain_len, t)
            chain.transactions = list(filter(lambda tx: tx not in tmp_txs, chain.transactions))

        return block
    return None