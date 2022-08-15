import binascii
from pathlib import Path
from flask import Flask, session
from flask import render_template, redirect, request, jsonify
from math import *

from datetime import datetime as dt
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


# Get and set some initial values for Election Authority
# =====================================================
path = Path('database/election_data.json')
data = json.loads(path.read_text())

ELECTION_INFO = data['election_info']
election_authorities = set(data['election_authorities'])
miner_nodes = data['miner_nodes']
# =====================================================


app = Flask(__name__)

@app.context_processor
def cxt_proc():
    def toUpper(el):
        return str(el).upper()
    
    def percent(el):
        
                
        return str((el/ELECTION_INFO['result']['total_votes']) * int(100))
    
    return {'upper': toUpper, 'percent': percent}

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
        transaction['from_addr'] = format_key_for_api(get_key()['public_key'])
        transaction['to_addr'] = None
        transaction['value'] = 0
        transaction['gas'] = 0
        transaction['args'] = []

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(BASE_DIR, "contract/vote_contract.py")

        with codecs.open(file_path,encoding='utf8',mode='r') as inp:
            transaction['args'].append(inp.read())
            # exec(transaction['args'][0], {'__builtins__': __builtins__}, {'name': 'Ben'})
        
        d1 = dt.now()
        d2 = dt(d1.year, d1.month, d1.day, d1.hour, d1.minute + 5, d1.second, d1.microsecond)

        t1 = dt.timestamp(d1)
        t2 = dt.timestamp(d2)

        contract_params = {
            'start_time': t1,
            'end_time': t2
        }
        transaction['args'].append(contract_params)
        transaction['contract_addr'] = get_election_addr(transaction['args'][0])

        # Signing the transaction using the contract the address
        # ===================================================
        path = Path('database/data.json')
        data = json.loads(path.read_text())

        priv_key = RSA.importKey(data['keys']['private_key'].encode())
        signer = PKCS1_v1_5.new(priv_key)
        h = SHA256.new((transaction['contract_addr']).encode())
        sig = signer.sign(h)
        transaction['signature'] = str(sig)
        # ===================================================

        response = requests.post('http://127.0.0.1:4000/transactions', json=transaction)
        print(response.json())
        return response.json()
    return redirect('/login')

@app.route('/check-results')
def check_results():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(BASE_DIR, "contract/vote_contract.py")
    with codecs.open(file_path,encoding='utf8',mode='r') as inp:
        data = inp.read()

    data = {
        'contract_addr': get_election_addr(data)
    }
    
    response = requests.post('http://127.0.0.1:4000/get-contract-result', json=data)
    response = response.json()
    if response['status'] == True:
        print(response)
        ELECTION_INFO['result'] = response['contract_result']
        
        
        c_names  = []
    
        for x in ELECTION_INFO['candidates']:
            c_names.append({
                'id': x['id'],
                'name': x['name']
            })
            
        tmp = {}
        cands = ELECTION_INFO['result']['candidates']
        for i in cands:
            tmp[i] = []
            for j in cands[i]:
                for k in c_names:
                    if int(j) == int(k['id']):
                        tmp[i].append({
                            'id': k['id'],
                            'vote_count': cands[i][j],
                            'name' : k['name']
                        })
        
        data = {
            'portfolio': ELECTION_INFO['portfolio'],
            'cands': tmp
        }
        return render_template('check-results.html', data=data)
    else:
        return jsonify(response)

@app.route('/get-result')
def get_result():
    tmp  = []
    
    for x in ELECTION_INFO['candidates']:
        tmp.append({
            'id': x['id'],
            'name': x['name']
        })
        
    return jsonify({
        'cand_names': tmp,
        'result': ELECTION_INFO['result'],
        'portfolio': ELECTION_INFO['portfolio']
    })

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

def format_key_for_api(key, type='pub'):
    if key != None:
        if type == 'pub':
            key = key[27 : len(key) - 25]
            return binascii.hexlify(key.encode()).decode().upper()
        else:
            key = key[32 : len(key) - 30]
            return binascii.hexlify(key.encode()).decode().upper()
    else:
        return key

app.secret_key = 'mysecret'

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=7000, type=int, help='port to listen on')
    parser.add_argument('--host', default='127.0.0.1', type=str, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='127.0.0.1', port=port, debug = True, threaded = True)
