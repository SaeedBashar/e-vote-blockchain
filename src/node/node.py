import socket
import time
import threading
import random
import hashlib

from . import node_connection

class Node(threading.Thread):

    def __init__(self, addr, port, id, callback=None, max_connections=0):
        super(Node, self).__init__()

        self.addr = addr
        self.port = port
        self.callback = callback

        self.terminate_flag = threading.Event()

        self.nodes_inbound: list[node_connection.Node_connection] = []  
        self.nodes_outbound: list[node_connection.Node_connection] = []

        self.reconnect_to_nodes: list[node_connection.Node_connection] = []

        if id == None:
            self.id = self.generate_id()
        else:
            self.id = str(id)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.init_server()

        self.message_count_send = 0
        self.message_count_recv = 0
        self.message_count_rerr = 0

        self.max_connections = max_connections

        self.debug = False


    @property
    def all_nodes(self):
        return self.nodes_inbound + self.nodes_outbound


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
                    "addr": addr, "port": port, "tries": 0
                })

            return True

        except Exception as e:
            self.debug_print("[CONNECTION ERROR]: Could not connect with node. (" + str(e) + ")")
            return False


    def create_new_connection(self, sock, id, addr, port):
        pass

    def outbound_node_connected(self, t):
        pass