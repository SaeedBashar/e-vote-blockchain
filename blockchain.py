
from time import time


from block import Block
from transaction import Transaction


##################################
### Blockchain Class

class Blockchain():
    def __init__(self) -> None:
        self.chain : list(Block) = []
        self.dif = 4
        self.pending_tx = []
        self.add_block([Transaction(0, 0, 0, 0, 'init_tx')])

    def add_block(self, tx_arr):
        block: Block = Block(time(), tx_arr)
        block.prev_hash = self.chain[-1].hash if len(self.chain) != 0 else 0x0
        block.mineBlock(self.dif)
        block.setBlock()

        self.chain.append(block)

    def add_transaction(self, tx:Transaction):
        self.pending_tx.append(tx)

    def tx_to_add_block(self):
        tmp_tx = []

        while len(tmp_tx) < 2 and len(self.pending_tx) > 0 : # #2 num of tx to add to block
            tmp = self.pending_tx[0]
            tmp_i = 0
            for i, t in enumerate(self.pending_tx):
                if t.timestamp < int(tmp.timestamp):
                    tmp_i = i
            tmp_tx.append(self.pending_tx[tmp_i])
            self.pending_tx.pop(tmp_i)
        return tmp_tx

    def is_chain_valid(self, chain: list[Block]):
        prev_block = chain[0]
        cur_block_i = 1

        while cur_block_i < len(chain):
            block = chain[cur_block_i]
            if block.prev_hash != prev_block.hash:
                return False
            if block.hash != block.getHash():
                return False
            
            cur_block_i += 1
            prev_block = block

        return True