import random
from urllib import response
from uuid import uuid4
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
voter_img = {}

@app.context_processor
def cxt_proc():
    def toUpper(el):
        return str(el).upper()
    
    def percent(el):
        if result_data !=  None:
            if result_data['total_votes'] == 0:
                total = 1
            else:
                total = result_data['total_votes']

            return str(round((el/int(total)) * int(100),1))

    def parl_percent(el, total):  
        if total == 0:
            total = 1
        return str(round((el/int(total)) * int(100),1))

    def remove_space(el):
        return el.replace(' ', '')
    
    return {'upper': toUpper, 'percent': percent, 'r_space': remove_space, 'p_percent': parl_percent}

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
                x = uuid4()
                sign_id = str(x).replace('-', '')
                session['sign_id'] = sign_id
                response = requests.post('http://127.0.0.1:7000/user-get-info', json={'id': data['id'], 'sign_id': sign_id}).json()
                if response['status'] == True:
                    if 'message' not in response:
                        keys = gen_key()
                        session['public_key'] = keys['public_key']
                        session['private_key'] = keys['private_key']

                        global voter_img
                        for x in response['election_info']['candidates']:
                            voter_img[x['name'].replace(' ', '')] = x['img'] if x['img'] != "" or x['img'] != None else ""
                            x['img'] = ''

                        session['ELECTION_INFO'] = response['election_info']
                        session['ELECTION_ADDR'] = response['election_addr']
                        session['MINER_NODES'] = response['miner_nodes']
                        session['SIGNATURE'] = response['signature']
                        session['uid'] = response['user_id']
                        session['constituency'] = response['constituency']
                        session['isLoggedIn'] = True
                        session['uname'] = uname


                        global hasVoted
                        g.hasVoted = True
                        
                        
                        return redirect('/index')
                    else:
                        return redirect('/voted')
            else:
                return redirect('/voted')
        else:
            t_data = {'message': data['message']}
            return render_template('not-eligible.html', data=t_data)
        # return {'status': False, 'message': 'You are not eligible to vote'}

@app.route('/index')
def index():
    if session.get('isLoggedIn', None) != None:
        if not hasVoted:
            data = {
                'info': session['ELECTION_INFO'],
                'imgs': voter_img
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
            'args': []
        }
    transaction['args'].append({})
    time_voted = dt.timestamp(dt.now())
    transaction['args'][0]['transaction_time'] = time_voted
    
    transaction['args'][0]['action'] = 'vote_cast'
    
    transaction['args'][0]['sign_data'] = [
        session['sign_id']
    ]
    transaction['args'][0]['sign_data'].extend(list(voted_candidates.values()))

    transaction['args'][0]['signature'] = sign_ballot(session['private_key'], transaction['args'][0]['sign_data'])

    transaction['args'].append({
                            'candidates': voted_candidates,
                            'ballot_info': {
                                            'constituency': session['constituency'],
                                            'signature': session['SIGNATURE'], 
                                            'sign_data': [session['sign_id']]
                                        }
                            })
    
    # =================================================================

    for miner in session['MINER_NODES']:
        response = requests.post("http://" + miner + "/transactions",json=transaction).json()

    return jsonify(response)

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
    # const = ['ejisu', 'asokwa', 'bekwai', 'juaben']
    # x = random.randint(0,3)
    response = requests.get('http://127.0.0.1:7000/get-result-for-user?constituency=%s' % session['constituency'])
    # response = requests.get('http://127.0.0.1:7000/get-result-for-user?constituency=%s' % const[x])
    try:
        response = response.json()

        if response['status'] == True:
            global result_data
            result_data = response['data']

            return render_template('/check-results.html', data=result_data)
        else:
            return render_template('/result-not-ready.html')
    except:
        return render_template('/result-not-ready.html')


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
    parser.add_argument('--host', default='0.0.0.0', type=str, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port, threaded = True)
