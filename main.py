import json
from flask import Flask, jsonify, request
from uuid import uuid4

from src.chain_struct.blockchain import Blockchain
from src.chain_struct.transaction import Transaction


blockchain = Blockchain()

app = Flask(__name__)

node_addr = str(uuid4()).replace('-', '')

@app.route('/mine_block', methods=['GET'])
def mine_block():
    pass

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    data = request.get_json()
    tx_keys = ['tx_type', 'timestamp', 'voter_addr', 'voted_candidates']
    for k in tx_keys:
        if k not in list(data.keys()):
            return 'Provided data is not complete'
    blockchain.add_transaction(
        data['timestamp'],
        data['voter_addr'],
        data['voted_candidates'],
        data['tx_type']
    )
    return {"done": 'Success'}

@app.route('/pending_transactions', methods=['GET'])
def get_pending_tx():
    tmp_tx = []
    for tx in blockchain.pending_tx:
        tmp_tx.append(tx.tx_item)

    return jsonify({"pending_transactions":tmp_tx})

@app.route('/connect_node', methods=['POST'])
def connect_node():
    data = request.get_json()
    if not data['nodes']:
        return 'No node'
    for node in data['nodes']:
        blockchain.add_node(node)
    response = {
        'message': 'All the nodes are now connected',
        'peers': list(blockchain.nodes)
    }
    return jsonify(response)

@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {
            'message': 'The nodes had different nodes so it was replaced by the longest one',
            'newChain': blockchain.chain}
    else:
        response = {
            'message': 'All good, the chain is the longest one',
            'chain': blockchain.chain}
    return jsonify(response)
    
@app.route('/is_chain_valid', methods=['GET'])
def is_valid():
    isValid = blockchain.is_chain_valid(blockchain.chain)
    if isValid:
        response = {'message': 'All good. The blockchain is valid'}
    else:
        response = {'message': 'We have a problem, the chain is invalid!!'}
    return jsonify(response)

app.run(host='0.0.0.0', port=5000)
