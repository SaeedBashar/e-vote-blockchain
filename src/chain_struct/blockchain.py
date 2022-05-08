
import time as tm
from time import time
from urllib.parse import urlparse
import threading

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
        # self.nodes_list = set()
        # self.add_block([Transaction(0, 0, {'fv':0, 'pv':0}, 'init_tx')])

    def add_block(self, tx_arr):
        block: Block = Block(time(), tx_arr)
        block.prev_hash = self.chain[-1].hash if len(self.chain) > 1 else self.chain[-1]['hash']
        block.mine_block(self.dif)

        self.chain.append(block)

    def add_transaction(self, t, va, cand):
        tx = Transaction(t, va, cand)
        self.pending_tx.append(tx)

    def tx_to_add_block(self):
        tmp_tx = []
        max_limit = 2
        counter = 0

        while counter < len(tmp_tx) < max_limit or len(self.pending_tx) == 0 : 
            tmp = self.pending_tx[0]
            tmp_i = 0
            for i, t in enumerate(self.pending_tx):
                if t.timestamp < int(tmp.timestamp):
                    tmp_i = i
            tmp_tx.append(self.pending_tx[tmp_i])
            self.pending_tx.pop(tmp_i)
        return tmp_tx

    # def add_node(self, addr):
    #     parsed_url = urlparse(addr)
    #     self.nodes_list.add(parsed_url.netloc)

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

        conn.response_data = None
        conn.cont = False
        node.send_to_node(node_with_longest_chain, 
                          {
                              'type': 'chain_request', 
                              'client_chain_length': len(node.blockchain.chain),
                              'last_block_hash': node.blockchain.chain[-1].hash if len(node.blockchain.chain) > 1 else node.blockchain.chain[-1]['hash']
                          },
                          'bzip2'
                        )
        return True
            
        # TODO: Possible alternative
        # network = node_conn_list
        # longest_chain = None
        # max_length = len(node.blockchain.chain)
        # for conn in network:
        #     response = rq.get(f'http://{conn.addr}:{conn.port}/get_chain')
        #     if response.status_code == 200:
        #         length = int(response.json()['length'])
        #         chain = response.json()['chain']
        #         if length > max_length and self.is_chain_valid(chain):
        #             max_length = length
        #             longest_chain = chain
        # if longest_chain:
        #     self.chain = longest_chain
        #     return True
        # return False

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