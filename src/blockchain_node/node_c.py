
import binascii
import socket

import Crypto
import Crypto.Random
from Crypto.Hash import  SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

from pathlib import Path
import json
import threading

from src.blockchain import keygen


class Node(threading.Thread):
    def __init__(self, address, port):
        super(Node, self).__init__()
        
        self.address = address
        self.port = port

        self.private_key = ""
        self.public_key = ""
        self.key_pair = None

        self.opened_connection = []
        self.connected_nodes = []

        is_mined = False

        ENABLE_MINING = True
        ENABLE_LOGGING = True
        ENABLE_RPC = True

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

    def run(self):
        pass