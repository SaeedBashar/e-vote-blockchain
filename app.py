import binascii
import json
from math import trunc
import os
from flask import Flask, jsonify, request, render_template, redirect, session, escape, g
from flask_cors import CORS
from flask_socketio import SocketIO, emit

import socket
import time as tm
from time import time
from datetime import datetime as dt

from src.blockchain_node.node import Node
from src.wallet.wallet import Wallet
from database.database import Database as db
from api.api import API as api
from util.util import *
from argparse import ArgumentParser


parser = ArgumentParser()
parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
args = parser.parse_args()
port = args.port

# addr = socket.gethostbyname(socket.gethostname())
addr = "0.0.0.0"
host_node = Node(addr, port)

host_node.start()

app = Flask(__name__)
CORS(app)

@app.route('/api/<req>')
def api_route(req):
    response = api.get_url(req)

    return jsonify(response)

@app.route('/', methods=['GET'])
def index():
    if 'u_name' in session:
        return redirect('/home')
    else:
        return redirect('/login')

@app.route('/home', methods=['GET'])
def home():
    if 'u_name' in session:
        data = {
            'name': session['name'],
            'email': session['email'],
            'u_name': session['u_name'],
            'public_key': format_key_for_display(session['public_key'])
        }

        return_data = db.get_data('blocks')
        blocks = []
        for b in return_data:
            d = {}
            d['index'] = b[0]
            d['timestamp'] = b[1]
            d['data'] = b[2]
            d['difficulty'] = b[3]
            d['merkle_root'] = b[4]
            d['prev_hash'] = b[5]
            d['nonce'] = b[6]
            d['hash'] = b[7]
            blocks.append(d)
        
        data['blocks'] = blocks

        return_data = db.get_data('transactions')
        transactions = []
        data['sent'] = 0
        data['received'] = 0
        for b in return_data:
            d = {
                "from_addr": format_key_for_display(b[0])[:15] if b[0] != None else b[0],
                "to_addr": format_key_for_display(b[1])[:15] if b[1] != None else b[0],
                "value": b[2],
                "gas": b[3],
                "args": json.loads(b[4]),
                "timestamp": b[5],
                "tx_hash": b[6]
            }
            transactions.append(d)

            if session['public_key'] == b[0]:
                data['sent'] += int(b[2])

            if session['public_key'] == b[1]:
                data['received'] += int(b[2])
        
        data['transactions'] = transactions
        
        return render_template('home/index.html', data=data)
    else:
        return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def signin():
    if request.method == 'GET':
        return render_template('home/page-login.html')
    else:
        uname = request.form.get('username')
        pword = request.form.get('password')
        
        return_data = db.get_user((uname, pword))
      
        if len(return_data) != 0:
            return_data = return_data[0]

        if len(return_data) != 0:
            session['name'] = return_data[0]
            session['email'] = return_data[1]
            session['u_name'] = return_data[2]
            session['password'] = return_data[3]
            session['private_key'] = return_data[4]
            session['public_key'] = return_data[5]

            if session['public_key'] == None or session['public_key'] == "":
                return redirect('/key-generate')
            else:
                return redirect('/home')
        else:
            
            return redirect('/login')

@app.route('/logout')
def signout():
    session.pop('u_name', None)
    session.pop('name', None)
    session.pop('email', None)
    session.pop('public_key', None)
    session.pop('password', None)

    return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('home/page-register.html')
    else:
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            uname = request.form.get('username')
            pword = request.form.get('password')

            status = db.add_user((name, email, uname, pword))
            if status:
                return redirect('/key-generate')
            else:
                return jsonify({'message': 'An Error Occured while creating record!!'})
        except Exception as e:
            print(e)
            return jsonify({'message': 'An Unexpected Error Occured!!, could not create record'})
        
@app.route('/key-generate')
def key_generate():
    if 'u_name' in session:
        return render_template('home/page-generate-key.html')
    else:
        return redirect('/login')

@app.route('/generate')
def generate():
    if 'u_name' in session:
        uname = session['u_name']
        pword = session['password']
       
        return_data = db.get_user((uname, pword))
        
        if len(return_data) != 0:
            return_data = return_data[0]
            
            if (return_data[4] == None or return_data[4] == "") and (return_data[5] == None or return_data[5] == ""):
                keys = host_node.gen_key_pair()

                data = {
                    'private_key': keys['private_key'],
                    'public_key': keys['public_key'],
                    'user' : {
                                'name' : session['name'],
                                'email' : session['email']
                            }
                }
                status = db.insert_keys(data)
                
                if status:
                    return jsonify({
                        'private_key': format_key_for_display(keys['private_key'], 'priv'),
                        'public_key': format_key_for_display(keys['public_key'])
                    })
                else:
                    return jsonify({'message': 'Error generating keys!!'})
            else:
                return jsonify({
                        'private_key': format_key_for_display(return_data[4], 'priv'),
                        'public_key': format_key_for_display(return_data[5])
                    })
        else:
            return redirect('/register')
    else:
        return redirect('/login')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'u_name' in session:
        data = {}
        data['name'] = session['name']
        data['email'] = session['email']
        data['u_name'] = session['u_name']
        data['password'] = session['password']
        data['public_key'] = format_key_for_display(session['public_key'])

        return render_template('home/users-profile.html', data = data)
    else:
        return redirect('/login')

@app.route('/send', methods=['GET'])
def send():
    if 'u_name' in session:
        uname = session['u_name']
        pword = session['password']
       
        return_data = db.get_user((uname, pword))
        
        if len(return_data) != 0:
            return_data = return_data[0]

        data = {}
        data['name'] = return_data[0]
        data['email'] = return_data[1]
        data['u_name'] = return_data[2]
        data['password'] = return_data[3]
        data['public_key'] = format_key_for_display(return_data[5])

        return render_template('home/page-send.html', data=data)
    else:
        return redirect('/login')

@app.route('/blocks', methods=['GET'])
def blocks():
    if 'u_name' in session:
        data = {}
        data['name'] = session['name']
        data['email'] = session['email']
        data['u_name'] = session['u_name']
        data['password'] = session['password']
        data['public_key'] = format_key_for_display(session['public_key'])
        
        data['blocks'] = get_blocks(trunc = True)
        
        return render_template('home/page-blocks.html', data=data)
    else:
        redirect('/login')

@app.route('/get_block_by_index')
def get_block_by_index():
    if 'u_name' in session:
        
        data = {}
        data['block'] = get_block()
        return render_template('/home/page-block-detail.html', data=data)

@app.route('/transactions', methods=['GET', 'POST'])
def transactions():
    if request.method == "GET":
        if 'u_name' in session:
           
            data = {}
            data['name'] = session['name']
            data['email'] = session['email']
            data['u_name'] = session['u_name']
            data['password'] = session['password']
            data['public_key'] = format_key_for_display(session['public_key'])
            data['transactions'] = get_transactions(trunc = True)
            data['mined_transactions'] = get_mined_transactions(trunc = True)

            return render_template('home/page-transactions.html', data = data)
        else:
            return redirect('/login')
    else:
        # route to add a new transaction
        data = request.get_json()
        tx_keys = ['from_addr', 'to_addr', 'value', 'gas', 'args']
        for k in tx_keys:
            if k not in list(data.keys()):
                return jsonify({"status": False, 
                                "message": 'Transaction failed. Make sure all required field are included'})
        
        data['from_addr'] = format_key_for_use(data['from_addr'])
        data['to_addr'] = format_key_for_use(data['to_addr'])

        data['timestamp'] = time()

        # Sign transaction if this account is the one making the transaction
        # ==================================================================
        if 'u_name' in session:
            if data['from_addr'] == session['public_key']:
                sig = Wallet.sign_transaction(session['private_key'], [
                            data['from_addr'], 
                            data['to_addr'], 
                            data['value'], 
                            data['gas'], 
                            str(data['args'])
                        ]
                    )

                data['signature'] = sig
        # ==================================================================
        

        response_data = host_node.make_transaction(data)
        return jsonify(response_data)
        
@app.route('/get_transaction_by_hash')
def trans_detail():
    if 'u_name' in session:
        
        data = {}
        data['trans'] = get_transaction()

        return render_template('home/page-transaction-detail.html', data = data)
    else:
        return redirect('/login')

@app.route('/contracts', methods=['GET'])
def contracts():
    if 'u_name' in session:
        data = {}
        data['name'] = session['name']
        data['email'] = session['email']
        data['u_name'] = session['u_name']
        data['password'] = session['password']
        data['public_key'] = format_key_for_display(session['public_key'])

        data['contracts'] = get_contracts(trunc = True)

        return render_template('home/page-contracts.html', data=data)
    else:
        redirect('/login')

@app.route('/get-contract-result', methods=['POST'])
def get_contract_result():
    data = request.get_json()
    
    response = get_contract(data['contract_addr'])
    
    return jsonify(response
    )

@app.route('/connect-node', methods=['GET', 'POST'])
def connect_node():
    if 'u_name' in session:
        if request.method == 'GET':
            data = {}
            data['name'] = session['name']
            data['email'] = session['email']
            data['u_name'] = session['u_name']
            data['password'] = session['password']
            data['public_key'] = format_key_for_display(session['public_key'])

            tmp = []
            for n in host_node.nodes_inbound:
                tmp.append({
                    "address": n.address,
                    "port": n.port,
                    'public_key': n.pk
                })
            data['in_nodes'] = tmp

            tmp = []
            for n in host_node.nodes_outbound:
                tmp.append({
                    "address": n.address,
                    "port": n.port,
                    'public_key': n.pk
                })
            data['out_nodes'] = tmp
            return render_template('home/page-connect-node.html', data=data)
        else:
            data = request.get_json()
            return_data = host_node.connect_with_node(data['address'], int(data['port']))
            res = db.get_connected_node((data['address'], int(data['port'])))
            pk = None
            if len(res) != 0:
                pk = res[0][2]
            return_data['public_key'] = format_key_for_display(pk)
        
        return jsonify(return_data)
    else:
        return redirect('/login')

@app.route('/mine', methods=['GET'])
def mine_block():
    return_data = host_node.start_mining()
    
    if return_data['status'] == True:
        return jsonify({'status': True,'message': return_data['msg'],
                'Block': host_node.blockchain.chain[-1].block_item})
    else:
        return jsonify({'status': False,'message': return_data['msg']})

@app.route('/sync', methods=['GET'])
def sync_chain():
    
    return_data = host_node.sync_chain()

    return jsonify(return_data)

@app.route('/check-sync-complete')
def check_sync():
    # Checks to see if synchronization is still in progress
    if host_node.sync_finished:
        return {'status': True, 'message': 'Synchronization completed Successfully'}
    else:
        return {'status': False, 'message': 'Synchronization is still in progress...'}
 
@app.errorhandler(404)
def page_not_found(error):
    return render_template('home/page-error-404.html'), 404


# Used by flask's session variable
app.secret_key = 'mysecret'

if __name__ == '__main__':
    app.run(host=addr, port=(int(port) - 1000), debug = True)

