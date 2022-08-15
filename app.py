import binascii
import json
import os
from flask import Flask, jsonify, request, render_template, redirect, session, escape, g
from flask_cors import CORS
from flask_socketio import SocketIO, emit

import socket
import time as tm
from time import time
from datetime import datetime as dt

from src.blockchain_node.node import Node
from src.blockchain import keygen
from database.database import Database as db

from argparse import ArgumentParser

from src.wallet.wallet import Wallet

parser = ArgumentParser()
parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
args = parser.parse_args()
port = args.port

# addr = socket.gethostbyname(socket.gethostname())
addr = "127.0.0.1"
host_node = Node(addr, port)

host_node.start()

app = Flask(__name__)
CORS(app)

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
        
        tmp = []
        r_data = db.get_data('blocks')
        for b in r_data:
            tmp.append({
                'index': b[0],
                'timestamp': b[1],
                'nonce': b[6],
                'hash': b[7][:15] if b[7] != None else b[7]
            })
        data['blocks'] = tmp
        return render_template('home/page-blocks.html', data=data)
    else:
        redirect('/login')

@app.route('/get_block_by_index')
def get_block():
    if 'u_name' in session:
        index = request.args.get('index')
        r_data = db.get_block(index)
        block = {
            'index': r_data[0][0],
            'timestamp': r_data[0][1],
            'data': r_data[0][2].replace("}", "}\n\n"),
            'difficulty': r_data[0][3],
            'merkle_root': r_data[0][4],
            'prev_hash': r_data[0][5],
            'nonce': r_data[0][6],
            'hash': r_data[0][7]
        }
        data = {}
        data['block'] = block
        return render_template('/home/page-block-detail.html', data=data)

@app.route('/transactions', methods=['GET', 'POST'])
def transactions():
    if request.method == "GET":
        if 'u_name' in session:
            tmp_tx = []
            r_data = db.get_data('transactions')
            for tx in r_data:
                from_addr = format_key_for_display(tx[0])
                to_addr = format_key_for_display(tx[1])

                tmp_tx.append({
                    "from_addr": from_addr[:15] if tx[0] != None else tx[0],
                    "to_addr": to_addr[:15] if tx[1] != None else tx[1],
                    "value": tx[2],
                    "gas": tx[3],
                    "args": json.loads(tx[4]),
                    "timestamp": tx[5],
                    "tx_hash": tx[6]
                })
            
            tmp_tx1 = []
            r_data = db.get_data('mined_transactions')
            for tx in r_data:
                from_addr = format_key_for_display(tx[1])
                to_addr = format_key_for_display(tx[2])

                tmp_tx1.append({
                    "from_addr": from_addr[:15] if tx[1] != None else tx[1],
                    "to_addr": to_addr[:15] if tx[2] != None else tx[2],
                    "value": tx[3],
                    "gas": tx[4],
                    "args": json.loads(tx[5]),
                    "timestamp": tx[6],
                    "tx_hash": tx[7]
                })

            data = {}
            data['name'] = session['name']
            data['email'] = session['email']
            data['u_name'] = session['u_name']
            data['password'] = session['password']
            data['public_key'] = format_key_for_display(session['public_key'])
            data['transactions'] = tmp_tx
            data['mined_transactions'] = tmp_tx1

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
        tx_hash = request.args.get('hash')
        r_data = db.get_transaction(tx_hash)
        
        if len(r_data[0]) == 7: # 7 is the number of columns for pending txs in the database
            from_addr = format_key_for_display(r_data[0][0])
            to_addr = format_key_for_display(r_data[0][1])

            tx = {
                    "from_addr": from_addr,
                    "to_addr": to_addr,
                    "value": r_data[0][2],
                    "gas": r_data[0][3],
                    "args": r_data[0][4],
                    "timestamp": r_data[0][5],
                    "tx_hash": r_data[0][6]
                }
        else:
            from_addr = format_key_for_display(r_data[0][0])
            to_addr = format_key_for_display(r_data[0][1])

            tx = {
                    "from_addr": from_addr,
                    "to_addr": to_addr,
                    "value": r_data[0][3],
                    "gas": r_data[0][4],
                    "args": r_data[0][5],
                    "timestamp": r_data[0][6],
                    "tx_hash": r_data[0][7]
                }
        data = {}
        data['trans'] = tx
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

        tmp = []
        r_data = db.get_data('states')
        for b in r_data:
            if len(b) == 64:  # 64 being the length of contracts address
                tmp.append({
                    'address': b[:40] if b != None else b,
                    'balance': r_data[b]['balance']
                })
        data['contracts'] = tmp
        return render_template('home/page-contracts.html', data=data)
    else:
        redirect('/login')

@app.route('/get-contract-result', methods=['POST'])
def get_contract_result():
    data = request.get_json()

    res_data = db.get_contract_info(data['contract_addr'])
    if len(res_data) != 0:
        d1 = dt.now()
        t1 = dt.timestamp(d1)
        
        if t1 < float(res_data[0][1]):
            return jsonify({'status': False, 'message': 'No Such Contract!!'})
        
        elif t1 >= float(res_data[0][1]) and t1 <= float(res_data[0][2]):
            return jsonify({'status': False, 'message': 'Contract is still in progress, can not get result now.!!'})
        
        else:
            state = db.get_state(data['contract_addr'])[0]
            data = {
                'status': True,
                'contract_result': json.loads(state[4])
            }
            return jsonify(data)

    return jsonify({'status': False, 'message': 'No Such Contract!!'})

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
            pk = db.get_connected_node((data['address'], int(data['port'])))[0][2]
            return_data['public_key'] = format_key_for_display(pk)
        
        return jsonify(return_data)
    else:
        return redirect('/login')

@app.route('/mine', methods=['GET'])
def mine_block():
    host_node.public_key = session.get('public_key')
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

def format_key_for_display(key, type='pub'):
    if key != None:
        if type == 'pub':
            key = key[27 : len(key) - 25]
            return binascii.hexlify(key.encode()).decode().upper()
        else:
            key = key[32 : len(key) - 30]
            return binascii.hexlify(key.encode()).decode().upper()
    else:
        return key

def format_key_for_use(key, type="pub"):
    pub_start = '-----BEGIN PUBLIC KEY-----\n'
    pub_end = '\n-----END PUBLIC KEY-----'

    priv_start = '-----BEGIN RSA PRIVATE KEY-----\n'
    priv_end = '\n-----END RSA PRIVATE KEY-----'

    if key != None:
        if key[:2].upper() != "SC":
            if type == 'pub':
                key = binascii.unhexlify(key.lower()).decode()
                key = f"{pub_start}{key}{pub_end}"
                return key

            else:
                key = binascii.unhexlify(key.lower()).decode()
                key = f"{priv_start}{key}{priv_end}"
                return key
        return key
    else:
        return key

# Used by flask's session variable
app.secret_key = 'mysecret'

if __name__ == '__main__':
    app.run(host=addr, port=(int(port) - 1000), debug = True)

