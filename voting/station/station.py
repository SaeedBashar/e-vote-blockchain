from pathlib import Path
import re
from flask import Flask
from flask import render_template, redirect, request, jsonify
from math import *

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

nodes = []
reg_public_key = ""

def get_info():
    response = requests.post('http://127.0.0.1:7000/get-info', json={'addr': '127.0.0.1:6000'})
    
    reg_public_key = response.json()['public_key']
    nodes = response.json()['nodes']

get_info()

@app.route('/submit-ballot', methods=['POST'])
def submit_ballot():
    x = request.get_json()

    # res = verify_ballot((x['user_name'], x['user_id']))
    
    # if res['status'] == True:
    response = requests.post('http://127.0.0.1:7000/user-vote', json={'user_id': x['user_id']})

    return jsonify({'status': True})

def verify_ballot(arg):

    h = SHA256.new((arg[0] + arg[1]).encode())
    try:
        pub_key = RSA.importKey(reg_public_key.encode())
        verifier = PKCS1_v1_5.new(pub_key)

        verifier.verify(h)
        return {
            'status': True,
            'msg': 'Verification Success'
        }
    except ValueError as e:
        print("Verification Failed")
        print(e)
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


def timestamp_to_string(epoch_time):
    return datetime.datetime.fromtimestamp(epoch_time).strftime('%H:%M')


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=6000, type=int, help='port to listen on')
    parser.add_argument('--host', default='127.0.0.1', type=str, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='127.0.0.1', port=port, debug = True, threaded = True)
