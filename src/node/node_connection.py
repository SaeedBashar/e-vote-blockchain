import threading
import socket

from node.node import Node

class Node_connection(threading.Thread):
    
    def __init__(self, cur_node : Node, sock: socket, id, addr, port):
        super(Node_connection, self).__init__()
        
        self.cur_node = cur_node
        self.sock = sock
        self.id = id
        self.addr = addr
        self.port = port