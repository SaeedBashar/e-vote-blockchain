from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import socket


from src.blockchain_node.node_c import Node

from argparse import ArgumentParser


parser = ArgumentParser()
parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
args = parser.parse_args()
port = args.port

addr = socket.gethostbyname(socket.gethostname())
host_node = Node(addr, port, callback=None)

host_node.start()

app = Flask(__name__)
CORS(app)

if __name__ == '__main__':
    app.run(host=addr, port=(int(port) - 1000))
