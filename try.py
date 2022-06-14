from flask import Flask, jsonify, request, render_template
import socket

import sys
import time
# sys.path.insert(0, '..') # Import the files where the modules are located

from src.node_pack.node import Node


def node_callback(event, main_node, connected_node, data):
    try:
        if event != 'node_request_to_stop': # node_request_to_stop does not have any connected_node, while it is the main_node that is stopping!
            print('Event: {} from main node {}: connected node {}: {}'.format(event, main_node.id, connected_node.id, data))

    except Exception as e:
        print(e)


addr = socket.gethostbyname(socket.gethostname())
node_1 = Node(addr, 5000, callback=None)

node_1.start()

# node_1.connect_with_node('127.0.0.1', 5002)
# node_1.connect_with_node('127.0.0.1', 5003)

node_1.send_to_nodes({'type': 'message', "content":"hello from node 0"})

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', chain=node_1.blockchain.chain)

@app.route('/all_nodes', methods=['GET'])
def get_nodes():
    return jsonify({'nodes': node_1.all_nodes})

@app.route('/get_id', methods=['GET'])
def get_id():
    return jsonify({'id': node_1.id})

@app.route('/connect_node', methods=['POST'])
def connect_node():
    data = request.get_json()
    is_connected = node_1.connect_with_node(data['host'], data['port'])

    if is_connected:
        return jsonify({
            'msg': 'Connect Successfully'
        })
    return jsonify({
        'msg': 'Failed to connect'
    })


# Blockchain routes
@app.route('/mine_block', methods=['GET'])
def mine_block():
    node_1.blockchain.add_block(node_1.blockchain.pending_tx)
    return jsonify({'message': 'Block added Successfully',
            'Block': node_1.blockchain.chain[-1].block_item})

@app.route('/get_chain', methods=['GET'])
def get_chain():
    l_block_data = request.args.to_dict()
    print(l_block_data)
    tmp = []
    if l_block_data != {}:
        tmp = node_1.extract_chain_part(l_block_data['hash'])
    else:
        for b in node_1.blockchain.chain:
            tmp.append(b.block_item)

    return jsonify({
        'chain': tmp,
        'length': len(tmp)
    })

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    data = request.get_json()
    tx_keys = ['timestamp', 'voter_addr', 'voted_candidates']
    for k in tx_keys:
        if k not in list(data.keys()):
            return 'Provided data is not complete'
    node_1.blockchain.add_transaction(
        data['timestamp'],
        data['voter_addr'],
        data['voted_candidates']
    )
    return jsonify({"done": 'Success'})

@app.route('/pending_transactions', methods=['GET'])
def get_pending_tx():
    tmp_tx = []
    for tx in node_1.blockchain.pending_tx:
        tmp_tx.append(tx.tx_item)

    return jsonify({"pending_transactions":tmp_tx})

# @app.route('/connect_node', methods=['POST'])
# def connect_node():
#     data = request.get_json()
#     if not data['nodes']:
#         return 'No node'
#     for node in data['nodes']:
#         node_1.blockchain.add_node(node)
#     response = {
#         'message': 'All the nodes are now connected',
#         'peers': list(node_1.blockchain.nodes_list)
#     }
#     return jsonify(response)

@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = node_1.replace_chain()
    if is_chain_replaced:
        tmp = []
        for b in node_1.blockchain.chain:
            tmp.append(b.block_item)
        response = {
            'message': 'Chain replaced by the longest one',
            'newChain': tmp}
    else:
        tmp = []
        for b in node_1.blockchain.chain:
            tmp.append(b.block_item)
        response = {
            'message': 'All good, the chain is the longest one',
            'chain': tmp}
    return jsonify(response)
    
@app.route('/is_chain_valid', methods=['GET'])
def is_valid():
    isValid = node_1.blockchain.is_chain_valid(node_1.blockchain.chain)
    if isValid:
        response = {'message': 'All good. The blockchain is valid'}
    else:
        response = {'message': 'We have a problem, the chain is invalid!!'}
    return jsonify(response)


app.run(host=addr, port=4000)
