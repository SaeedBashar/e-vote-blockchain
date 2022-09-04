
import binascii
import hashlib
import json
import math
import os
from pathlib import Path
import ast
import sys
import threading
from threading import Thread

import Crypto
import Crypto.Random
from Crypto.Hash import  SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

import time as tm
from time import time
from datetime import datetime as dt

from src.blockchain.transaction import Transaction
from src.blockchain.block import Block
from src.blockchain import miner
from src.wallet.wallet import Wallet
from database.database import Database as db


# Get and initialize the public key used for the initial transaction
# ==================================================================
path = Path('src/blockchain/data/blockchain.json')
init_public_key = json.loads(path.read_text())['init_public_key']
# ==================================================================


class Blockchain:
    def __init__(self):

        self.transactions = []

        # Get and initialize transaction objects if some exist in the database.
        # If some exist, the node was online before, else initialize the first
        # transaction for a newly running node.
        # ====================================================================
        return_data = db.get_data('transactions')
        if len(return_data) != 0:
            for tx in return_data:
                tx_obj = Transaction.get_tx_object(tx)
                self.transactions.append(tx_obj)
        else:
            if len(db.get_data('mined_transactions')) == 0:
                
                # Set the time to the begining of the year 2022 for initial transaction
                t = dt.timestamp(dt(2022, 1, 1))  
                
                self.initial_transaction = Transaction(None, init_public_key, 0, 0, ['Initial Blockchain Transaction'], t)
                db.add_transaction(self.initial_transaction)
                db.add_to_state(init_public_key)
        # ====================================================================
        

        # Initiliaze the difficulty and mining reward from data/database.json file
        # ========================================================================
        path = Path('src/blockchain/data/blockchain.json')
        data = json.loads(path.read_text())

        self.difficulty = data['difficulty']
        self.reward = data['reward']
        # ========================================================================

        self.chain = []

        self.miner_thread = None

        
        self.contract_params = {}  
        c_res = db.get_data('contracts')
        if len(c_res) != 0:
            for c in c_res:
                self.contract_params[c[0]] = {
                    'start_time': float(c[1]),
                    'end_time': float(c[2])
                }

        # get and initiliaze block objects if some exist in the database
        # If some exist, the node was online before, else create the 
        # genesis block of the chain
        # ==============================================================
        return_data = db.get_data('blocks')
        if len(return_data) != 0:
            for blk in return_data:
                blk_obj = Block.get_blk_object(blk)
                self.chain.append(blk_obj)
        else:
            self.create_genesis_block()
        # ==============================================================

    def create_genesis_block(self):
        t = dt.timestamp(dt(2022, 1, 1))
        block = Block(0, t, [self.initial_transaction], '', self.difficulty)

        # Add initial transaction to mined txs and remove from umined txs
        db.add_to_mined_tx(0, self.initial_transaction)
        self.transactions = list(filter(lambda tx: tx.tx_hash != self.initial_transaction.tx_hash, self.transactions))
        
        block.prev_hash = '0' * 64
        block.mine_block(self.difficulty)
        block.set_block()

        self.chain.append(block)
        db.add_block(block)

    def start_miner(self, addr, send_nodes):

        # Start a mining process on a new thread since 
        self.miner_thread = ThreadWithReturnValue(target=miner.mine, name='MinerThread', args=(self,))
        self.miner_thread.start()

        mined_block = self.miner_thread.join()

        if mined_block != None:
            mining_reward_tx = {
                'from_addr': None,
                'to_addr': addr,
                'value': self.reward,
                'gas': 0,
                'args': [],
                'timestamp': time()
            }
            self.add_transaction(mining_reward_tx, send_nodes)
        
        return mined_block

    def add_block(self, n_block):

        if n_block['prev_hash'] != self.chain[-1].prev_hash: # If node already has the new block
            
            # Convert transactions in block into json objects
            for tx in n_block['data']:
                tx['args'] = ast.literal_eval(tx['args'])
            
            is_valid_block = Block.is_valid(n_block, self.chain[-1].block_item)
            
        
            if is_valid_block:

                # Check and update the difficulty after every fifth block
                # =======================================================
                if len(self.chain) % 5 == 0:
                    self.difficulty = self.difficulty + 1
                    
                    path = Path('src/blockchain/data/blockchain.json')
                    data = json.loads(path.read_text())
                
                    data['difficulty'] = self.difficulty
                    path.write_text(json.dumps(data))
                # =======================================================

                   
                tmp_txs = []
                for t_item in n_block['data']:
                    tmp = Transaction(
                                                t_item['from_addr'],
                                                t_item['to_addr'],
                                                t_item['value'],
                                                t_item['gas'],
                                                t_item['args'],
                                                t_item['timestamp']
                                            )
                    tmp.tx_hash = t_item['tx_hash']
                    tmp.set_transaction()

                    tmp_txs.append(tmp)

                tmp_block = Block(
                                    n_block['index'],
                                    n_block['timestamp'],
                                    tmp_txs,
                                    n_block['prev_hash'],
                                    n_block['difficulty']
                            )

                tmp_block.hash = n_block['hash']
                tmp_block.nonce = n_block['nonce']
                tmp_block.merkle_root = n_block['merkle_root']
                tmp_block.set_block()

                self.chain.append(tmp_block)

                # store the block in the database
                db.add_block(tmp_block)

                if self.miner_thread != None:
                    self.miner_thread.stop()

                # Remove txs from non mined to mined txs
                for t in tmp_txs:
                    db.add_to_mined_tx(len(self.chain), t)
                    self.transactions = list(filter(lambda tx: tx not in tmp_txs, self.transactions))

                return {
                    'status': True,
                    'new_block': tmp_block
                }
        
            return {'status': False}

    def add_transaction(self, trans, send_nodes, node_conn_exempt = None):
        if not trans['to_addr'] == None and trans['to_addr'][:2] != "SC":
            # For transactions, that involove sending coin from one address to another

            if trans['from_addr'] != None: # if funds being transferred to another account

                res = Wallet.verify_transaction(trans['signature'], trans['from_addr'], [
                    trans['from_addr'], 
                    trans['to_addr'], 
                    trans['value'], 
                    trans['gas'], 
                    str(trans['args'])
                ])

                if res['status'] == True:
                    balance = self.get_balance(trans['from_addr'])
                    if balance == 0:
                        return {
                            "status": False,
                            "message": "[FAILED], No fund in this account"
                        }
                    elif balance - int(trans['value']) - int(trans['gas']) < 0:
                        return {
                            "status": False,
                            "message": "[FAILED], Not enough fund to transact"
                        }
                    else:
                        
                        balance = balance - int(trans['value']) - int(trans['gas'])
                        if Transaction.is_valid(trans):
                            is_valid_tx = True
                            r_data = db.get_data('transactions')
                            tmp = []
                            for t in r_data:
                                tmp.append(Transaction.get_tx_object(t))

                            self.transactions = tmp
                            tmp_txs = filter(lambda x: x.from_addr == trans['from_addr'], self.transactions)
                            
                            for tx in tmp_txs:
                                if str(tx.timestamp) == trans['timestamp']:
                                    is_valid_tx = False

                            if is_valid_tx:
                                tmp_tx = Transaction(
                                                trans['from_addr'],
                                                trans['to_addr'],
                                                trans['value'],
                                                trans['gas'],
                                                trans['args'],
                                                trans['timestamp']
                                            )
                                
                                tmp_tx.set_transaction()

                                self.transactions.append(tmp_tx)
                                db.add_transaction(tmp_tx)
                                db.update_state_obj(balance, tmp_tx)

                                transaction = tmp_tx.tx_item
                                transaction['signature'] = trans['signature']
                                data = {"type": "NEW_TRANSACTION_REQUEST", "transaction": transaction}
                                
                                exclude_list = [trans['from_addr']]

                                if node_conn_exempt != None:
                                    exclude_list.append(node_conn_exempt.pk)

                                send_nodes(data, exclude_list)
                                return {
                                    "status": True,
                                    "message": "[SUCCESS] Transaction made successfully"
                                }
                            return {
                                "status": False,
                                "message": "[FAILED], Transaction has been recorded already"
                            }
                        return {
                                "status": False,
                                "message": "[FAILED], Not valid transaction"
                            }
            
            else: # if mining reward being giving to a miner
                
                balance = self.get_balance(trans['to_addr'])
                tmp_tx = Transaction(
                                            trans['from_addr'],
                                            trans['to_addr'],
                                            trans['value'],
                                            trans['gas'],
                                            trans['args'],
                                            trans['timestamp']
                                        )
                
                tmp_tx.set_transaction()

                self.transactions.append(tmp_tx)
                db.add_transaction(tmp_tx)
                db.update_state_obj(balance, tmp_tx)
                data = {"type": "NEW_TRANSACTION_REQUEST", "transaction": tmp_tx.tx_item}
                
                exclude_list = []

                if node_conn_exempt != None:
                    exclude_list.append(node_conn_exempt.pk)

                send_nodes(data, exclude_list)
                return {
                    "status": True,
                    "message": "[SUCCESS] Transaction made successfully"
                }
        
        elif trans['to_addr'] == None:  
            # For transactions initiating contract on the network

            res = Wallet.verify_transaction(trans['signature'], trans['from_addr'], trans['sign_data'])

            if res['status'] == True:
                BASE_DIR = os.path.dirname(os.path.abspath(__file__))
                contract_path = os.path.join(BASE_DIR, "contracts\{}.py".format(trans['contract_addr']))

                path = Path(contract_path)
                if not path.exists():
                    path.write_text(trans['args'][0])

                # status = db.add_to_state(trans['contract_addr'])
                tmp_tx = Transaction(
                                            trans['from_addr'],
                                            trans['to_addr'],
                                            trans['value'],
                                            trans['gas'],
                                            trans['args'],
                                            trans['timestamp']
                                        )
                
                tmp_tx.set_transaction()

                self.transactions.append(tmp_tx)
                db.add_transaction(tmp_tx)
                status = db.update_state_obj(trans['value'], tmp_tx)
                if status:
                    import imp

                    fp, path, desc = imp.find_module(str(trans['contract_addr']), path=[os.path.join(BASE_DIR, "contracts")])
                    c_module = imp.load_module(str(trans['contract_addr']), fp, path, desc)
                    sys.modules[trans['contract_addr']] = c_module

                    contract_tx = Transaction(trans['contract_addr'], None, 0, 0)
                    db.update_state_obj(0, contract_tx)

                    state = db.get_data('contracts-states')[trans['contract_addr']]
                    return_state = c_module.contract(action=trans['action'], state = state)
                    db.update_state_cont(trans['contract_addr'], return_state)
                    
                    # Stores the start and end time of each contract
                    self.contract_params[trans['contract_addr']] = trans['args'][1]
                    db.add_contract_info((
                                            trans['contract_addr'], 
                                            trans['args'][1]['start_time'], 
                                            trans['args'][1]['end_time']
                                        ))

                    data = {"type": "NEW_TRANSACTION_REQUEST", "transaction": trans}
                            
                    exclude_list = [trans['from_addr']]

                    if node_conn_exempt != None:
                        exclude_list.append(node_conn_exempt.pk)

                    send_nodes(data, exclude_list)
                    
                return {'status': True, 'message': 'Contract Instantiated Successfully'}
                
            return {'status': False, 'message': 'Transaction verification failed'}

        elif trans['to_addr'][:2] == 'SC':  
            # For transactions with a contract addresss

            res = Wallet.verify_transaction(
                trans['signature'],
                trans['from_addr'], 
                trans['sign_data']
                )

            if res['status'] == True:
                tmp = float(trans['args'][2])

                if trans['to_addr'][2:] not in self.contract_params:
                    tmp_cont = db.get_contract_info(trans['to_addr'][2:])[0]

                    self.contract_params[trans['to_addr'][2:]] = {
                        'start_time': float(tmp_cont[1]),
                        'end_time': float(tmp_cont[2])
                    }

                if tmp >= self.contract_params[trans['to_addr'][2:]]['start_time'] and tmp <= self.contract_params[trans['to_addr'][2:]]['end_time']:
                    import imp

                    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
                    fp, path, desc = imp.find_module(trans['to_addr'][2:], path=[os.path.join(BASE_DIR, "contracts")])
                    c_module = imp.load_module(trans['to_addr'][2:], fp, path, desc)
                    
                    state = db.get_data('contracts-states')[trans['to_addr'][2:]]

                    return_state = c_module.contract(action=trans['action'], state = state, args = trans['args'])
                    db.update_state_cont(trans['to_addr'][2:], return_state)
                    tmp_tx = Transaction(
                                                trans['from_addr'],
                                                trans['to_addr'],
                                                trans['value'],
                                                trans['gas'],
                                                trans['args'],
                                                trans['timestamp']
                                            )
                    
                    tmp_tx.set_transaction()

                    self.transactions.append(tmp_tx)
                    db.add_transaction(tmp_tx)

                    data = {"type": "NEW_TRANSACTION_REQUEST", "transaction": trans}            
                    exclude_list = [trans['from_addr']]

                    if node_conn_exempt != None:
                        exclude_list.append(node_conn_exempt.pk)

                    send_nodes(data, exclude_list)
                    return {'status': True, 'message': 'Contract Updated Successfully'}
                else:
                    return {'status': False, 'message': 'Contract Validity Period Expired'}

            return {'status': False, 'message': 'Transaction verification Failed!!!'}
                    
        else:
            print('Invalid Transaction')
            return {
                    "status": False,
                    "message": "[FAILED], Invalid transaction"
                }

    def tx_to_add_block(self):
        tmp_tx = []
        max_limit = 5
        counter = 0
        
        tmp_txs = db.get_data('transactions')
        txs = []
        for x in tmp_txs:

            x = list(x)
            x[4] = ast.literal_eval(x[4])
            x[5] = float(x[5])

            tmp = Transaction(x[0], x[1], x[2], x[3], x[4], x[5])
            tmp.tx_hash = x[6]
            tmp.set_transaction()

            txs.append(tmp)

        self.transactions = txs
        
        while counter < max_limit and len(self.transactions) != 0 : 
            tmp = self.transactions[0]
            tmp_i = 0

            for i, t in enumerate(self.transactions):
                if int(t.gas) > int(tmp.gas):
                    tmp_i = i
                elif int(t.gas) == int(tmp.gas):
                    if t.timestamp < tmp.timestamp:
                        tmp_i = i

            tmp_tx.append(self.transactions[tmp_i])
            self.transactions.pop(tmp_i)
            counter += 1
        return tmp_tx

    def get_balance(self, address):

        r_data = db.get_balance(address)

        if len(r_data) != 0:
            bal = int(r_data[0][0])
        else:
            db.add_to_state(address)
            bal = 0

        # return self.state[address]['balance'] if self.state[address] != None else 0
        return bal


# The join method of the thread module in python does not return any value
# This class inherits from it, and modify the join method to return a value
# Used in the miner method of the blockchain class to start a mining thread
# =========================================================================
class ThreadWithReturnValue(Thread):
            def __init__(self, group=None, target=None, name=None,
                        args=(), kwargs={}, Verbose=None):
                Thread.__init__(self, group, target, name, args, kwargs)
                self._return = None

            def stop(self):
                if not self._stop.isSet():
                    self._stop.set()

            def stopped(self):
                return self._stop.isSet()

            def run(self):
                # print(type(self._target))
                if self._target is not None:
                    self._return = self._target(*self._args,
                                                        **self._kwargs)
            
            def join(self, *args):
                Thread.join(self, *args)
                return self._return
# =========================================================================
