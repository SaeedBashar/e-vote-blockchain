
import binascii
import math
import socket
from sre_parse import State
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
from src.blockchain_node.node_connection import Node_connection
from src.blockchain.blockchain import Blockchain
from src.blockchain.block import Block
from src.blockchain.transaction import Transaction
from src.blockchain import miner

# Variables for testing purposes
temp_state = {
    "state": {"30819f300d06092a864886f70d010101050003818d0030818902818100a9433cc207ef9a748188014eddf20d12433c3b15f4c1827fa6fff37061887de1a9ebb8f58821402c35aedf2a195bcf1bc5b6ea7d0a45f5bcc81a9b2fe1ec693c881aa0ad1a69dd81cd4f985ec30526885a0a629ccd6e630d9152a96b42e6b8d0df305b918d50c60ce4fe9d6694746b4343e6fc93fa5e0def1bef06098a2cad2f0203010001":
                   {
                    "balance":100000000000,
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
        self.temporary_chain = [self.blockchain.chain[0]]

        is_mined = False
        self.enable_mining = True
        self.enable_logging = True
        self.enable_chain_request = True

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.init_server()

    @property
    def all_nodes(self):
        tmp_nodes = []
        tmp = {}
        all_nodes = self.connected_nodes
        if all_nodes != []:
            for n in all_nodes:
                tmp['address'] = n.address
                tmp['port'] = n.port
                tmp['public_key'] = n.pk
                
                tmp_nodes.append(tmp)
            return tmp_nodes
        else:
            return 'No connected node'

    def gen_key_pair(self):
        keys = keygen.gen_key_pair()
        self.private_key = keys['private_key']
        self.public_key = keys['public_key']
        self.key_pair = keys['key_pair']

    def init_server(self):
        print("[INITIALIZATION] Node initializing...")
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.address, self.port))
        # self.sock.settimeout(10.0)
        self.sock.listen()
        print(f"[LISTENING] Node listening on {self.address}:{self.port}")

    def log(self, msg):
        if self.enable_logging:
            print(msg)

    def create_new_connection(self, connection, id, address, port):
        return Node_connection(self, connection, id, address, port)

    def make_transaction(self, trans):
        status = self.blockchain.add_transaction(trans, self.send_to_nodes, temp_state['state'])
        
        return status

    def start_mining(self):
        thread_list = [x for x in threading.enumerate()]
        thread_names = [x.getName() for x in threading.enumerate()]
        # for t in thread_list:
        # if 'MinerThread' == t.getName():
        #     pass
        try:
            if 'MinerThread' in thread_names:
                return {"status": True, "msg": "Miner is already running..."}
            else:
                mined_block = self.blockchain.start_miner()

                self.blockchain.chain.append(mined_block)

                temp_state['state'] = change_state(mined_block, temp_state['state'])

                print("We got here")

                trigger_contract(self.blockchain.chain[-1], temp_state['state'], self.blockchain, self.enable_logging)
                
                print("here too")

                data = {'type': 'NEW_BLOCK_REQUEST', 'block': mined_block.block_item}
                self.send_to_nodes(data, [])

                return {"status": True, "msg": "Miner has mined a new block..."}
        except Exception as e:
            print(e)
            return {"status": False, "msg": "Could not start miner..."}

    def connect_with_node(self, address, port, reconnect=False):
        if address == self.address and port == self.port:
            self.log("[SELF CONNECTION]: Can not connect to yourself!!")
            return False

        for node in self.connected_nodes:
            if node.address == address and node.port == port:
                self.log(f"[EXISTING CONNECTION]: Already connected to node {address}:{port}")
                return True

        try:
            if self.public_key != "":
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.log("[CONNECTING]: Connecting to node %s:%s..." % (address, port))
                sock.connect((address, port))

                sock.send((self.public_key + ":" + str(self.port)).encode('utf-8')) 
                connected_node_pk = sock.recv(4096).decode('utf-8')

                for node in self.connected_nodes:
                    if node.address == address and node.pk == connected_node_pk:
                        self.log(f"[EXISTING CONNECTION]: Already connected to node {address}:{port}")
                        sock.send("[CLOSING]: Closing, connection exist already".encode('utf-8'))
                        sock.close()
                        return True

                thread_client = self.create_new_connection(sock, connected_node_pk, address, port)
                thread_client.start()

                return {"status": True, "msg": "Connected Successfully"}
            else:
                return {"status": False, "msg": "Failed to Connect. Please make sure you have a public key"}

        except Exception as e:
            self.log("[CONNECTION ERROR]: Could not connect with node. (" + str(e) + ")")
            return False

             
    def node_message(self, node_conn, data):

        self.log(json.dumps(data))

        keys_in_data = [x[1] for x in enumerate(data)]

        if 'type' in keys_in_data:
            if data['type'] == 'NEW_TRANSACTION_REQUEST':
                transaction = data['transaction']

                self.blockchain.add_transaction(transaction, temp_state['state'], self.send_to_nodes, node_conn)
                    
            elif data['type'] == 'LATEST_BLOCK_REQUEST':
                node_conn.send({'msg': 'success'})
            elif data['type'] == "NEW_BLOCK_REQUEST":
                # "NEW_BLOCK_REQUEST" is sent when someone wants to submit a new block.
                # Its message body must contain the new block.

                n_block = data['block']

                return_data = self.blockchain.add_block(n_block, temp_state['state'])

                if return_data['success']:
                    temp_state['state'] = change_state(return_data['new_block'], temp_state['state'])

                    trigger_contract(self.blockchain.chain[-1], temp_state['state'], self.blockchain, self.enable_logging)

                    data = {'type': 'NEW_BLOCK_REQUEST', 'block': return_data['new_block'].block_item}
                    self.send_to_nodes(data, [node_conn.pk])
                    self.enable_mining = False

            elif data['type'] == 'CHAIN_REQUEST':
                for i, b in enumerate(self.blockchain.chain):
                    response_data = {
                        'type': 'CHAIN_RESPONSE',
                        'finished': i == len(self.blockchain.chain) - 1,
                        'block': b.block_item
                    }

                    node_conn.send(response_data, compression='bzip2')
            
            elif data['type'] == 'CHAIN_RESPONSE':
                if self.enable_chain_request:
                    n_block = data['block']
                    tmp_txs = []
                    for tx in n_block['data']:
                        if Transaction.is_valid(tx, temp_state['state']):
                            tmp_txs.append(
                                Transaction(
                                    tx['from_addr'],
                                    tx['to_addr'],
                                    tx['value'],
                                    tx['gas'],
                                    tx['args'],
                                    tx['timestamp']
                                )
                            )
                    
                    tmp_block = Block(
                        n_block['index'],
                        n_block['timestamp'],
                        tmp_txs,
                        n_block['prev_hash'],
                        n_block['difficulty']
                    )
                    tmp_block.hash = n_block['hash']
                    tmp_block.merkle_root = n_block['merkle_root']
                    tmp_block.nonce = n_block['nonce']
                    tmp_block.prev_hash = n_block['prev_hash']

                    if not data['finished']:
                        self.temporary_chain.append(tmp_block)
                    else:
                        self.temporary_chain.append(tmp_block)

                        is_chain_valid = True
                        dif = 1
                        initial_state = {"30819f300d06092a864886f70d010101050003818d0030818902818100a9433cc207ef9a748188014eddf20d12433c3b15f4c1827fa6fff37061887de1a9ebb8f58821402c35aedf2a195bcf1bc5b6ea7d0a45f5bcc81a9b2fe1ec693c881aa0ad1a69dd81cd4f985ec30526885a0a629ccd6e630d9152a96b42e6b8d0df305b918d50c60ce4fe9d6694746b4343e6fc93fa5e0def1bef06098a2cad2f0203010001":
                            {
                            "balance":100000000000,
                            "body":"",
                            "timestamps":[],
                            "storage":{}
                            }
                        }

                        for i in range(1, len(self.temporary_chain) - 1):
                            cur_block = self.temporary_chain[i]
                            pre_block = self.temporary_chain[i-1]

                            if SHA256.new(cur_block.index + 
                            cur_block.timestamp + 
                            json.dumps(cur_block.block_item['data']) +
                            cur_block.difficulty+
                            pre_block.hash + 
                            cur_block.nonce + 
                            cur_block.merkle_root
                            ) != cur_block.hash:
                                self.log("Failed first test")
                                is_chain_valid = False

                            # TODO:: temp_state will be checked later
                            if not Block.has_valid_transactions(cur_block, temp_state['state']):
                                self.log("Failed second test")
                                is_chain_valid = False

                            if int(cur_block.timestamp) > time() or int(cur_block.timetamp) < int(pre_block.timestamp):
                                self.log("Failed third test")
                                is_chain_valid = False

                            if cur_block.prev_hash != pre_block.hash:
                                self.log("Failed forth test")
                                is_chain_valid = False

                            if int(cur_block.index) - 1 != pre_block.index:
                                self.log("Failed fifth test")
                                is_chain_valid = False

                            if cur_block.difficulty != dif:
                                self.log("Failed sixth test")
                                is_chain_valid = False


                            if is_chain_valid:
                                if int(n_block['index']) % 100 == 0:
                                    dif = math.ceil(self.difficulty * 100 * self.block_time / (int(n_block['timestamp']) - int(self.chain[len(self.chain)-99].timestamp)))
                                    
                                initial_state = change_state(cur_block, initial_state)
                                trigger_contract(cur_block, initial_state)
                            else:
                                break

                        if is_chain_valid:
                            self.blockchain.chain = self.temporary_chain
                            self.blockchain.difficulty = dif
                            temp_state['state'] = initial_state

                            self.temporary_chain = []
                            self.enable_chain_request = False
                        else:
                            self.log("[INVALID] Chain is invalid")
                            

        self.log("[RECEIVED MESSAGE]: Data from node %s:[%s]" % (node_conn.address, str(data)))


    def send_to_nodes(self, data, exclude=[], compression='none'):
        
        for n in self.connected_nodes:
            if n.pk in exclude:
                self.log(f"[EXCLUSION] Node {n.address}:{n.port} is excluded")
            else:
                self.send_to_node(n, data, compression)


    def send_to_node(self, n, data, compression='none'):

        if n in self.connected_nodes:
            n.send(data, compression=compression)
        else:
            self.log(f"[UNKNOWN NODE]: Do not have connection with node {n.address}:{n.port}!!")
    
    def extract_chain_part(self, b_index):
        tmp_chain_part = []
        tmp_index = None
        for block in enumerate(self.blockchain.chain):
            if block[1].index == b_index:
                tmp_index = block[0]
                break

        for block in self.blockchain.chain[tmp_index : ]:
            tmp_chain_part.append(block.block_item)

        return tmp_chain_part

    def stop(self):
        self.terminate_flag.set()

    def run(self):
        while not self.terminate_flag.is_set():
            try:
                self.log("[WAITING]: Waiting for incoming connection...")
                connection, client_address = self.sock.accept()
                self.log("[RECEIVED]: New connection received.")


                if len(self.connected_nodes) > self.max_connections:
                    self.log("[LIMIT]. You have reached the maximum connection limit!")
                    connection.close()
                else:
                    connected_node_port = 5000
                    connected_node_pk   = connection.recv(4096).decode('utf-8')
                    
                    if ":" in connected_node_pk:
                        if len(connected_node_pk.split(':')) == 2:
                            (connected_node_pk, connected_node_port) = connected_node_pk.split(':')
                        else:
                            print(connected_node_pk + "No pk here")
                    
                    connection.send(self.public_key.encode('utf-8')) 
                    # connection.send(self.id.encode('utf-8')) 

                    thread_client = self.create_new_connection(connection, connected_node_pk, client_address[0], connected_node_port)
                    thread_client.start()

                    self.connected_nodes.append(thread_client)


            except socket.timeout:
                    self.log('Node: Connection timeout!')

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