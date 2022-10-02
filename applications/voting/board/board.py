import binascii
from pathlib import Path
from unittest import result
from uuid import uuid4
from flask import Flask, session
from flask import render_template, redirect, request, jsonify, g
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


# Get configuartion values for board member
# =====================================================
path = Path('database/board_config.json')
global_data = json.loads(path.read_text())

PARTY_ID = global_data['party_id']
PARTY_NAME = None

RA_ip = global_data['reg_auth_ip']
RA_port = global_data['reg_auth_port']
miner_ip = global_data['miner_ip']
miner_port = global_data['miner_port']
# =====================================================

ELECTION_ADDRESS = None
TOTAL_VOTES = None

app = Flask(__name__)

@app.context_processor
def cxt_proc():
    def toUpper(el):
        return str(el).upper()
    
    def percent(el): 
        if TOTAL_VOTES == 0:
                total = 1
        else:
            total = TOTAL_VOTES
        return str(round((el/int(total)) * int(100),1))
    
    def parl_percent(el, total):  
        if total == 0:
            total = 1
        return str(round((el/int(total)) * int(100),1))

    def toStr(el):
        return str(el)
    
    return {'upper': toUpper, 'percent': percent, 'toStr': toStr, 'p_percent': parl_percent}

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
        
        return_data = db.signin((uname, pword))

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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            uname = request.form.get('username')
            pword = request.form.get('password')

            status = db.add_user((name, email, uname, pword))
            if status:
                session['name'] = name
                session['email'] = email
                session['u_name'] = uname
                session['password'] = pword
                return redirect('/key-generate',)
            else:
                return jsonify({'message': 'An Error Occured while creating record!!'})
        except Exception as e:
            print(e)
            return jsonify({'message': 'An Unexpected Error Occured!!, could not create record'})
        
@app.route('/key-generate')
def key_generate():
    if 'u_name' in session:
        return render_template('generate-key.html')
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
                keys = generate_key()
                
                session['private_key'] = keys['private_key']
                session['public_key'] = keys['public_key']
                
                status = db.update_data((keys['public_key'], keys['private_key'], session['u_name'], session['password']))
                
                if status:
                    return jsonify({
                        'private_key': format_key_for_api(keys['private_key'], 'priv'),
                        'public_key': format_key_for_api(keys['public_key'])
                    })
                else:
                    return jsonify({'message': 'Error generating keys!!'})
            else:
                return jsonify({
                        'private_key': format_key_for_api(return_data[4], 'priv'),
                        'public_key': format_key_for_api(return_data[5])
                    })
        else:
            return redirect('/register')
    else:
        return redirect('/login')

def generate_key():
        key = RSA.generate(1024)
        priv_key = key.exportKey()
        pub_key = key.publickey().exportKey()
        
        keys = {
            'private_key': priv_key.decode(),
            'public_key': pub_key.decode()
        }

        return keys

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

@app.route('/home')
def home():
    if 'name' in session:
        
        path = Path('database/presidents_img.json')
        c_imgs = json.loads(path.read_text())

        temp = db.get_presidents()
        pres = []
        # ========================================
        for p in temp:
            pres.append({
                'name': p[1],
                'portfolio': p[2],
                'age': p[3],
                'desc': p[4],
                'img': c_imgs[p[1].replace(' ', '')] if p[1].replace(' ', '') in c_imgs else None
            })

        path = Path('database/parliaments_img.json')
        c_imgs = json.loads(path.read_text())
        parl = {}
        
        tmp = db.get_parliaments()
    
        parl = {}
        for i1 in tmp:
            try:
                print(parl[i1[3]])
            except:
                parl[i1[3]] = []

            parl[i1[3]].append({
                'name': i1[1],
                'age': i1[2],
                'constituency': i1[3],
                'description': i1[4],
                'image': c_imgs[i1[1].replace(' ', '')] if i1[1].replace(' ', '') in c_imgs else None
            })

        data = {
            'pres': pres,
            'parl': parl
        }

        return render_template('index.html', data = data)
    
    return redirect('/login')

@app.route('/submit-data', methods=['POST'])
def submit_data():
    # ===========================
    data = request.get_json()

    # x = uuid4()
    # id = str(x).replace('-', '')
    data['party_id'] = PARTY_ID

    global PARTY_NAME
    PARTY_NAME = data['party_name']
    # db.add_party_info((data['party_id'], data['party_name']))

    president = data['presidential']

    c_name = president["name"]
    c_portfolio = president["portfolio"]
    c_age = president["age"]
    c_desc = president["description"]
    c_img = president['imgByte']

    if c_img != None:
        path = Path('database/presidents_img.json')
        imgs = json.loads(path.read_text())
        imgs[c_name.replace(' ', '')] = c_img
        path.write_text(json.dumps(imgs))

    db.add_candidate('pres', (data['party_id'], c_name, c_portfolio, c_age, c_desc))
    
    parliamentary = data['parliamentary']
    path = Path('database/parliaments_img.json')
    imgs = json.loads(path.read_text())
    for p in parliamentary:
        db.add_candidate('parl', (data['party_id'], p['name'], p['age'], p['constituency'], p['description']))

        if p['imgByte'] != None:
            imgs[p['name'].replace(' ', '')] = p['imgByte']
    path.write_text(json.dumps(imgs))

    # ===========================
   

    data['board_address'] = db.get_user((session['u_name'], session['password']))[0][5]
    res = requests.post(f"http://{RA_ip}:{RA_port}/submit-candidates", json=data).json()

    global ELECTION_ADDRESS
    ELECTION_ADDRESS = res['election_address']
    
    return jsonify({'status': True})     

@app.route('/approve-election')
def approve_election():
    board = db.get_user((session['u_name'], session['password']))
    transaction = {
            'from_addr': format_key_for_api(board[0][5]),
            'to_addr': 'SC' + ELECTION_ADDRESS,
            'value': 0,
            'gas': 0,
            'args': []
        }
    transaction['args'].append({})
    time_approved = dt.timestamp(dt.now())
    transaction['args'][0]['transaction_time'] = time_approved
    
    transaction['args'][0]['action'] = 'consent'
    
    transaction['args'][0]['sign_data'] = ['approving']

    transaction['args'][0]['signature'] = sign_ballot(board[0][4], transaction['args'][0]['sign_data'])

    transaction['args'].append({
                                    'public_key': board[0][5],
                                    'signature': transaction['args'][0]['signature'], 
                                    'sign_data': transaction['args'][0]['sign_data']
                            })

    response = requests.post(f'http://{miner_ip}:{miner_port}/transactions', json=transaction)

    return {'status': True}
    

@app.route('/election-status')
def elecion_status():
    # addr = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
    # addr = session['election_addr']
    try:
        data = {
            'contract_addr': ELECTION_ADDRESS
        }
        
        response = requests.post(f'http://{miner_ip}:{miner_port}/get-contract-result', json=data)
        response = response.json()
        print(response)

        if response['status'] == False:
            return render_template('error.html', data=response['message'])

        board = response['contract_result']['board']
        return render_template('election-status.html', data=board)

    except:
        return render_template('error.html', data="An Error Occured")
        
    
@app.route('/get-result')
def check_result():
    
    res = requests.get(f'http://{RA_ip}:{RA_port}/get-result').json()
    if res['status'] == True:
        global TOTAL_VOTES
        TOTAL_VOTES = res['total_votes']

        return render_template('get-results.html', data=res)
    else:
        return render_template('result-not-ready.html', data=res)



@app.route('/get-results')
def get_result():
    
    res = requests.get(f'http://{RA_ip}:{RA_port}/get-result').json()
    
    return res

    
@app.route('/logout')
def logout():
    session.pop('name', None)

    return redirect('/')

def sign_ballot(pv_key, arg):
    
    priv_key = RSA.importKey(pv_key.encode())
    signer = PKCS1_v1_5.new(priv_key)

    tmp = ""
    for x in arg:
        tmp += str(x)

    h = SHA256.new(tmp.encode())
    sig = signer.sign(h)

    return str(sig)

app.secret_key = 'mysecret'

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=8000, type=int, help='port to listen on')
    parser.add_argument('--host', default='127.0.0.1', type=str, help='port to listen on')
    args = parser.parse_args()
    port = args.port


    app.run(host='127.0.0.1', port=port, threaded = True)
