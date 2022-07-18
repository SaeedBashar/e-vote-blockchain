import json
import os
from flask import Flask, jsonify, request, render_template, redirect, session, escape, g
from flask_cors import CORS
from flask_socketio import SocketIO, emit

import socket

import time as tm
from time import time

from src.blockchain_node.node import Node
from src.blockchain import keygen
from database.database import Database as db

from argparse import ArgumentParser

# __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


parser = ArgumentParser()
parser.add_argument('-p', '--port', default=5001, type=int, help='port to listen on')
args = parser.parse_args()
port = args.port

addr = socket.gethostbyname(socket.gethostname())
host_node = Node(addr, port)

host_node.start()

app = Flask(__name__)
CORS(app)
# socketio = SocketIO(app)

# @app.context_processor
# def my_utility_processor():

#     g.is_mining = ""

#     def get_mining_status():
#         return g.is_mining

#     def change_mining_status(arg):
#         # nonlocal is_mining
#         g.is_mining = arg

#     return dict(get_status= get_mining_status)

# @app.before_request
# def load_user():
#     if "user_id" in session:
#         g.user = db.session.get(session["user_id"])

@app.route('/', methods=['GET'])
def index():
    if 'u_name' in session:
        return redirect('/home')
    else:
        return redirect('/login')

@app.route('/home', methods=['GET'])
def home():
    if 'u_name' in session:
        host_node.public_key = session['public_key']

        data = {
            'name': session['name'],
            'email': session['email'],
            'u_name': session['u_name'],
            'public_key': session['public_key']
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
                "from_addr": b[0][:15] if b[0] != None else b[0],
                "to_addr": b[1][:15] if b[1] != None else b[0],
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
            session['public_key'] = return_data[5]

            if session['public_key'] == None or session['public_key'] == "":
                return redirect('/key-generate')
            else:
                host_node.public_key = session['public_key']
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
                        'private_key': keys['private_key'],
                        'public_key': keys['public_key']
                    })
                else:
                    return jsonify({'message': 'Error generating keys!!'})
            else:
                return jsonify({
                        'private_key': return_data[4],
                        'public_key': return_data[5]
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
        data['public_key'] = session['public_key']
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
        data['public_key'] = return_data[5]

        return render_template('home/page-send.html', data=data)
    else:
        return redirect('/login')

@app.route('/receive', methods=['GET'])
def receive():
    if 'u_name' in session:
        data = {}
        data['name'] = session['name']
        data['email'] = session['email']
        data['u_name'] = session['u_name']
        data['password'] = session['password']
        data['public_key'] = session['public_key']
        return render_template('home/page-receive.html', data=data)
    else:
        redirect('/login')

@app.route('/blocks', methods=['GET'])
def blocks():
    if 'u_name' in session:
        data = {}
        data['name'] = session['name']
        data['email'] = session['email']
        data['u_name'] = session['u_name']
        data['password'] = session['password']
        data['public_key'] = session['public_key']
        
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
                        tmp_tx.append({
                            "from_addr": tx[0][:15] if tx[0] != None else tx[0],
                            "to_addr": tx[1][:15] if tx[1] != None else tx[1],
                            "value": tx[2],
                            "gas": tx[3],
                            "args": json.loads(tx[4]),
                            "timestamp": tx[5],
                            "tx_hash": tx[6]
                        })
                    tmp_tx1 = []
                    r_data = db.get_data('mined_transactions')
                    for tx in r_data:
                        tmp_tx1.append({
                            "from_addr": tx[1][:15] if tx[1] != None else tx[1],
                            "to_addr": tx[2][:15] if tx[2] != None else tx[2],
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
                    data['public_key'] = session['public_key']
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
                
                data['timestamp'] = time()
                host_node.make_transaction(data)
                return jsonify({"status": True, "message": 'Transaction successfully done'})
        
@app.route('/get_transaction_by_hash')
def trans_detail():
    if 'u_name' in session:
        tx_hash = request.args.get('hash')
        r_data = db.get_transaction(tx_hash)
        # tx = {}
        # ar = ""
        # print(json.loads(r_data[0][4]))
        # for a in json.loads(r_data[0][4]):
        #     ar += f"{a}\n"
        if len(r_data[0]) == 7: # 7 is the number of columns for pending txs in the database
            tx = {
                    "from_addr": r_data[0][0],
                    "to_addr": r_data[0][1],
                    "value": r_data[0][2],
                    "gas": r_data[0][3],
                    "args": r_data[0][4],
                    "timestamp": r_data[0][5],
                    "tx_hash": r_data[0][6]
                }
        else:
            tx = {
                    "from_addr": r_data[0][1],
                    "to_addr": r_data[0][2],
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
        data['public_key'] = session['public_key']

        tmp = []
        r_data = db.get_data('contracts')
        for b in r_data:
            if len(b[0]) == 64:  # 64 being the length of contracts address
                tmp.append({
                    'address': b[0][:40] if b[0] != None else b[0],
                    'balance': b[1]
                })
        data['contracts'] = tmp
        return render_template('home/page-contracts.html', data=data)
    else:
        redirect('/login')

@app.route('/connect-node', methods=['GET', 'POST'])
def connect_node():
    if 'u_name' in session:
        if request.method == 'GET':
            data = {}
            data['name'] = session['name']
            data['email'] = session['email']
            data['u_name'] = session['u_name']
            data['password'] = session['password']
            data['public_key'] = session['public_key']

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
            return_data['public_key'] = pk
            print(return_data)
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

