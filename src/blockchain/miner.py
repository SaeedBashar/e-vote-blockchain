
import math
from time import time
from src.blockchain.block import Block
from src.blockchain import keygen

def mine(chain):
    tmp_txs = chain.tx_to_add_block()
    block = Block(len(chain.chain), time(), tmp_txs, chain.chain[-1].hash, chain.difficulty)
    dif_str = "".join(["0" for x in range(chain.difficulty)])
    while block.hash[:chain.difficulty] != dif_str:
        block.nonce +=1
        block.hash = block.get_hash()
    block.set_block()

    return block