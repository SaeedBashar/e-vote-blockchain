
import binascii
import hashlib
import json
import math
import threading
from threading import Thread

import Crypto
import Crypto.Random
from Crypto.Hash import  SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

import time as tm
from time import time

from src.blockchain import keygen
from src.blockchain.transaction import Transaction
from src.blockchain.block import Block
from src.blockchain import miner

keys = keygen.gen_key_pair()
private_key = keys['private_key']
public_key = keys['public_key']
KEY_PAIR = keys['key_pair']

tmp_public_key = '30819f300d06092a864886f70d010101050003818d0030818902818100a9433cc207ef9a748188014eddf20d12433c3b15f4c1827fa6fff37061887de1a9ebb8f58821402c35aedf2a195bcf1bc5b6ea7d0a45f5bcc81a9b2fe1ec693c881aa0ad1a69dd81cd4f985ec30526885a0a629ccd6e630d9152a96b42e6b8d0df305b918d50c60ce4fe9d6694746b4343e6fc93fa5e0def1bef06098a2cad2f0203010001'

from database.database import Database as db

class Blockchain:
    def __init__(self):

        self.transactions = []

        # Get and initialize transaction objects if some exist in the database
        return_data = db.get_data('transactions')
        if len(return_data) != 0:
            for tx in return_data:
                tx_obj = Transaction.get_tx_object(tx)
                self.transactions.append(tx_obj)
        else:
            self.initial_coin_release = Transaction(None, tmp_public_key, 100000000000, 0, [], 0)
            db.add_transaction(self.initial_coin_release)
        

        self.difficulty = 4
        self.chain = []

        self.miner_thread = None

        self.block_time = 30000
        self.reward = 297

        # get and initiliaze block objects if some exist in the database
        return_data = db.get_data('blocks')
        if len(return_data) != 0:
            for blk in return_data:
                blk_obj = Block.get_blk_object(blk)
                self.chain.append(blk_obj)
        else:
            self.create_genesis_block()

        self.state = {
            tmp_public_key : {
                'balance': 100000000000,
                'body': "",
                'timestamps': [],
                'storage': {}
            }
        }

    def create_genesis_block(self):
        block = Block(0, '123456789', [self.initial_coin_release], '', self.difficulty)
        block.prev_hash = '0' * 64
        block.mine_block(self.difficulty)

        self.chain.append(block)
        db.add_block(block)

    def start_miner(self):

        self.miner_thread = ThreadWithReturnValue(target=miner.mine, name='MinerThread', args=(self,))
        self.miner_thread.start()

        mined_block = self.miner_thread.join()
        # print('from mine ')
        # print(mined_block.block_item)
        return mined_block

    def add_block(self, n_block, temp_state):

        is_valid_block = False

        if n_block['prev_hash'] != self.chain[-1].prev_hash:
            is_valid_block = True
            # if SHA256.new(n_block['index'] + 
            #                 n_block['timestamp'] + 
            #                 json.dumps(n_block['data']) +
            #                 n_block['difficulty'] +
            #                 self.chain[-1].hash + 
            #                 n_block['nonce'] + 
            #                 n_block['merkle_root']
            #                 ) != n_block['hash']:
            #     self.log("Failed first test")
            #     is_valid_block = False

            # # TODO:: temp_state will be checked later
            # if not Block.has_valid_transactions(n_block, temp_state['state']):
            #     self.log("Failed second test")
            #     is_valid_block = False

        #     if int(n_block['timestamp']) > time() or int(n_block['timetamp']) < int(self.chain[-1].timestamp):
        #         self.log("Failed third test")
        #         is_valid_block = False

        #     if n_block['prev_hash'] != self.chain[-1].prev_hash:
        #         self.log("Failed forth test")
        #         is_valid_block = False

        #     if int(n_block['index']) - 1 != int(self.chain[-1].index):
        #         self.log("Failed fifth test")
        #         is_valid_block = False

        #     if int(n_block['difficulty']) != int(self.difficulty):
        #         self.log("Failed sixth test")
        #         is_valid_block = False
                        
        # if is_valid_block:
        if int(n_block['index']) % 100 == 0:
            self.difficulty = math.ceil(self.difficulty * 100 * self.block_time / (int(n_block['timestamp']) - int(self.chain[len(self.chain)-99].timestamp)))
        
        tmp_txs = []
        for t_item in n_block['data']:
            tmp_txs.append(Transaction(
                                        t_item['from_addr'],
                                        t_item['to_addr'],
                                        t_item['value'],
                                        t_item['gas'],
                                        t_item['args'],
                                        t_item['timestamp']
                                    )
                        )

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

        self.chain.append(tmp_block)

        # store the block in the database
        db.add_block(tmp_block)

        self.miner_thread.stop()
        self.transactions = list(filter(lambda tx: Transaction.is_valid(tmp_txs)))

        return {
            'status': True,
            'new_block': tmp_block
        }
    
        # return {
        #     'status': False,
        #     'new_block': None
        # }

    def add_transaction(self, trans, send_nodes, node_conn_exempt = None):
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
            # for tx in self.transactions:
            #     if tx.from_addr == trans['from_addr']:
            #         balance -= tx.value + tx.gas

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

                    self.transactions.append(tmp_tx)
                    db.add_transaction(tmp_tx)
                    db.update_state(balance, tmp_tx)
                    data = {"type": "NEW_TRANSACTION_REQUEST", "transaction": tmp_tx.tx_item}
                    
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
                    "message": "[FAILED], Not valid transaction"
                }
            return {
                    "status": False,
                    "message": "[FAILED], Not valid transaction"
                }


    def tx_to_add_block(self):
        tmp_tx = []
        max_limit = 5
        counter = 0

        while counter < max_limit and len(self.transactions) != 0 : 
            tmp = self.transactions[0]
            tmp_i = 0

            for i, t in enumerate(self.transactions):
                if t.gas > tmp.gas:
                    tmp_i = i
                elif t.gas == tmp.gas:
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
                print(type(self._target))
                if self._target is not None:
                    self._return = self._target(*self._args,
                                                        **self._kwargs)
            def join(self, *args):
                Thread.join(self, *args)
                return self._return
