
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
import ast

from src.wallet.wallet import Wallet as wlt
from src.blockchain_node.node_connection import Node_connection
from src.blockchain.blockchain import Blockchain
from src.blockchain.block import Block
from src.blockchain.transaction import Transaction
from src.blockchain import miner

from database.database import Database as db

class Node(threading.Thread):
    def __init__(self, address, port, max_connections=10):
        super(Node, self).__init__()
        
        self.address = address
        self.port = port
        self.max_connections = max_connections

        self.public_key = None 

        self.opened_connection = []
        self.connected_nodes = []

        self.nodes_inbound: list[Node_connection] = []  
        self.nodes_outbound: list[Node_connection] = []


        self.terminate_flag = threading.Event()
        self.blockchain = Blockchain()
        self.temporary_chain = [self.blockchain.chain[0]]

        self.enable_mining = True
        self.enable_logging = True
        self.enable_chain_request = True

        # SPECIAL VARIABLES USED LATER

        # A variable used to signal the template(Html interface) that synchronization is complete
        self.sync_finished = False
        
        # A variable used to hold a dict of responded nodes during synchronization
        self.length_response = []

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.init_server()

    @property
    def all_nodes(self):

        tmp_nodes = []
        tmp = {}
        all_nodes = set(self.nodes_inbound + self.nodes_outbound)
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
        keys = wlt.generate_key()
        self.private_key = keys['private_key']
        self.public_key = keys['public_key']

        return keys

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
        status = self.blockchain.add_transaction(trans, self.send_to_nodes)
        
        return status

    def start_mining(self):
        # thread_list = [x for x in threading.enumerate()]
        thread_names = [x.getName() for x in threading.enumerate()]
        
        try:
            if 'MinerThread' in thread_names:

                return {"status": True, "msg": "Miner is already running..."}
            
            else:
                
                mined_block = self.blockchain.start_miner(self.public_key, self.send_to_nodes)
                
                if mined_block != None:
                    self.blockchain.chain.append(mined_block)
                    db.add_block(mined_block)

                    if len(self.blockchain.chain) % 10 == 0:
                        self.blockchain.difficulty = self.blockchain.difficulty + 1
                

                    data = {'type': 'NEW_BLOCK_REQUEST', 'block': mined_block.block_item}
                    self.send_to_nodes(data, [])

                    return {"status": True, "msg": "A New Block Has Been Mined!!"}
                else:
                    return {"status": True, "msg": "No Transactions Available!!!"}

        except Exception as e:
            print(e)
            return {"status": False, "msg": "Could not start miner..."}

    def connect_with_node(self, address, port):
        if address == self.address and port == self.port:
            self.log("[SELF CONNECTION]: Can not connect to yourself!!")
            return {
                "status": False,
                'msg': '[SELF CONNECTION]: Can not connect to yourself!!'
            }
        for node in self.nodes_outbound:
            # for node in self.connected_nodes:
            if node.address == address and node.port == port:
                self.log(f"[EXISTING CONNECTION]: Already connected to node {address}:{port}")
                return {
                    "status": False,
                    "msg": f"[EXISTING CONNECTION]: Already connected to node {address}:{port}"
                }

        try:
            self.public_key = db.get_pk()[0][0]
            if self.public_key != "":
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.log("[CONNECTING]: Connecting to node %s:%s..." % (address, port))
                sock.connect((address, int(port)))

                sock.send((self.public_key + ":" + str(self.port)).encode('utf-8')) 
                connected_node_pk = sock.recv(4096).decode('utf-8')
                for node in self.nodes_inbound:
                    # for node in self.connected_nodes:
                    if node.address == address and node.pk == connected_node_pk:
                        self.log(f"[EXISTING CONNECTION]: Already connected to node {address}:{port}")
                        sock.send("[CLOSING]: Closing, connection exist already".encode('utf-8'))
                        sock.close()
                        return {
                                "status": False,
                                "msg": f"[EXISTING CONNECTION]: Already connected to node {address}:{port}"
                            }
                thread_client = self.create_new_connection(sock, connected_node_pk, address, port)
                thread_client.start()
                self.nodes_outbound.append(thread_client)
                # self.connected_nodes.append(thread_client)
                status = db.add_connection(thread_client)
                
                if status:
                    self.log("[CONNECTED]: Connected to node %s:%s..." % (address, port))
                return {"status": True, "msg": "Connected Successfully"}
            else:
                return {"status": False, "msg": "Failed to Connect. Please make sure you have a public key"}

        except Exception as e:
            self.log("[CONNECTION ERROR]: Could not connect with node. (" + str(e) + ")")
            return {
                'status': False,
                'msg': '[CONNECTION ERROR]: Could not connect with node'
            }
        
    def node_message(self, node_conn, data):
        
        # self.log(json.dumps(data))

        keys_in_data = [x[1] for x in enumerate(data)]

        if 'type' in keys_in_data:
            if data['type'] == 'NEW_TRANSACTION_REQUEST':
                transaction = data['transaction']
                transaction['args'] = ast.literal_eval(str(transaction['args']))
                self.blockchain.add_transaction(transaction, self.send_to_nodes, node_conn)
            
            elif data['type'] == "NEW_BLOCK_REQUEST":
                # "NEW_BLOCK_REQUEST" is sent when someone wants to submit a new block.
                # Its message body must contain the new block.

                n_block = data['block']
                # n_block['data'] = ast.literal_eval(str(n_block['data']))
                n_block['data'] = json.loads(str(n_block['data']))
                return_data = self.blockchain.add_block(n_block)

                if return_data['status']:
                   
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
                        if Transaction.is_valid(tx):
                            tmp =  Transaction(
                                    tx['from_addr'],
                                    tx['to_addr'],
                                    tx['value'],
                                    tx['gas'],
                                    tx['args'],
                                    tx['timestamp']
                                )
                            tmp.tx_hash = tx['tx_hash']
                            tmp.set_transaction()

                            tmp_txs.append(tmp)
                            db.add_to_mined_tx(n_block['index'], tmp)
                    
                    
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
                    tmp_block.set_block()

                    if not data['finished']:
                        self.temporary_chain.append(tmp_block)
                    else:
                        self.temporary_chain.append(tmp_block)

                        is_chain_valid = True
                        dif = 4

                        for i in range(1, len(self.temporary_chain) - 1):
                            cur_block = self.temporary_chain[i]
                            pre_block = self.temporary_chain[i-1]

                         
                            if not Block.is_valid(cur_block.block_item, pre_block.block_item):
                                is_chain_valid = False


                            # if is_chain_valid:
                            #     if int(n_block['index']) % 100 == 0:
                            #         dif = math.ceil(self.difficulty * 100 * self.block_time / (int(n_block['timestamp']) - int(self.chain[len(self.chain)-99].timestamp)))

                            # else:
                            #     break

                        if is_chain_valid:
                            self.blockchain.chain = self.temporary_chain
                            self.blockchain.difficulty = self.temporary_chain[-1].difficulty

                            
                            request_data = {
                                'type': 'NON_MINED_TRANSACTION_REQUEST'
                            }
                            node_conn.send(request_data, compression='bzip2')

                            request_data = {
                                'type': 'STATE_REQUEST'
                            }
                            node_conn.send(request_data, compression='bzip2')
                            
                            self.temporary_chain = []
                            self.enable_chain_request = False
                        else:
                            self.log("[INVALID] Chain is invalid")
                            
            elif data['type'] == 'CHAIN_LENGTH_REQUEST':
                
                chain_len = len(self.blockchain.chain)
                latest_block = self.blockchain.chain[-1]

                response_data = {
                    'type': 'CHAIN_LENGTH_RESPONSE',
                    'length': chain_len,
                    'block': latest_block.block_item
                }

                node_conn.send(response_data)

            elif data['type'] == 'CHAIN_LENGTH_RESPONSE':
                tmp = {
                    'length': data['length'],
                    'block': data['block'],
                    'node_conn': node_conn
                }

                self.length_response.append(tmp)

            elif data['type'] == 'STATE_REQUEST':

                response_data = {
                        'type': 'STATE_RESPONSE',
                        'state': db.get_data('states')
                    }
                node_conn.send(response_data, compression='bzip2')

            elif data['type'] == 'STATE_RESPONSE':
                for st in data['state']:
                    db.add_to_state(st)
                    db.update_state_cont(st, data['state'][st])
                
                # A variable used to signal the template(Html interface) that synchronization is complete
                self.sync_finished = True

            elif data['type'] == 'MINED_TRANSACTION_REQUEST':
                tmp_txs = []
                r_data = db.get_data('mined_transactions')
                for tx in r_data:
                    tmp_txs.append({
                        "block_index": tx[0],
                        "from_addr": tx[1],
                        "to_addr": tx[2],
                        "value": tx[3],
                        "gas": tx[4],
                        "args": json.loads(tx[5]),
                        "timestamp": tx[6],
                        "tx_hash": tx[7]
                    })
                
                request_data = {
                                'type': 'MINED_TRANSACTION_RESPONSE',
                                'transactions': tmp_txs
                            }
                node_conn.send(request_data, compression='bzip2')

            elif data['type'] == 'MINED_TRANSACTION_RESPONSE':
                for t_item in data['transactions']:
                    tmp = Transaction(
                                    t_item['from_addr'],
                                    t_item['to_addr'],
                                    t_item['value'],
                                    t_item['gas'],
                                    t_item['args'],
                                    t_item['timestamp']
                                )
                    tmp.tx_hash = t_item['tx_hash']
                    tmp.set_transaction()
                    
                    db.add_to_mined_tx(t_item['block_index'], tmp)

            elif data['type'] == 'NON_MINED_TRANSACTION_REQUEST':
                tmp_txs = []
                r_data = db.get_data('transactions')
                for tx in r_data:
                    tmp_txs.append({
                        "from_addr": tx[0],
                        "to_addr": tx[1],
                        "value": tx[2],
                        "gas": tx[3],
                        "args": json.loads(tx[4]),
                        "timestamp": tx[5],
                        "tx_hash": tx[6]
                    })
                
                request_data = {
                                'type': 'NON_MINED_TRANSACTION_RESPONSE',
                                'transactions': tmp_txs
                            }
                node_conn.send(request_data, compression='bzip2')

            elif data['type'] == 'NON_MINED_TRANSACTION_RESPONSE':
                for t_item in data['transactions']:
                    tmp = Transaction(
                                    t_item['from_addr'],
                                    t_item['to_addr'],
                                    t_item['value'],
                                    t_item['gas'],
                                    t_item['args'],
                                    t_item['timestamp']
                                )
                    tmp.tx_hash = t_item['tx_hash']
                    tmp.set_transaction()

                    self.blockchain.transactions.append(tmp)
                    db.add_transaction(tmp)

        self.log("[RECEIVED MESSAGE]: Data from node %s:[%s]" % (node_conn.address, str(data)))

    def send_to_nodes(self, data, exclude=[], compression='none'):
        
        for n in self.nodes_inbound:
            if n.pk in exclude:
                self.log(f"[EXCLUSION] Node {n.address}:{n.port} is excluded")
            else:
                self.send_to_node(n, data, compression)

        for n in self.nodes_outbound:
            if n.pk in exclude:
                self.log(f"[EXCLUSION] Node {n.address}:{n.port} is excluded")
            else:
                self.send_to_node(n, data, compression)

    def send_to_node(self, n, data, compression='none'):

        if n in self.nodes_inbound or n in self.nodes_outbound:
             n.send(data, compression=compression)
            # if n in self.connected_nodes:
            #     n.send(data, compression=compression)
        else:
            self.log(f"[UNKNOWN NODE]: Do not have connection with node {n.address}:{n.port}!!")
    
    def sync_chain(self):
        try:
            network = []
            for n in self.nodes_inbound + self.nodes_outbound:
                for nd in network:
                    if n.address == nd.address and n.port == nd.port:
                        break
                else:
                    network.append(n)
                
            if len(network) != 0:
                for conn in network:
                    request_data = {'type':'CHAIN_LENGTH_REQUEST'}
                    self.send_to_node(conn, request_data)
                
                # Delay execution to allow all nodes to send feedback
                time.sleep(0.3)
                node_with_longest_chain = max(self.length_response, key=lambda x : int(x['length']))
                
                if len(self.blockchain.chain) < int(node_with_longest_chain['length']):
                    request_data = {'type':'CHAIN_REQUEST'}
                    node_with_longest_chain['node_conn'].send(request_data)
                    return {'status': True, 'message': 'Sychronization has began...!!!\nPlease wait while all required data are being updated.'}
                
                else:
                    return {'status': False, 'message': 'Chain is already up to date with the network!!'}

            else:
                return {'status': False, 'message': 'Please make sure you are connected to at least one node!!!'}
        
        except Exception as e:
            return {'status': False, 'message': 'An Error Occured While Trying to Synchronize!!!'}
    
    def stop(self):
        self.terminate_flag.set()

    def run(self):
        while not self.terminate_flag.is_set():
            try:
                self.log("[WAITING]: Waiting for incoming connection...")
                connection, client_address = self.sock.accept()
                self.log("[RECEIVED]: New connection received.")

                if len(self.nodes_inbound) > self.max_connections:
                # if len(self.connected_nodes) > self.max_connections:
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
                    
                    if self.public_key == None:
                        # Get and instantiate public key of the node
                        r_data = db.get_pk()
                        self.public_key = r_data[0][0]

                    connection.send(self.public_key.encode('utf-8')) 
                    # connection.send(self.id.encode('utf-8')) 

                    thread_client = self.create_new_connection(connection, connected_node_pk, client_address[0], connected_node_port)
                    thread_client.start()

                    self.nodes_inbound.append(thread_client)
                    # self.connected_nodes.append(thread_client)
                    # db.add_connection(thread_client)


            except socket.timeout:
                    self.log('Node: Connection timeout!')

            except Exception as e:
                    raise e
        
        self.log("[STOPPING] Node stopping....")
        for t in self.nodes_inbound:
            t.stop()

        for t in self.nodes_outbound:
            t.stop()
        # for n in self.connected_nodes:
        #     n.stop()

        for t in self.nodes_inbound:
            t.join()

        for t in self.nodes_outbound:
            t.join()

        # for n in self.connected_nodes:
        #     n.join()

        time.sleep(3)
        self.sock.close()
        self.log("[TERMINATED] Node stopped...")