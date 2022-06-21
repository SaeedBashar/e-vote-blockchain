
import binascii
import math
import socket
import time
from turtle import isvisible

import Crypto
import Crypto.Random
from Crypto.Hash import  SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

from pathlib import Path
import json
import threading

from src.blockchain import keygen
from src.blockchain.state import change_state, trigger_contract
from src.blockchain_node.node_conn_c import Node_connection
from src.blockchain.blockchain_c import Blockchain
from src.blockchain.block_c import Block
from src.blockchain.transaction_c import Transaction


# Variables for testing purposes
temp_state = {
    "state": {"30819f300d06092a864886f70d010101050003818d0030818902818100a9433cc207ef9a748188014eddf20d12433c3b15f4c1827fa6fff37061887de1a9ebb8f58821402c35aedf2a195bcf1bc5b6ea7d0a45f5bcc81a9b2fe1ec693c881aa0ad1a69dd81cd4f985ec30526885a0a629ccd6e630d9152a96b42e6b8d0df305b918d50c60ce4fe9d6694746b4343e6fc93fa5e0def1bef06098a2cad2f0203010001":
                   {
                    "balance":100000000000000,
                    "body":"",
                    "timestamps":[],
                    "storage":{}
                    }
            }
}

class Node(threading.Thread):
    def __init__(self, address, port, max_connections=10):
        super(Node, self).__init__()
        
        self.address = address
        self.port = port
        self.max_connections = max_connections

        self.private_key = ""
        self.public_key = ""
        self.key_pair = None

        self.opened_connection = []
        self.connected_nodes = []


        self.terminate_flag = threading.Event()
        self.blockchain = Blockchain()

        is_mined = False
        self.enable_mining = True
        self.enable_logging = True

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.init_server()

    def gen_key_pair(self):
        keys = keygen.gen_key_pair()
        self.private_key = keys['private_key']
        self.public_key = keys['public_key']
        self.key_pair = keys['key_pair']

    def init_server(self):
        print("[INITIALIZATION] Node initializing...")
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.address, self.port))
        self.sock.settimeout(10.0)
        self.sock.listen()
        print(f"[LISTENING] Node listening on {self.address}:{self.port}")

    def log(self, msg):
        if self.enable_logging:
            print(msg)

    def create_new_connection(self, connection, id, addr, port):
        return Node_connection(self, connection, id, addr, port)

    def node_message(self, node_conn, data):

        self.log(json.dumps(data))

        keys_in_data = [x[1] for x in enumerate(data)]

        if 'type' in keys_in_data:

            if data['type'] == 'LATEST_BLOCK_REQUEST':
                pass
            elif data['type'] == "NEW_BLOCK_REQUEST":
                # "NEW_BLOCK_REQUEST" is sent when someone wants to submit a new block.
                # Its message body must contain the new block and the new difficulty.

                n_block = data['block']
                is_valid_block = False

                if n_block['prev_hash'] != self.blockchain[-1].prev_hash:
                    is_valid_block = True
                    if SHA256.new(n_block['index'] + 
                                    self.blockchain.chain[-1].hash + 
                                    n_block['timestamp'] + 
                                    n_block['data'] +
                                    n_block['nonce'] + 
                                    n_block['difficulty']
                                    ) != n_block['hash']:
                        self.log("Failed first test")
                        is_valid_block = False

                    # TODO:: temp_state will be checked later
                    if not Block.has_valid_transactions(n_block, temp_state['state']):
                        self.log("Failed second test")
                        is_valid_block = False

                    if int(n_block['timestamp']) > time() or int(n_block['timetamp']) < int(self.chain[-1].timestamp):
                        self.log("Failed third test")
                        is_valid_block = False

                    if n_block['prev_hash'] != self.chain[-1].prev_hash:
                        self.log("Failed forth test")
                        is_valid_block = False

                    if n_block['index'] - 1 != self.chain[-1].index:
                        self.log("Failed fifth test")
                        is_valid_block = False

                    if n_block['difficulty'] != self.chain.difficulty:
                        self.log("Failed sixth test")
                        is_valid_block = False
                        
                if is_valid_block:
                    if n_block['index'] % 100 == 0:
                        self.blockchain.difficulty = math.ceil(self.blockchain.difficulty * 100 * self.blockchain.block_time / (int(n_block['timestamp']) - int(self.blockchain.chain[len(self.blockchain.chain)-99].timestamp)))
                    
                    
                    tmp_txs = []
                    for t_item in n_block['data']:
                        tmp_txs.append(Transaction(
                                                    t_item['from_addr'],
                                                    t_item['to_addr'],
                                                    t_item['value'],
                                                    t_item['gas'],
                                                    t_item['args'],
                                                    t_item['timestamp']
                                                )
                                    )

                    tmp_block = Block(
                                        n_block['index'],
                                        n_block['timestamp'],
                                        tmp_txs,
                                        n_block['difficulty']
                                )

                    tmp_block.hash = n_block['hash']
                    tmp_block.nonce = n_block['nonce']
                    tmp_block.merkle_tree = n_block['merkle_tree']

                    self.blockchain.chain.append(tmp_block)
                    self.blockchain.transactions = filter(lambda tx: Transaction.is_valid(tmp_txs, temp_state['state']))
                    self.log("[NEW BLOCK] New block is added to the chain")

                    change_state(tmp_block, temp_state['state'])

                    trigger_contract(self.blockchain.chain[-1], temp_state, self.blockchain, self.enable_logging)
            
            elif data['type'] == 'chain_request':
                tmp_chain_part = []
                tmp_index = None
                for block in enumerate(self.blockchain.chain):
                    if block[1].hash == data['last_block_hash']:
                        tmp_index = block[0]
                        break

                for block in self.blockchain.chain[tmp_index + 1 : ]:
                    tmp_chain_part.append(block.block_item)

                node_conn.send({
                    'type': 'chain_response',
                    'chain_part': tmp_chain_part, # Only part of the chain is sent
                    'insert_index': tmp_index + 1
                    },
                    compression='bzip2')
            elif data['type'] == 'chain_response':
                node_conn.cont = True
            
                try:
                    for b_item in data['chain_part']:
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
                        tmp_block.hash = b_item['hash']
                        tmp_block.nonce = b_item['nonce']

                        self.blockchain.chain.append(tmp_block)
                    else:
                        print("Chain is Updated Successfully")
                except Exception as e:
                    print("An error occured while updating chain")
                    raise e

                print('From chain response ' + self.blockchain.chain)
    
            elif data['type'] == 'chain_length_request':
                node_conn.send({
                    'type': 'chain_length_response', 
                    'length': len(self.blockchain.chain)})
            elif data['type'] == 'chain_length_response':
                # use to continue replace_chain method in blockchain class
                node_conn.response_data = data
                node_conn.cont = True

        self.debug_print("[RECEIVED MESSAGE]: Data from node %s:[%s]" % (node_conn.addr, str(data)))
        if self.callback is not None:
            self.callback("node_message", self, node_conn, data)


    def run(self):
        while not self.terminate_flag.is_set():
            try:
                self.log("[WAITING]: Waiting for incoming connection...")
                connection, client_address = self.sock.accept()

                if len(self.connected_nodes) > self.max_connections:
                    self.log("[LIMIT]. You have reached the maximum connection limit!")
                    connection.close()
                else:
                    
                    connected_node_pk   = connection.recv(4096).decode('utf-8')
                    
                    if ":" in connected_node_pk:
                        (connected_node_pk, connected_node_port) = connected_node_pk.split(':')

                   
                    connection.send(self.public_key.encode('utf-8')) 
                    # connection.send(self.id.encode('utf-8')) 

                    thread_client = self.create_new_connection(connection, connected_node_pk, client_address[0], connected_node_port)
                    thread_client.start()

                    self.connected_nodes.append(thread_client)


            except socket.timeout:
                    self.debug_print('Node: Connection timeout!')

            except Exception as e:
                    raise e
        
        self.log("[STOPPING] Node stopping....")
        for n in self.connected_nodes:
            n.stop()

        for n in self.connected_nodes:
            n.join()

        time.sleep(3)
        self.sock.close()
        self.log("[TERMINATED] Node stopped...")