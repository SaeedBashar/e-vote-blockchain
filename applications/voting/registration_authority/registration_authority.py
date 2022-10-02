import binascii
from pathlib import Path
from unittest import result
from flask import Flask, session
from flask import render_template, redirect, request, jsonify, g
from math import *

from datetime import datetime as dt
import json
import codecs
import requests
import os
from uuid import uuid4

import Crypto
import Crypto.Random
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

from database import database as db


# Get and set some initial values for Election Authority
# =====================================================
path = Path('database/election_config.json')
data = json.loads(path.read_text())

MINER_NODES = data['miner_nodes']
constituencies = ['ejisu', 'asokwa', 'bekwai', 'juaben']
# =====================================================


app = Flask(__name__)

@app.context_processor
def cxt_proc():
    def toUpper(el):
        return str(el).upper()
    
    def percent(el):  
        result = json.loads(db.get_election()[0][2])
        if result['total_votes'] == 0:
            total = 1
        else:
            total = result['total_votes']
            
        return str(round((el/int(total)) * int(100),1))

    def parl_percent(el, total):
        if total == 0:
            total = 1 
        return str(round((el/int(total)) * int(100),1))

    def toStr(el):
        return str(el)

    def length(el):
        return len(el)
    
    return {'upper': toUpper, 'percent': percent, 'toStr': toStr, 'len': length, 'p_percent': parl_percent}


# ===================================
# APIs used by Registration Authority

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
            return_data = return_data[0]

            session['name'] = uname
            session['email'] = return_data[1]
            session['u_name'] = return_data[2]
            session['password'] = return_data[3]
            session['private_key'] = return_data[4]
            session['public_key'] = return_data[5]

            if session['public_key'] == None or session['public_key'] == "":
                return redirect('/key-generate')
            else:
                return redirect('/home')

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

            status = db.add_registrar((name, email, uname, pword))
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
       
        return_data = db.get_registrar((uname, pword))
        
        if len(return_data) != 0:
            return_data = return_data[0]
            
            if (return_data[4] == None or return_data[4] == "") and (return_data[5] == None or return_data[5] == ""):
                keys = generate_key()
                
                session['private_key'] = keys['private_key']
                session['public_key'] = keys['public_key']
                
                status = db.update_registrar_info((keys['public_key'], keys['private_key'], session['u_name'], session['password']))
                
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

@app.route('/home')
def home():
    if 'name' in session:
        data = {
            'presidents': [],
            'parliaments': [],
            'constituency': constituencies,
            'parties': db.get_parties()
        }
        res = db.get_presidents()
    
        if len(res) != 0:
            path = Path('database/presidents_img.json')
            imgs = json.loads(path.read_text())
            for p in res:
                data['presidents'].append({
                    'id': p[1],
                    'name': p[2],
                    'age': p[4],
                    'description': p[5],
                    'image': imgs[p[2].replace(' ', '')],
                    'party_name': db.get_party_name(p[0])
                })

        res = db.get_parliaments()
        
        if len(res) != 0:
            path = Path('database/parliaments_img.json')
            imgs = json.loads(path.read_text())
            for p in res:
                data['parliaments'].append({
                    'id': p[1],
                    'name': p[2],
                    'age': p[3],
                    'constituency': p[4],
                    'description': p[5],
                    'image': imgs[p[2].replace(' ', '')],
                    'party_name': db.get_party_name(p[0])
                })
        return render_template('index.html', data = data)
    
    return redirect('/login')

@app.route('/start-election', methods=['POST'])
def start_election():
    if 'name' in session:
        print('starting election...')
        ret_data = db.get_registrar((session['u_name'], session['password']))
        req_data = request.get_json()
        transaction = {}
        transaction['from_addr'] = format_key_for_api(ret_data[0][5])
        transaction['to_addr'] = None
        transaction['value'] = 0
        transaction['gas'] = 0
        transaction['args'] = []

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(BASE_DIR, "contract/vote_contract.py")

        with codecs.open(file_path,encoding='utf8',mode='r') as inp:
            transaction['args'].append(inp.read())
            # exec(transaction['args'][0], {'__builtins__': __builtins__}, {'name': 'Ben'})
        
        # d1 = dt.now()
        # d2 = dt(d1.year, d1.month, d1.day, d1.hour, d1.minute + 5, d1.second, d1.microsecond)
        
        # t1 = dt.timestamp(d1)
        # t2 = dt.timestamp(d2)

        t1 = float(req_data['start_date'])
        t2 = float(req_data['end_date'])

        global start_time # used to control voter voting ahead of time
        start_time = t1
        
        contract_params = {
            'start_time': t1,
            'end_time': t2
        }
        contract_params['contract_addr'] = db.get_election()[0][1]
        contract_params['action'] = "init"

        # Signing the transaction using the contract the address
        # ===================================================
        priv_key = RSA.importKey(ret_data[0][4].encode())
        signer = PKCS1_v1_5.new(priv_key)
        h = SHA256.new((contract_params['contract_addr']).encode())
        sig = signer.sign(h)
        contract_params['signature'] = str(sig)
        contract_params['sign_data'] = [contract_params['contract_addr']]
        # ===================================================
        
        transaction['args'].append(contract_params)

        response = requests.post(F'http://{MINER_NODES[0]}/transactions', json=transaction)
        
        return response.json()
    return redirect('/login')

@app.route('/create-election')
def create_election():
    ret = db.get_election()
    if len(ret) == 0:
        x = uuid4()
        id = str(x).replace('-', '')

        addr = SHA256.new(id.encode()).hexdigest()

        status = db.create_election((id, addr, None))

        if status == True:
            return {'status': True, 'message': 'Election Initiated Successfully!!'}

        return {'status': False, 'message': 'Error Initiating Election!!!'}
    else:
        return {'status': False, 'message': 'There is an Election with Id : \n' + str(ret[0][1]) + ' already!!'}

@app.route('/get-contract-transactions')
def get_cont_transactions():

    addr =  db.get_election()[0][1]
    
    response = requests.get(f'http://{MINER_NODES[0]}/api/contract-transactions?address={addr}')
    response = response.json()
    
    # ===========================
   
    temp = db.get_presidents()
    pres = []
    # ========================================
    for p in temp:
        pres.append({
            'id': p[1],
            'name': p[2],
            'portfolio': p[3]
        })

    parl = {}
    for c in constituencies:
        tmp = db.get_parliaments_by_constituency(c)
       
        parl[c] = []
        for i1 in tmp:
            parl[c].append({
                'id': i1[1],
                'name': i1[2],
                'constituency': i1[4]
            })

    # ===========================
   
    data = {
        'presidents': pres,
        'parliaments': parl,
        'transactions': response
    }
    return render_template('contract-transactions.html', data=data)

@app.route('/check-results')
def check_results():

    data = {
        'contract_addr': db.get_election()[0][1]
    }
    
    response = requests.post(f'http://{MINER_NODES[0]}/get-contract-result', json=data)
    response = response.json()
    if response['status'] == True:

        db.update_election(response['contract_result'])

        ret_data = construct_data_for_display()

        return render_template('check-results.html', data=ret_data)
    else:
        return render_template('result-not-ready.html')

@app.route('/get-result')
def get_result():
    
    try:
        ret_data = construct_data_for_display()
        ret_data['total_votes'] = json.loads(db.get_election()[0][2])['total_votes']
        ret_data['status'] = True
        return ret_data
    except:
        return {'status': False}

@app.route('/logout')
def logout():
    session.pop('name', None)

    return redirect('/')




# ====================================
# APIs used by voters

@app.route('/get-result-for-user')
def get_result_for_user():
    cons = request.args.get('constituency')

    result = db.get_election()[0][2]
    if result != None or result != "":
        data = {}

        data = construct_data_for_display()
        pres = data['presidents']
        parl = data['parliaments'][cons]

        ret_data = {
            'presidents': pres,
            'parliaments': parl,
            'parl_count': data['parl_count'][cons],
            'total_votes': json.loads(db.get_election()[0][2])['total_votes']
        }

        return jsonify({'status': True, 'data' : ret_data})

    else:
        return jsonify({'status': False, 'message': 'Election Result Not Ready Yet!!'})

@app.route('/user-transaction', methods=['POST'])
def user_vote():
    data = request.get_json()
    
    db.insert_user_vote(data['user_id'])
    
    return jsonify({'status': True})

@app.route('/user-login', methods=['POST'])
def auth_login():
    x = request.get_json()

    uname = x['username'].lower()
    pword = SHA256.new(x['password'].encode()).hexdigest()
    r_data = db.get_user((uname, pword))
    
    try:
        if  float(dt.timestamp(dt.now())) > start_time: # user trying to vote ahead of time
            if len(r_data) != 0:  # Check if is an eligible voter
                if r_data[0][4] == 0: # Check if he/she has voted already
                    if r_data[0][2] == None: # Check if he/she has an id
                        userId = Crypto.Random.new().read(64).hex()
                        db.insert_voter_id(userId, (uname, pword))
                    else:
                        userId = r_data[0][2] 
                    db.verify_user(userId)
                    return jsonify({'status': True, 'id': userId})
                else:
                    return jsonify({'status': True, 'message': 'You have already voted'})
            else:
                return jsonify({'status': False, 'message': 'You are not eligible to vote'})
        else:
            return jsonify({'status': False, 'message': 'Election is not in progress yet!!'})
    except:
        return jsonify({'status': True, 'message': 'You have already voted'})

@app.route('/user-get-info', methods=['POST'])
def user_get_info():
    x = request.get_json()
    r_data = db.check_if_verified(x['id'])

    if len(r_data) != 0:
        if r_data[1] == 1:
            hasId = True
            db.insert_user_vote(r_data[0])
            user = db.get_data('user', (r_data[0],))

            candidates = []

            path = Path('database/presidents_img.json')
            c_imgs = json.loads(path.read_text())

            temp = db.get_presidents()
            for p in temp:
                candidates.append({
                    'party_id': p[0],
                    'id': p[1],
                    'name': p[2],
                    'portfolio': p[3],
                    'age': p[4],
                    'desc': p[5],
                    'img': c_imgs[p[2].replace(' ', '')]
                })

            path = Path('database/parliaments_img.json')
            c_imgs = json.loads(path.read_text())

            temp = db.get_parliaments_by_constituency(user[3])
            for p in temp:
                candidates.append({
                    'party_id': p[0],
                    'id': p[1],
                    'name': p[2],
                    'age': p[3],
                    'constituency': p[4],
                    'desc': p[5],
                    'portfolio': 'parliament',
                    'img': c_imgs[p[2].replace(' ', '')]
                })

            election_info = {}
            election_info['candidates'] = candidates
            election_info['portfolio'] = ['president', 'parliament']

            # temp = db.get_election()[0][2]
            # election_info['result'] = json.loads(temp) if temp != None or temp != "" else None

            return {
                'status': True,
                'signature': sign_ballot((user[0], user[1]), hasId, x['sign_id']),
                'miner_nodes': list(MINER_NODES),
                'election_info': election_info,
                'election_addr': db.get_election()[0][1],
                'user_id': user[2],
                'constituency': user[3]
            }
        else:
            return {'status': True, 'message': 'Results will be available soon'}
    else:
        return {'status': False, 'message': 'Please verify your credentials and try again'}



# =============================================
# APIs used by Board Members

@app.route('/submit-candidates', methods=["POST"])
def party_data():
    data = request.get_json()

    ret_data = db.get_parties()
    is_submitted = False
    for x in ret_data:
        if x[0] == data['party_id']:
            is_submitted = True

    addr = db.get_election()[0][1]
    if not is_submitted:
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

        ret = db.get_presidents()
        db.add_candidate('pres', (data['party_id'], len(ret), c_name, c_portfolio, c_age, c_desc))
        
        parliamentary = data['parliamentary']
        path = Path('database/parliaments_img.json')
        imgs = json.loads(path.read_text())
        for p in parliamentary:
            ret = db.get_parliaments_by_constituency(p['constituency'])
            db.add_candidate('parl', (data['party_id'], len(ret), p['name'], p['age'], p['constituency'], p['description']))

            if p['imgByte'] != None:
                imgs[p['name'].replace(' ', '')] = p['imgByte']
        path.write_text(json.dumps(imgs))

        db.add_party((data['party_id'], data['party_name'], data['board_address']))

        
        return jsonify({'status': True, 'election_address': addr})
    else:
        return jsonify({'status': True, 'election_address': addr})




# ==========================================================
# UTILITY FUNCTIONS

def sign_ballot(arg, hasId=False, sign_data=''):
    path = Path('database/data.json')
    data = json.loads(path.read_text())
   
    if not hasId:
        userId = Crypto.Random.new().read(64).hex()
        db.insert_voter_id(userId, arg)
    else:
        print(arg)
        userId = db.get_data('voterId', arg)
        
    priv_key = RSA.importKey(data['keys']['private_key'].encode())
    signer = PKCS1_v1_5.new(priv_key)
    h = SHA256.new(sign_data.encode())
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

def construct_data_for_display():
    temp = db.get_election()
    
    if temp[0][2] != None:
        result = json.loads(temp[0][2])
    else:
        result = None

    path = Path('database/presidents_img.json')
    c_imgs = json.loads(path.read_text())

    temp = db.get_presidents()
    pres = []
    # ========================================
    for p in temp:
        tmp1 = result['candidates']['president']
        pres.append({
            'party_id': p[0],
            'id': p[1],
            'name': p[2],
            'portfolio': p[3],
            'age': p[4],
            'desc': p[5],
            'img': c_imgs[p[2].replace(' ', '')] if p[2].replace(' ', '') in c_imgs else None,
            'vote_count': tmp1[str(p[1])]
        })

    path = Path('database/parliaments_img.json')
    c_imgs = json.loads(path.read_text())
    parl = {}
    parl_count = {}
    for c in constituencies:

        tmp = db.get_parliaments_by_constituency(c)
        tmp1 = result['candidates']['parliament'][c]

        try:
            print(parl_count[c])
        except:
            parl_count[c] = 0

        parl[c] = []
        for i1 in tmp:
            for i2 in tmp1:
                if str(i1[1]) == str(i2):
                    parl[c].append({
                        'id': i1[1],
                        'name': i1[2],
                        'age': i1[3],
                        'constituency': i1[4],
                        'description': i1[5],
                        'image': c_imgs[i1[2].replace(' ', '')] if i1[2].replace(' ', '') in c_imgs else None,
                        'party_name': db.get_party_name(i1[0]),
                        'vote_count': tmp1[i2]
                    })
                    parl_count[c] += int(tmp1[i2])
                    break
        
    # ========================================
    

    return {'presidents': pres, 'parliaments': parl, 'parl_count': parl_count}

def generate_key():
        key = RSA.generate(1024)
        priv_key = key.exportKey()
        pub_key = key.publickey().exportKey()
        
        keys = {
            'private_key': priv_key.decode(),
            'public_key': pub_key.decode()
        }

        return keys

app.secret_key = 'mysecret'

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=7000, type=int, help='port to listen on')
    parser.add_argument('--host', default='0.0.0.0', type=str, help='port to listen on')
    args = parser.parse_args()
    port = args.port


    app.run(host='0.0.0.0', port=port, threaded = True)
