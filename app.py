import os
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit

import socket
from time import time

from src.blockchain_node.node import Node

from argparse import ArgumentParser

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


parser = ArgumentParser()
parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
args = parser.parse_args()
port = args.port

addr = socket.gethostbyname(socket.gethostname())
host_node = Node(addr, port)

host_node.start()

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', chain=host_node.blockchain.chain)

@app.route('/all_nodes', methods=['GET'])
def get_nodes():
    return jsonify({'data': host_node.all_nodes})

@app.route('/get_pk', methods=['GET'])
def get_id():
    return jsonify({'public_key': host_node.public_key})

@app.route('/connect_node', methods=['POST'])
def connect_node():
    data = request.get_json()
    return_data = host_node.connect_with_node(data['host'], data['port'])

    if return_data['status']:
        return jsonify({
            'message': return_data['msg']
        })
    return jsonify({
        'message': return_data['msg']
    })


# Blockchain routes
@app.route('/mine_block', methods=['GET'])
def mine_block():
    return_data = host_node.start_mining()
    if return_data['status'] == True:
        return jsonify({'message': return_data['msg'],
                'Block': host_node.blockchain.chain[-1].block_item})
    else:
        return jsonify({'message': return_data['msg']})


@app.route('/get_chain', methods=['GET'])
def get_chain():
    block_data = request.args.to_dict()
    tmp = []
    if block_data != {}:
        tmp = host_node.extract_chain_part(block_data['index'])
    else:
        for b in host_node.blockchain.chain:
            tmp.append(b.block_item)

    return jsonify({
        'chain': tmp,
        'length': len(tmp)
    })

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    data = request.get_json()
    tx_keys = ['from_addr', 'to_addr', 'value', 'gas', 'args']
    for k in tx_keys:
        if k not in list(data.keys()):
            return jsonify({"status": False, 
                            "message": 'Transaction failed. Make sure all required field are included'})
    
    data['timestamp'] = time()
    # host_node.blockchain.add_transaction(data, host_node.send_to_nodes)
    host_node.make_transaction(data)
    return jsonify({"status": True, "message": 'Transaction successfully done'})

@app.route('/get_transactions', methods=['GET'])
def get_pending_tx():
    tmp_tx = []
    for tx in host_node.blockchain.transactions:
        tmp_tx.append(tx.tx_item)

    return jsonify({"transactions":tmp_tx})

# TODO:: would work on this route 
@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = host_node.replace_chain()
    if is_chain_replaced:
        tmp = []
        for b in host_node.blockchain.chain:
            tmp.append(b.block_item)
        response = {
            'message': 'Chain replaced by the longest one',
            'newChain': tmp}
    else:
        tmp = []
        for b in host_node.blockchain.chain:
            tmp.append(b.block_item)
        response = {
            'message': 'All good, the chain is the longest one',
            'chain': tmp}
    return jsonify(response)
    
# @app.route('/is_chain_valid', methods=['GET'])
# def is_valid():
#     isValid = host_node.blockchain.is_chain_valid(host_node.blockchain.chain)
#     if isValid:
#         response = {'message': 'All good. The blockchain is valid'}
#     else:
#         response = {'message': 'We have a problem, the chain is invalid!!'}
#     return jsonify(response)



# @socketio.on('connect')
# def test_connect():
#     emit('update',  {'data':'Lets dance'})

# @socketio.on('Slider value changed')
# def value_changed(message):
#     emit('update value', message, broadcast=True)


if __name__ == '__main__':
    socketio.run(app, host=addr, port=(int(port) - 1000), debug = True)
