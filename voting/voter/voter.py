from flask import Flask, session
from flask import render_template, redirect, request, jsonify, g
from math import *

# from utils import get_ip

import datetime, time
import json
import codecs
import requests
import os

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

app = Flask(__name__)

hasVoted = False

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
        
        response = requests.post('http://127.0.0.1:7000/auth', json={'username': uname, 'password': pword})
        data = response.json()
        if data['status'] == True:
            if 'message' not in data:
                session['ELECTION_INFO'] = data['election_info']
                session['ELECTION_AUTH'] = data['election_auth']
                session['SIGNATURE'] = data['signature']
                session['uid'] = data['user_id']
                session['isLoggedIn'] = True
                session['uname'] = uname

                global hasVoted
                g.hasVoted = True
                
                return redirect('/index')
            else:
                return redirect('/voted')
        return {'status': False, 'message': 'You are not eligible to vote'}

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
    data = request.get_json()

    ballot_paper = {}
    ballot_paper['voted_candidates'] = data
    ballot_paper = completeBallot(ballot_paper)

    for ea in session['ELECTION_AUTH']:
        response = requests.post("http://" + ea + "/submit-ballot",json=ballot_paper)

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
    
def completeBallot(arg):
    arg['signature'] = session['SIGNATURE']
    arg['user_id'] = session['uid']
    arg['user_name'] = session['uname']

    return arg

app.secret_key = 'mysecret'

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=8080, type=int, help='port to listen on')
    parser.add_argument('--host', default='127.0.0.1', type=str, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='127.0.0.1', port=port, debug = True, threaded = True)
