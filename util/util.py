import binascii
import json
from database.database import Database as db
from flask import request
from datetime import datetime as dt


def get_blocks(trunc = False):
    tmp = []
    r_data = db.get_data('blocks')
    for b in r_data:
        tmp.append({
            'index': b[0],
            'timestamp': b[1],
            'difficulty': b[3],
            'merkle_root': b[4],
            'prev_hash': b[5],
            'nonce': b[6],
            'hash': (b[7][:15] if b[7] != None else b[7]) if trunc else b[7]
        })

    return tmp

def get_block():
    index = request.args.get('index', 0)
    r_data = db.get_block(index)
    block = {
        'index': r_data[0][0],
        'timestamp': r_data[0][1],
        'data': r_data[0][2].replace("}", "}\n\n"),
        'difficulty': r_data[0][3],
        'merkle_root': r_data[0][4],
        'prev_hash': r_data[0][5],
        'nonce': r_data[0][6],
        'hash': r_data[0][7]
    }

    return block

def get_transactions(trunc = False):
    tmp_tx = []
    r_data = db.get_data('transactions')
    for tx in r_data:
        from_addr = format_key_for_display(tx[0])
        to_addr = format_key_for_display(tx[1])

        tmp_tx.append({
            "from_addr": (from_addr[:15] if tx[0] != None else tx[0]) if trunc else tx[0],
            "to_addr": (to_addr[:15] if tx[1] != None else tx[1]) if trunc else tx[1],
            "value": tx[2],
            "gas": tx[3],
            "args": json.loads(tx[4]),
            "timestamp": tx[5],
            "tx_hash": tx[6]
        })

    return tmp_tx

def get_transaction():
    tx_hash = request.args.get('hash')
    r_data = db.get_transaction(tx_hash)
    
    if len(r_data[0]) == 7: # 7 is the number of columns for pending txs in the database
        from_addr = format_key_for_display(r_data[0][0])
        to_addr = format_key_for_display(r_data[0][1])

        tx = {
                "from_addr": from_addr,
                "to_addr": to_addr,
                "value": r_data[0][2],
                "gas": r_data[0][3],
                "args": r_data[0][4],
                "timestamp": r_data[0][5],
                "tx_hash": r_data[0][6]
            }
    else:
        from_addr = format_key_for_display(r_data[0][1])
        to_addr = format_key_for_display(r_data[0][2])

        tx = {
                "from_addr": from_addr,
                "to_addr": to_addr,
                "value": r_data[0][3],
                "gas": r_data[0][4],
                "args": r_data[0][5],
                "timestamp": r_data[0][6],
                "tx_hash": r_data[0][7]
            }

    return tx

def get_mined_transactions(trunc = False):
    tmp_tx1 = []
    r_data = db.get_data('mined_transactions')
    for tx in r_data:
        from_addr = format_key_for_display(tx[1])
        to_addr = format_key_for_display(tx[2])

        tmp_tx1.append({
            "block_index": tx[0],
            "from_addr": (from_addr[:15] if tx[1] != None else tx[1]) if trunc else tx[1],
            "to_addr": (to_addr[:15] if tx[2] != None else tx[2]) if trunc else tx[2],
            "value": tx[3],
            "gas": tx[4],
            "args": json.loads(tx[5]),
            "timestamp": tx[6],
            "tx_hash": tx[7]
        })

    return tmp_tx1

def get_contracts(trunc = False):
    tmp = []
    r_data = db.get_data('contracts-states')
    if trunc:
        for b in r_data:
            tmp.append({
                'address': b[:40] if b != None else b,
                'balance': r_data[b]['balance']
            })
        return tmp
    else:
        return r_data

def get_contract(addr):

    res_data = db.get_contract_info(addr)
    if len(res_data) != 0:
        d1 = dt.now()
        t1 = dt.timestamp(d1)
        
        if t1 < float(res_data[0][1]):
            return {'status': False, 'message': 'No Such Contract!!'}
        
        elif t1 >= float(res_data[0][1]) and t1 <= float(res_data[0][2]):
            return {'status': False, 'message': 'Contract is still in progress, can not get result now.!!'}
        
        else:
            state = db.get_state(addr)[0]
            data = {
                'status': True,
                'contract_result': json.loads(state[4])
            }
            return data

    return {'status': False, 'message': 'No Such Contract!!'}

def get_contract_transactions(addr):
    cont_txs = []

    cont_txs.extend(get_transactions())

    cont_txs.extend(get_mined_transactions())

    cont_txs = list(filter(lambda tx: tx['to_addr'] != None, cont_txs))
    cont_txs = list(filter(lambda tx: tx['to_addr'][2:] == addr, cont_txs))

    return cont_txs

def format_key_for_display(key, type='pub'):
    if key != None:
        if type == 'pub':
            key = key[27 : len(key) - 25]
            return binascii.hexlify(key.encode()).decode().upper()
        else:
            key = key[32 : len(key) - 30]
            return binascii.hexlify(key.encode()).decode().upper()
    else:
        return key

def format_key_for_use(key, type="pub"):
    pub_start = '-----BEGIN PUBLIC KEY-----\n'
    pub_end = '\n-----END PUBLIC KEY-----'

    priv_start = '-----BEGIN RSA PRIVATE KEY-----\n'
    priv_end = '\n-----END RSA PRIVATE KEY-----'

    if key != None:
        if key[:2].upper() != "SC":
            if type == 'pub':
                key = binascii.unhexlify(key.lower()).decode()
                key = f"{pub_start}{key}{pub_end}"
                return key

            else:
                key = binascii.unhexlify(key.lower()).decode()
                key = f"{priv_start}{key}{priv_end}"
                return key
        return key
    else:
        return key
