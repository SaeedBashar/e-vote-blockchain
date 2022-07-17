import sqlite3
import json
from pathlib import Path

import os.path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "Mudcoindb.sqlite3")


class Database:
    def __init__(self) -> None:
        pass

    @classmethod
    def get_data(self, arg):
        if arg == 'transactions':
            query = "SELECT * FROM non_mined_transactions"

            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute(query)
                return cursor.fetchall()
        elif arg == 'mined_transactions':
            query = "SELECT * FROM mined_transactions"

            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute(query)
                return cursor.fetchall()
        elif arg == 'blocks':
            query = "SELECT * FROM Chain"

            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute(query)
                return cursor.fetchall()

        elif arg == 'nodes':
            query = "SELECT * FROM connected_nodes"

            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute(query)
                return cursor.fetchall()
        elif arg == 'contracts':
            query = "SELECT * FROM state"

            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute(query)
                return cursor.fetchall()

    @classmethod
    def get_user(self, data):
        query = "SELECT * FROM Profile WHERE u_name = ? AND password = ?"

        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(query, data)
            return cursor.fetchall()

    @classmethod
    def add_user(self, data):
        query = "INSERT INTO Profile VALUES(?, ?, ?, ?, '', '')"
        try:
            with sqlite3.connect(db_path) as conn:
                conn.execute(query, data)
                conn.commit()

            return True
        except Exception as e:
            print(e)
            return False

    @classmethod
    def insert_keys(self, data):
        query = "UPDATE Profile SET private_key = ?, public_key = ? WHERE name=? and email=?"
        try:
            with sqlite3.connect(db_path) as conn:
                conn.execute(query, (
                                        data['private_key'], 
                                        data['public_key'], 
                                        data['user']['name'],
                                        data['user']['email']
                                    )
                            )
                conn.commit()
            return True
        except Exception as e:
            print(e)
            return False

    @classmethod
    def add_block(self, data):
        blk_dict = data.block_item
        blk_dict['data'] = json.dumps(blk_dict['data'])
        try:
            with sqlite3.connect(db_path) as conn:
                query = "INSERT INTO Chain VALUES(?, ?, ?, ?, ?, ?, ?, ?)"
                conn.execute(query, tuple(blk_dict.values()))
                conn.commit()
                return True
        except Exception as e:
            print(e)
            return False

    @classmethod
    def get_block(self, ind):
        with sqlite3.connect(db_path) as conn:
            query = "SELECT * FROM Chain WHERE ind = ?"
            cursor = conn.execute(query, (ind,))
            return cursor.fetchall()

    @classmethod
    def add_transaction(self, data):
        tx_dict = data.tx_item
        # tx_dict['args'] = json.dumps(tx_dict['args'])
        try:
            with sqlite3.connect(db_path) as conn:
                query = "INSERT INTO non_mined_transactions VALUES(?, ?, ?, ?, ?, ?, ?)"
                conn.execute(query, tuple(tx_dict.values()))
                conn.commit()
                return True
        except Exception as e:
            print(e)
            return False

    @classmethod
    def add_to_mined_tx(self, blk_index, data):
        try:
            with sqlite3.connect(db_path) as conn:
                query = "INSERT INTO mined_transactions VALUES(?, ?, ?, ?, ?, ?, ?, ?)"
                tx_dict = data.tx_item

                tmp = [blk_index]
                tmp.extend(list(tx_dict.values()))
                conn.execute(query, tuple(tmp))
                conn.commit()


                query = "DELETE FROM non_mined_transactions WHERE tx_hash = ?"
                conn.execute(query, (data.tx_hash,))
                conn.commit()
                return True
        except Exception as e:
            print(e)
            return False

    @classmethod
    def get_transaction(self, hash):
        with sqlite3.connect(db_path) as conn:
                query = "SELECT * FROM non_mined_transactions WHERE tx_hash = ?"
                cursor = conn.execute(query, (hash,))
                tmp = cursor.fetchall()

                if len(tmp) == 0: # if the transaction was not found in pending transactions
                    query = "SELECT * FROM mined_transactions WHERE tx_hash = ?"
                    cursor = conn.execute(query, (hash,))
                    return cursor.fetchall()
                
                return tmp

    @classmethod
    def add_connection(self, data):
        addr = data.address
        port = data.port
        pk = data.pk
        try:
            with sqlite3.connect(db_path) as conn:
                query = "INSERT INTO connected_nodes VALUES(?, ?, ?)"
                conn.execute(query, (addr,port,pk))
                conn.commit()
                print("done")
                return True
        except Exception as e:
            print('fail')
            print(e)
            return False

    @classmethod
    def get_pk(self):
        query = 'SELECT public_key FROM profile'
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(query)
            return cursor.fetchall()

    @classmethod
    def get_connected_node(self, data):
        query = 'SELECT * FROM connected_nodes where address = ? and port = ?'
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(query, data)
            return cursor.fetchall()

    @classmethod
    def get_balance(self, addr):
        query = 'SELECT balance FROM state WHERE public_key = ?'

        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(query, (addr,))
            return cursor.fetchall()

    @classmethod
    def update_state_obj(self, bal, tx):
        with sqlite3.connect(db_path) as conn:
            if tx.from_addr != None:
                # Update state for from_addr
                query = "SELECT * FROM state WHERE public_key = ?"
                cursor = conn.execute(query, (tx.from_addr,))
                r_data = cursor.fetchall()
                if len(r_data) != 0:
                    query = "UPDATE state set balance = ? where public_key = ?"
                    conn.execute(query, (bal, tx.from_addr))
                    conn.commit()
                else:
                    self.add_to_state(tx.from_addr)

            if tx.to_addr != None:
                # Update state for to_addr
                query = "SELECT * FROM state WHERE public_key = ?"
                cursor = conn.execute(query, (tx.to_addr,))
                r_data = cursor.fetchall()
                if len(r_data) != 0:
                    query = "UPDATE state set balance = ? where public_key = ?"
                    b = int(r_data[0][1])
                    b += int(tx.value)
                    conn.execute(query, (b, tx.to_addr))
                    conn.commit()
                else:
                    self.add_to_state(tx.to_addr)
                    query = "UPDATE state set balance = ? where public_key = ?"
                    conn.execute(query, (tx.value, tx.to_addr))
                    conn.commit()

        return True

    @classmethod
    def get_state(self):
        query = 'SELECT * FROM state'

        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(query)
            tmp = {}
            for s in cursor:
                tmp[s[0]] = {
                    'balance': s[1],
                    'body': s[2],
                    'timestamps': json.loads(s[3]),
                    'storage': json.loads(s[4])
                }

            return tmp

    @classmethod
    def add_to_state(self, addr):
        with sqlite3.connect(db_path) as conn:
            # Check for existence of address before inserting
            query = "SELECT public_key FROM state"
            cursor = conn.execute(query)
            for x in cursor.fetchall():
                if x[0] == addr:
                    return False

            query = "INSERT INTO state VALUES(?, ?, ?, ?, ?)"
            conn.execute(query, (addr, 0, "", json.dumps([]), json.dumps({})))
            conn.commit()
            return True

    @classmethod
    def update_state_cont(self, addr, state):
        with sqlite3.connect(db_path) as conn:
            query = "UPDATE state set balance = ?, body = ?, timestamps = ?, storage = ? where public_key = ?"
            conn.execute(query, (state['balance'], state['body'], json.dumps(state['timestamps']), json.dumps(state['storage']), addr))
            conn.commit()
            return True

    def calli(self):
        with sqlite3.connect(db_path) as conn:
            query = "select * from Movies"
            cursor = conn.execute(query)
            return cursor.fetchall()
            # for c in cursor:
            #     print(c)
            # query = "INSERT INTO Movies VALUES(?, ?, ?)"
            # for m in movies:
            #     conn.execute(query, tuple(m.values()))
            # conn.commit()
