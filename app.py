import os
from flask import Flask, jsonify, request, render_template, redirect, session, escape
from flask_cors import CORS
from flask_socketio import SocketIO, emit

import socket
from time import time

from src.blockchain_node.node import Node
from src.blockchain import keygen
from database.database import Database as db

from argparse import ArgumentParser

# __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


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
    if 'u_name' in session:
        return redirect('/home')
    else:
        return redirect('/login')

@app.route('/home', methods=['GET'])
def home():
    if 'u_name' in session:
        user = {
            'name': session['name'],
            'email': session['email'],
            'u_name': session['u_name'],
            'public_key': session['public_key']
        }
        data = {
            "user" : user,
            'blockchain': host_node.blockchain
        }
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

        c = keygen.get_sym_key()
        enc_pword = c.encrypt(pword.encode())
        return_data = db.get_user((uname, enc_pword.decode()))

        if len(return_data) != 0:
            return_data = return_data[0]

        c = keygen.get_sym_key()

        if len(return_data) != 0:
            session['name'] = return_data[0]
            session['email'] = return_data[1]
            session['u_name'] = return_data[2]
            session['password'] = c.decrypt(return_data[3])
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

            c = keygen.get_sym_key()
            enc_pword = c.encrypt(pword.encode())

            status = db.add_user((name, email, uname, enc_pword.decode()))
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
       
        c = keygen.get_sym_key()
        return_data = db.get_user((uname, c.encrypt(pword).decode()))
        
        if len(return_data) != 0:
            return_data = return_data[0]
            
            if (return_data[4] == None or return_data[4] == "") or (return_data[5] == None and return_data[5] == ""):
                keys = keygen.gen_key_pair()
                # cipher = keygen.get_sym_key()

                enc_priv_key = c.encrypt(keys['private_key'].encode())
                data = {
                    'private_key': enc_priv_key.decode(),
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
                c = keygen.get_sym_key()
                return jsonify({
                        'private_key': c.decrypt(return_data[4]),
                        'public_key': return_data[5]
                    })
        else:
            return redirect('/register')
    else:
        return redirect('/login')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'u_name' in session:
        user = {
            'name': session['name'],
            'email': session['email'],
            'u_name': session['u_name'],
            'public_key': session['public_key']
        }
        return render_template('home/users-profile.html', user = user)
    else:
        return redirect('/login')

@app.route('/send', methods=['GET'])
def send():
    if 'u_name' in session:
        return render_template('home/page-send.html')
    else:
        redirect('/login')

@app.route('/receive', methods=['GET'])
def receive():
    if 'u_name' in session:
        return render_template('home/page-receive.html')
    else:
        redirect('/login')

@app.route('/blocks', methods=['GET'])
def blocks():
    if 'u_name' in session:
        return render_template('home/page-blocks.html')
    else:
        redirect('/login')

@app.route('/transactions', methods=['GET'])
def transactions():
    if 'u_name' in session:
        return render_template('home/page-transactions.html')
    else:
        redirect('/login')

@app.route('/contracts', methods=['GET'])
def contracts():
    if 'u_name' in session:
        return render_template('home/page-contracts.html')
    else:
        redirect('/login')

@app.route('/connected-nodes', methods=['GET'])
def connected_nodes():
    if 'u_name' in session:
        return render_template('home/page-connected_nodes.html')
    else:
        redirect('/login')

@app.route('/connect-node', methods=['GET', 'POST'])
def connect_node():
    if 'u_name' in session:
        data = request.get_json()
        return_data = host_node.connect_with_node(data['host'], data['port'])

        # if return_data['status']:
        #     return jsonify({
        #         'message': return_data['msg']
        #     })
        # return jsonify({
        #     'message': return_data['msg']
        # })
        return render_template('home/page-connect-node.html')
    else:
        redirect('/login')

@app.route('/configure')
def configure():
    if 'u_name' in session:
        return render_template('home/page_configure.html')
    else:
        return redirect('/login')

@app.route('/all_nodes', methods=['GET'])
def get_nodes():
    return jsonify({'data': host_node.all_nodes})

@app.route('/get_pk', methods=['GET'])
def get_id():
    return jsonify({'public_key': host_node.public_key})


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


# @socketio.on('connect')
# def test_connect():
#     emit('update',  {'data':'Lets dance'})

# @socketio.on('Slider value changed')
# def value_changed(message):
#     emit('update value', message, broadcast=True)

app.secret_key = 'mysecret'

if __name__ == '__main__':
    socketio.run(app, host=addr, port=(int(port) - 1000), debug = True)
