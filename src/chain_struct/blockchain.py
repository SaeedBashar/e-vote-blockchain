
from time import time
from urllib.parse import urlparse
import requests as rq

from src.chain_struct.block import Block
from src.chain_struct.transaction import Transaction


##################################
### Blockchain Class

class Blockchain():
    def __init__(self) -> None:
        self.chain : list(Block) = [{
            'hash': '0000aa8a027447a360b8884f1f80f3b467a4c52182a25469e95710a5cabec4f7',
            'prev_hash': '0',
            'timestamp': '0',
            'transactions': [Transaction(0, 0, {'fv':0, 'pv':0}).tx_item]
        }]
        self.dif = 4
        self.pending_tx = []
        self.nodes_list = set()
        # self.add_block([Transaction(0, 0, {'fv':0, 'pv':0}, 'init_tx')])

    def add_block(self, tx_arr):
        block: Block = Block(time(), tx_arr) if len(self.chain) != 0 else Block(0, tx_arr)
        block.prev_hash = self.chain[-1].hash if len(self.chain) != 0 else 0x0
        block.mineBlock(self.dif)
        block.setBlock()

        self.chain.append(block)

    def add_transaction(self, t, va, cand):
        tx = Transaction(t, va, cand)
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

    def add_node(self, addr):
        parsed_url = urlparse(addr)
        self.nodes_list.add(parsed_url.netloc)

    def replace_chain(self):
        network = self.nodes_list
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = rq.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = int(response.json()['length'])
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False

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