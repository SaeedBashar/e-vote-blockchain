from urllib import response
from flask import Flask, session
from flask import render_template, redirect, request, jsonify, g
from math import *
from datetime import datetime as dt
from pathlib import Path
import binascii

import Crypto.Random
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

import datetime, time
import json
import codecs
import requests
import os

# __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

app = Flask(__name__)

hasVoted = False
result_data = None

@app.context_processor
def cxt_proc():
    def toUpper(el):
        return str(el).upper()
    
    def percent(el):
        if result_data !=  None:
            return str((el/int(result_data['total_votes'])) * int(100))
    
    return {'upper': toUpper, 'percent': percent}

@app.route('/')
def home():
    if session.get('isLoggedIn', None) != None:
        
        if not hasVoted:
            return redirect('/index')
            
        return redirect('/voted')
    
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        uname = request.form.get('username')
        pword = request.form.get('password')
        
        response = requests.post('http://127.0.0.1:7000/user-login', json={'username': uname, 'password': pword})
        data = response.json()

        if data['status'] == True:
            if 'message' not in data:
                response = requests.post('http://127.0.0.1:7000/user-get-info', json={'id': data['id']}).json()
                if response['status'] == True:
                    if 'message' not in response:
                        session['ELECTION_INFO'] = response['election_info']
                        session['ELECTION_ADDR'] = response['election_addr']
                        session['MINER_NODES'] = response['miner_nodes']
                        session['SIGNATURE'] = response['signature']
                        session['uid'] = response['user_id']
                        session['isLoggedIn'] = True
                        session['uname'] = uname

                        keys = gen_key()
                        session['public_key'] = keys['public_key']
                        session['private_key'] = keys['private_key']

                        global hasVoted
                        g.hasVoted = True
                        
                        return redirect('/index')
                    else:
                        return redirect('/voted')
            else:
                return redirect('/voted')
        else:
            return data
        # return {'status': False, 'message': 'You are not eligible to vote'}

@app.route('/index')
def index():
    if session.get('isLoggedIn', None) != None:
        if not hasVoted:
            data = {
                'info': session['ELECTION_INFO']
            }
            return render_template('index.html', data=data)
        return redirect('/voted')
    return redirect('/login')

@app.route('/submit-ballot', methods=['POST'])
def submit_ballot():
    voted_candidates = request.get_json()

    # =================================================================
    transaction = {
            'from_addr': format_key_for_api(session['public_key']),
            'to_addr': 'SC' + session['ELECTION_ADDR'],
            'value': 0,
            'gas': 0,
            'args': [
                {
                    'signature': session['SIGNATURE'], 
                    'sign_data': [session['uname'], session['uid']]
                },
                voted_candidates
            ]
        }
    time_voted = dt.timestamp(dt.now())
    transaction['args'].append(time_voted)
    
    transaction['action'] = 'vote_cast'
    
    transaction['sign_data'] = [
        session['uname'],
        session['uid'],
    ]
    transaction['sign_data'].extend(list(voted_candidates.values()))

    transaction['signature'] = sign_ballot(session['private_key'], transaction['sign_data'])

    # =================================================================

    for miner in session['MINER_NODES']:
        response = requests.post("http://" + miner + "/transactions",json=transaction)

    return {'status': True}

@app.route('/voted')
def done_voting():
    return render_template('done-voting.html')

@app.route('/leave')
def leave():
    if session.get('isLoggedIn', None) != None:
        session.pop('isLoggedIn', None)
        return jsonify({'status': True})
    return jsonify({'status': False})
    
@app.route('/get-result')
def get_results():
    
    response = requests.get('http://127.0.0.1:7000/get-result-for-user')
    response = response.json()

    if response['status'] == True:
        global result_data
        result_data = response['data']['populate_data']

        data = {
            'portfolio': response['data']['populate_data']['portfolio'],
            'cands': response['data']['view_data']
        }
        print(data)
        return render_template('/check-results.html', data=data)
    else:
        return jsonify(response)

@app.route('/get-result-data')
def get_result_data():

    return jsonify(result_data)



def gen_key():
 
    key = RSA.generate(1024)
    priv_key = key.exportKey()
    pub_key = key.publickey().exportKey()
    keys = {
        'private_key': priv_key.decode(),
        'public_key': pub_key.decode()
    }

    # Testing purposes only
    path = Path('data/data.json')
    data = json.loads(path.read_text())
    
    data['voters_keys'].append(keys)
    path.write_text(json.dumps(data))

    return keys

def sign_ballot(pv_key, arg):
    
    priv_key = RSA.importKey(pv_key.encode())
    signer = PKCS1_v1_5.new(priv_key)

    tmp = ""
    for x in arg:
        tmp += str(x)

    h = SHA256.new(tmp.encode())
    sig = signer.sign(h)

    return str(sig)

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
    parser.add_argument('-p', '--port', default=8080, type=int, help='port to listen on')
    parser.add_argument('--host', default='127.0.0.1', type=str, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='127.0.0.1', port=port, debug = True, threaded = True)
