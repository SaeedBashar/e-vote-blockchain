import binascii
from pathlib import Path
import re
from flask import Flask
from flask import render_template, redirect, request, jsonify
from math import *
from datetime import datetime as dt


# from utils import get_ip

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


__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

app = Flask(__name__)


def get_info():
    global nodes
    global reg_public_key
    global contract_addr
    
    response = requests.post('http://127.0.0.1:7000/get-info', json={'addr': '127.0.0.1:6000'})
    
    reg_public_key = response.json()['public_key']
    nodes = response.json()['nodes']
    contract_addr = response.json()['contract_addr']

get_info()

@app.route('/submit-transaction', methods=['POST'])
def submit_transaction():
    x = request.get_json()

    res = verify_transaction((x['user_name'], x['user_id'], x['signature']))
   
    if res['status'] == True:
        
        response = requests.post('http://127.0.0.1:7000/user-transaction', json={'user_id': x['user_id']})
    
        # Construct a transaction and send to miner nodes
        transaction = {
            'from_addr': format_key_for_api(reg_public_key),
            'to_addr': 'SC' + contract_addr,
            'value': 0,
            'gas': 0,
            'args': [x['voted_candidates']]
        }
        time_voted = dt.timestamp(dt.now())
        transaction['args'].append(time_voted)
        
        transaction['signature'] = x['signature']
        transaction['action'] = 'vote_cast'
        
        transaction['sign_data'] = [
            x['user_name'],
            x['user_id']    
        ]

        # for n in nodes:
        res = requests.post('http://127.0.0.1:4000/transactions', json=transaction)
        print(res.json())   

    return jsonify(res.json())

def verify_transaction(arg):

    h = SHA256.new((arg[0].lower() + arg[1]).encode())
    try:
        pub_key = RSA.importKey(reg_public_key.encode())
        verifier = PKCS1_v1_5.new(pub_key)

        verifier.verify(h, arg[2].encode())
        print("Verified!!")
        return {
            'status': True,
            'msg': 'Verification Success'
        }
    except (ValueError, TypeError ):
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

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=6000, type=int, help='port to listen on')
    parser.add_argument('--host', default='127.0.0.1', type=str, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='127.0.0.1', port=port, debug = True, threaded = True)
