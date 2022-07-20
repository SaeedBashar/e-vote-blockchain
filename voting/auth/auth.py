import binascii
from pathlib import Path
from flask import Flask, session
from flask import render_template, redirect, request, jsonify
from math import *

import datetime, time
import json
import codecs
import requests
import os

import Crypto
import Crypto.Random
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

from database import database as db

ELECTION_INFO = {
    'id': 1234,
    'portfolio': ['president', 'secretary'],
    'candidates': [
        {'id':0 ,'name': 'Benjamin Kudjoe', 'desc': 'Vote for Peace', 'age': 93, 'portfolio': 'president'},
        {'id':1 ,'name': 'Kelvin Nana', 'desc': 'Vote for Progress', 'age': 87, 'portfolio': 'president'},
        {'id':2 ,'name': 'Kim Lee', 'desc': 'Vote for Progress', 'age': 66, 'portfolio': 'secretary'},
        {'id':3 ,'name': 'Ben Toe', 'desc': 'Vote for Progress', 'age': 34, 'portfolio': 'secretary'},
    ]
}

election_authorities = {'127.0.0.1:6000'}
# election_authorities = ('127.0.0.1:6000', '127.0.0.1:6001')
miner_nodes = ['127.0.0.1:4000']

app = Flask(__name__)

@app.route('/')
def index():
    if 'name' in session:
        return redirect('/home')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        uname = request.form.get('username')
        pword = request.form.get('password')
        
        return_data = db.auth_registrar((uname, pword))

        if len(return_data) != 0:
            session['name'] = uname
            return redirect('/home')

        return redirect('/login')


@app.route('/home')
def home():
    if 'name' in session:
        data = {}
        data['portfolio'] = ELECTION_INFO['portfolio']
        data['candidates'] = ELECTION_INFO['candidates']

        return render_template('index.html', data = data)
    
    return redirect('/login')

@app.route('/add-candidate', methods=['POST'])
def add_candidate():
    if 'name' in session:
        c_name = request.get_json()["name"]
        c_portfolio = request.get_json()["portfolio"]
        c_age = request.get_json()["age"]
        c_desc = request.get_json()["description"]

        cand_l = len(ELECTION_INFO['candidates'])
        ELECTION_INFO['candidates'].append({
            'id': cand_l,
            'name': c_name,
            'desc': c_desc,
            'age': c_age,
            'portfolio': c_portfolio
        })

        return jsonify({
            'id': cand_l,
            'name': c_name,
            'age': c_age,
            'description': c_desc,
            'portfolio': c_portfolio
        })

    return redirect('/login')
    
@app.route('/add-portfolio', methods=['POST'])
def add_portfolio():
    if 'name' in session:
        data = request.get_json()
        print(data['portfolio'])
        ELECTION_INFO['portfolio'].append(data['portfolio'].lower())
        return {'status': True}
    return redirect('/login')

@app.route('/start-election')
def start_election():
    if 'name' in session:
        print('starting election...')
        transaction = {}
        transaction['from_addr'] = get_key()['public_key']
        transaction['to_addr'] = None
        transaction['value'] = 0
        transaction['gas'] = 0
        transaction['args'] = []

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(BASE_DIR, "contract/vote_contract.py")

        with codecs.open(file_path,encoding='utf8',mode='r') as inp:
            transaction['args'].append(inp.read())
            # exec(transaction['args'][0], {'__builtins__': __builtins__}, {'name': 'Ben'})
            
        transaction['args'].append(ELECTION_INFO['portfolio'])
        transaction['contract_addr'] = get_election_addr(transaction['args'][0])

        response = requests.post('http://192.168.56.1:4001/transactions', json=transaction)
        print(response.json())
        return {'status': True}
    return redirect('/login')

@app.route('/logout')
def logout():
    session.pop('name', None)

    return redirect('/')

@app.route('/get-info', methods=['POST'])
def get_info():
    res = request.get_json()['addr']
    election_authorities.add(res)

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(BASE_DIR, "contract/vote_contract.py")
    with codecs.open(file_path,encoding='utf8',mode='r') as inp:
        data = inp.read()

    data = {
        'public_key': get_key()['public_key'],
        'nodes': miner_nodes,
        'contract_addr': get_election_addr(data)
    }

    return jsonify(data)

@app.route('/user-vote', methods=['POST'])
def user_vote():
    data = request.get_json()
    
    db.insert_user_vote(data['user_id'])
    
    return jsonify({'status': True})

@app.route('/auth', methods=['POST'])
def auth_login():
    x = request.get_json()
    r_data = db.get_user((x['username'], x['password']))
    
    if len(r_data) != 0:
        if r_data[0][3] == 0:
            # check to see if voter has an ID already
            hasId = False
            id = db.get_data('voterId', (r_data[0][0], r_data[0][1]))
            if id != None:
                hasId = True

            return {
                'status': True,
                'signature': sign_ballot((r_data[0][0], r_data[0][1]), hasId),
                'election_auth': list(election_authorities),
                'election_info': ELECTION_INFO,
                'user_id': r_data[0][2]
            }
        return {'status': True, 'message': 'Results will be available soon'}
    else:
        return {'status': False}

def get_election_addr(arg):
    path = Path('database/data.json')
    data = json.loads(path.read_text())
    if 'election_addr' in data:
        return data['election_addr']
    else:
        addr = SHA256.new(arg).hexdigest()
        data['election_addr'] = addr
        path.write_text(json.dumps(data))

        return addr

def get_key():
    path = Path('database/data.json')
    data = json.loads(path.read_text())
    if 'keys' in data:
        return data['keys']
    else:
        key = RSA.generate(1024)
        priv_key = key.exportKey()
        pub_key = key.publickey().exportKey()
        keys = {
            'private_key': priv_key.decode(),
            'public_key': pub_key.decode()
        }
        data['keys'] = keys
        path.write_text(json.dumps(data))

        return keys

def sign_ballot(arg, hasId=False):
    path = Path('database/data.json')
    data = json.loads(path.read_text())
   
    if not hasId:
        userId = Crypto.Random.new().read(64).hex()
        db.insert_voter_id(userId, arg)
    else:
        userId = db.get_data('voterId', arg)
        
    priv_key = RSA.importKey(data['keys']['private_key'].encode())
    signer = PKCS1_v1_5.new(priv_key)
    h = SHA256.new((arg[0].lower() + userId).encode())
    sig = signer.sign(h)

    return str(sig)

def verify_ballot(arg):
    path = Path('database/data.json')
    data = json.loads(path.read_text())

    id = db.get_data('voterId', arg)
    h = SHA256.new((arg[0] + id).encode())
    try:
        pub_key = RSA.importKey(data['supported_keys']['public_key'].encode())
        verifier = PKCS1_v1_5.new(pub_key)

        verifier.verify(h)
        return {
            'status': True,
            'msg': 'Verification Success'
        }
    except ValueError as e:
        print("Verification Failed")
        return {
            'status': False,
            'msg': 'Verification Failed'
        }
    except Exception as e:
        print("Unexpected Error occured!!")
        return  {
            'status': False,
            'msg': 'Unexpected Error occured!!'
        }

app.secret_key = 'mysecret'

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=7000, type=int, help='port to listen on')
    parser.add_argument('--host', default='127.0.0.1', type=str, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='127.0.0.1', port=port, debug = True, threaded = True)
