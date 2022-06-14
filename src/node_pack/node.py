import json
import socket
import time
import threading
import random
import hashlib
from src.chain_struct.block import Block
from src.chain_struct.transaction import Transaction

from src.node_pack.node_connection import Node_connection
from src.chain_struct.blockchain import Blockchain

class Node(threading.Thread):

    def __init__(self, addr, port, id=None, callback=None, max_connections=10):
        
        super(Node, self).__init__()

        self.addr = addr
        self.port = port

        self.blockchain = Blockchain()

        self.terminate_flag = threading.Event()

        self.callback = callback

        self.nodes_inbound: list[Node_connection] = []  
        self.nodes_outbound: list[Node_connection] = []

        self.reconnect_to_nodes: list[dict] = []

        if id == None:
            self.id = self.generate_id()
        else:
            self.id = str(id) 

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.init_server()

        # Message counters to make sure everyone is able to track the total messages
        self.message_count_send = 0
        self.message_count_recv = 0
        self.message_count_rerr = 0
        
        # Connection limit of inbound nodes (nodes that connect to us)
        self.max_connections = max_connections

        # Debugging on or off!
        self.debug = False

    @property
    def all_nodes(self):
    
        tmp_nodes = []
        tmp = {}
        all_nodes = set(self.nodes_inbound + self.nodes_outbound)
        if all_nodes:
            for n in all_nodes:
                tmp['addr'] = n.addr
                tmp['port'] = n.port
                tmp['id'] = n.id
                
                tmp_nodes.append(tmp)
        return tmp_nodes


    def debug_print(self, message):
        if self.debug:
            print("DEBUG (" + self.id + "): " + message)

    def generate_id(self):
        id = hashlib.sha256()
        t = self.addr + str(self.port) + str(random.randint(1, 99999999)) + time.ctime()
        id.update(t.encode('ascii'))
        return id.hexdigest()

    def init_server(self):
        print("[INITIALIZATION] Node initializing...")
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.addr, self.port))
        self.sock.settimeout(10.0)
        self.sock.listen()
        print(f"[LISTENING] Node listening on {self.addr}:{self.port}")

    def print_connections(self):
        print("Node connection overview:")
        print("[INBOUND CONNECTIONS] Number of nodes connected to us: %d" % len(self.nodes_inbound))
        print("[OUTBOUND CONNECTIONS] Number of nodes we have connected to: %d" % len(self.nodes_outbound))

    def send_to_nodes(self, data, exclude=[], compression='none'):
        
        for n in self.nodes_inbound:
            if n in exclude:
                self.debug_print(f"[EXCLUSION - inbound] Node {n.addr}:{n.port} is excluded")
            else:
                self.send_to_node(n, data, compression)

        for n in self.nodes_outbound:
            if n in exclude:
                self.debug_print(f"[EXCLUSION - outbound] Node {n.addr}:{n.port} is excluded")
            else:
                self.send_to_node(n, data, compression)

    def send_to_node(self, n, data, compression='none'):
        self.message_count_send += 1

        if n in self.nodes_inbound or n in self.nodes_outbound:
            n.send(data, compression=compression)

        else:
            self.debug_print(f"[UNKNOWN NODE]: Do not have connection with node {n.addr}:{n.port}!!")

    def connect_with_node(self, addr, port, reconnect=False):
        if addr == self.addr and port == self.port:
            print("[SELF CONNECTION]: Cannot connect to yourself!!")
            return False

        for node in self.nodes_outbound:
            if node.addr == addr and node.port == port:
                print(f"[EXISTING CONNECTION]: Already connected to node {addr}:{port}")
                return True

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.debug_print("[CONNECTING]: Connecting to node %s:%s..." % (addr, port))
            sock.connect((addr, port))

            sock.send((self.id + ":" + str(self.port)).encode('utf-8')) 
            connected_node_id = sock.recv(4096).decode('utf-8')

            for node in self.nodes_inbound:
                if node.addr == addr and node.id == connected_node_id:
                    print(f"[EXISTING CONNECTION]: Already connected to node {addr}:{port}")
                    sock.send("[CLOSING]: Closing, connection exist already".encode('utf-8'))
                    sock.close()
                    return True

            thread_client = self.create_new_connection(sock, connected_node_id, addr, port)
            thread_client.start()

            self.nodes_outbound.append(thread_client)
            self.outbound_node_connected(thread_client)

            if reconnect:
                self.debug_print("[RECONNECTION]: Reconnection check is enabled on node " + addr + ":" + str(port))
                self.reconnect_to_nodes.append({
                    "addr": addr, "port": port, "trials": 0
                })

            return True

        except Exception as e:
            self.debug_print("[CONNECTION ERROR]: Could not connect with node. (" + str(e) + ")")
            return False


    def disconnect_with_node(self, node):
        if node in self.nodes_outbound:
            self.node_disconnect_with_outbound_node(node)
            node.stop()
        else:
            self.debug_print("[DISCONNECTION ERROR]: There is no connection with the node")

    def stop(self):
        self.node_request_to_stop()
        self.terminate_flag.set()

    def create_new_connection(self, connection, id, addr, port):
        return Node_connection(self, connection, id, addr, port)

    def reconnect_nodes(self):
        for node_to_check in self.reconnect_to_nodes:
            found_node = False
            self.debug_print("[CHECKING]: Checking node " + node_to_check["addr"] + ":" + str(node_to_check["port"]))

            for node in self.nodes_outbound:
                if node.addr == node_to_check["addr"] and node.port == node_to_check["port"]:
                    found_node = True
                    node_to_check["trials"] = 0 
                    self.debug_print("[RUNNING]: Node " + node_to_check["addr"] + ":" + str(node_to_check["port"]) + " still running!")

            if not found_node:
                node_to_check["trials"] += 1

                if self.node_reconnection_error(node_to_check):
                    self.connect_with_node(node_to_check["addr"], node_to_check["port"]) 
                else:
                    self.debug_print("[REMOVING]: Removing node (" + node_to_check["addr"] + ":" + str(node_to_check["port"]) + ") from the reconnection list!")
                    self.reconnect_to_nodes.remove(node_to_check)

    def replace_chain(self):
        connected_nodes = []
      
        for n in self.nodes_inbound + self.nodes_outbound:
            if len(connected_nodes) != 0:
                for nd in connected_nodes:
                    if n.addr == nd.addr and n.port == nd.port:
                        break
                else:
                    connected_nodes.append(n)
            else:
                connected_nodes.append(n)

        chain_replaced = self.blockchain.replace_chain(self, connected_nodes)
    
        return chain_replaced

    def extract_chain_part(self, b_hash):
        tmp_chain_part = []
        tmp_index = None
        for block in enumerate(self.blockchain.chain):
            if block[1].hash == b_hash:
                tmp_index = block[0]
                break

        for block in self.blockchain.chain[tmp_index + 1 : ]:
            tmp_chain_part.append(block.block_item)

        return tmp_chain_part
        
    def run(self):
        while not self.terminate_flag.is_set(): 
            try:
                self.debug_print("[WAITING]: Waiting for incoming connection...")
                connection, client_address = self.sock.accept()

                self.debug_print("Total inbound connections:" + str(len(self.nodes_inbound)))

                if len(self.nodes_inbound) <= self.max_connections:
                    connected_node_port = client_address[1] 
                    connected_node_id   = connection.recv(4096).decode('utf-8')
                    
                    if ":" in connected_node_id:
                        (connected_node_id, connected_node_port) = connected_node_id.split(':') 
                    connection.send(self.id.encode('utf-8')) 

                    thread_client = self.create_new_connection(connection, connected_node_id, client_address[0], connected_node_port)
                    thread_client.start()

                    self.nodes_inbound.append(thread_client)
                    self.inbound_node_connected(thread_client)

                else:
                    self.debug_print("[LIMIT]. You have reached the maximum connection limit!")
                    connection.close()
            
            except socket.timeout:
                self.debug_print('Node: Connection timeout!')

            except Exception as e:
                raise e

            self.reconnect_nodes()

            time.sleep(0.01)

        print("Node stopping...")
        for t in self.nodes_inbound:
            t.stop()

        for t in self.nodes_outbound:
            t.stop()

        time.sleep(1)

        for t in self.nodes_inbound:
            t.join()

        for t in self.nodes_outbound:
            t.join()

        self.sock.settimeout(None)   
        print("Node stopping...")
        time.sleep(2)
        self.sock.close()
        print("Node stopped!!")

    def outbound_node_connected(self, node_conn):
        self.debug_print("[OUTBOUND CONNECTION]: Connected to %s:%s" % (node_conn.addr, node_conn.port))
        if self.callback is not None:
            self.callback("outbound_node_connected", self, node_conn, {})

    def inbound_node_connected(self, node_conn):
        self.debug_print("[INBOUND CONNECTION]: Connected to " + node_conn.id)
        if self.callback is not None:
            self.callback("inbound_node_connected", self, node_conn, {})

    def node_disconnected(self, node_conn):
        self.debug_print("node_disconnected: " + node_conn.id)

        if node_conn in self.nodes_inbound:
            del self.nodes_inbound[self.nodes_inbound.index(node_conn)]
            self.inbound_node_disconnected(node_conn)

        if node_conn in self.nodes_outbound:
            del self.nodes_outbound[self.nodes_outbound.index(node_conn)]
            self.outbound_node_disconnected(node_conn)

    def inbound_node_disconnected(self, node_conn):
        self.debug_print("[INBOUND DISCONNECTION]: Disconnected from node " + node_conn.id)
        if self.callback is not None:
            self.callback("inbound_node_disconnected", self, node_conn, {})

    def outbound_node_disconnected(self, node_conn):
        self.debug_print("[OUTBOUND DISCONNECTION]: Disconnected from node " + node_conn.id)
        if self.callback is not None:
            self.callback("outbound_node_disconnected", self, node_conn, {})

    def node_message(self, node_conn, data):

        print(json.dumps(data))
        keys_in_data = [x[1] for x in enumerate(data)]

        if 'type' in keys_in_data:

            if data['type'] == 'chain_request':
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

    def node_disconnect_with_outbound_node(self, node_conn):
        self.debug_print("node wants to disconnect with oher outbound node: " + node_conn.id)
        if self.callback is not None:
            self.callback("node_disconnect_with_outbound_node", self, node_conn, {})


    def node_request_to_stop(self):
        
        self.debug_print("node is requested to stop!")
        if self.callback is not None:
            self.callback("node_request_to_stop", self, {}, {})

    def node_reconnection_error(self, node_dict):
        self.debug_print("node_reconnection_error: Reconnecting to node " + node_dict['addr'] + ":" + str(node_dict['port']) + " (trials: " + str(node_dict['trials']) + ")")
        return True

    def __str__(self):
        return 'Node: {}:{}'.format(self.addr, self.port)
