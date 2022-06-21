
import json
import time as tm
from pprint import pprint
from time import time
from urllib.parse import urlparse
import threading
import requests as rq

from src.blockchain.block import Block
from src.blockchain.transaction import Transaction


##################################
### Blockchain Class

class Blockchain():
    def __init__(self) -> None:
        self.chain : list(Block) = []
        self.dif = 4
        self.pending_tx = []
        self.create_genesis_block()
      
    def create_genesis_block(self):
        block = Block('123456789',[])
        block.prev_hash = '0' * 64
        block.mine_block(self.dif)
        self.chain.append(block)

    def add_block(self, tx_arr):
        block: Block = Block(time(), tx_arr)
        block.prev_hash = self.chain[-1].hash
        block.mine_block(self.dif)

        self.chain.append(block)

    def add_transaction(self, t, va, cand):
        tx = Transaction(t, va, cand)
        self.pending_tx.append(tx)

    def tx_to_add_block(self):
        tmp_tx = []
        max_limit = 2
        counter = 0

        # while counter < len(tmp_tx) < max_limit or len(self.pending_tx) == 0 : 
        while counter < max_limit and len(self.pending_tx) != 0 : 
            tmp = self.pending_tx[0]
            tmp_i = 0
            for i, t in enumerate(self.pending_tx):
                if t.timestamp < int(tmp.timestamp):
                    tmp_i = i
            tmp_tx.append(self.pending_tx[tmp_i])
            self.pending_tx.pop(tmp_i)
            counter += 1
        return tmp_tx

    def replace_chain(self, node, node_conn_list):
        network = node_conn_list
       
        responded_nodes = []

        for conn in network:
            request_data = {'type':'chain_length_request'}
            node.send_to_node(conn, request_data)
            tm.sleep(0.5)

            if conn.response_data is None:
                continue
            else:
                print("%s responded with a length of %s" % (conn.addr, conn.response_data['length']))
                responded_nodes.append(conn)

        
        if len(responded_nodes) != 0:
            node_with_longest_chain = max(responded_nodes, key=lambda x: x.response_data['length'])
        else:
            print("None of the nodes responded")
            return False

        conn = node_with_longest_chain
        
        #TODO:: replace the get request with a post request
        payload = {'hash': node.blockchain.chain[-1].hash}
        response = rq.get(f'http://{conn.addr}:{str(int(conn.port) - 1000)}/get_chain', params=payload)

        if response.status_code == 200:
                
                chain = response.json()['chain']
                tmp_chain = []
                try:
                    for b_item in chain:
                        tmp_txs = []
                        for t_item in b_item['transactions']:
                            tmp_txs.append(Transaction(
                                                        t_item['timestamp'],
                                                        t_item['voter_addr'],
                                                        t_item['voted_candidates']
                                                    )
                                        )

                        tmp_block = Block(
                                            b_item['timestamp'],
                                            tmp_txs,
                                            b_item['prev_hash']
                                    )
                
                        tmp_block.nonce = b_item['nonce']
                        tmp_block.hash = b_item['hash']
                        tmp_block.set_block()

                        tmp_chain.append(tmp_block)
                        
                    else:
                        if self.is_chain_valid(tmp_chain):
                            node.blockchain.chain.extend(tmp_chain)
                            print("Chain is Updated Successfully")
                            return True
                        else:
                            print("Chain is not valid")
                            return False

                    
                except Exception as e:
                    print("An error occured while updating chain")
                    raise e

        return False
                   

    def is_chain_valid(self, chain: list[Block]):
        prev_block = chain[0]
        cur_block_i = 1

        while cur_block_i < len(chain):
            block = chain[cur_block_i]
            if block.prev_hash != prev_block.hash:
                return False
            if block.hash != block.get_hash():
                return False
            
            cur_block_i += 1
            prev_block = block

        return True