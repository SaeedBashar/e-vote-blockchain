import sqlite3
import json
from pathlib import Path

import os.path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "evoting.sqlite3")

def add_registrar(data):
    query = "INSERT INTO Registrar VALUES(?, ?, ?, ?, '', '')"
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute(query, data)
            conn.commit()

        return True
    except Exception as e:
        print(e)
        return False

def get_registrar(arg):
    query = "SELECT * FROM Registrar WHERE uname = ? AND pword = ?"

    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(query, arg)
        return cursor.fetchall()

def update_registrar_info(arg):
    query = "UPDATE Registrar set public_key = ?, private_key = ? where uname=? and pword=?"
    with sqlite3.connect(db_path) as conn:
        conn.execute(query, arg)
        conn.commit()

    return True

def auth_registrar(arg):
    query = "SELECT * FROM Registrar WHERE uname = ? AND pword = ?"
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(query, arg)
        return cursor.fetchall()

def get_data(arg, data):
    if arg == 'voterId':
        query = "SELECT voterId FROM Voters WHERE username = ? AND password = ?"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(query, data)
            return cursor.fetchall()[0][0]

    elif arg == 'user':
        query = "SELECT * FROM Voters WHERE voterId = ?"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(query, data)
            out = cursor.fetchall()[0]
            return out

def get_user(data):
    query = "SELECT * FROM Voters WHERE username = ? AND password = ?"

    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(query, data)
        return cursor.fetchall()

def insert_voter_id(id, data):
    query = "UPDATE Voters set voterId = ? where username = ? and password = ?"

    with sqlite3.connect(db_path) as conn:
        conn.execute(query, (id, data[0], data[1]))
        conn.commit()
        
def insert_user_vote(id):
    query = "UPDATE Voters set hasVoted = ? where voterId = ?"

    with sqlite3.connect(db_path) as conn:
        conn.execute(query, (1, id))
        conn.commit()

def verify_user(id):
    query = "Insert into Verification_table values(?, ?)"

    with sqlite3.connect(db_path) as conn:
        conn.execute(query, (id, 1))
        conn.commit()

def check_if_verified(id):
    query = "SELECT * FROM Verification_table WHERE id = ?"

    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(query, (id,))
        x = cursor.fetchall()
        if len(x) != 0:
            return x[0]

        return x

def add_candidate(portfolio, arg):

    if portfolio == 'pres':
        query = "INSERT INTO President VALUES(?, ?, ?, ?, ?, ?)"

        with sqlite3.connect(db_path) as conn:
            conn.execute(query, arg)
            conn.commit()
    elif portfolio == 'parl':
        query = "INSERT INTO Parliament VALUES(?, ?, ?, ?, ?, ?)"

        with sqlite3.connect(db_path) as conn:
            conn.execute(query, arg)
            conn.commit()

def add_party(arg):
    query = "INSERT INTO Party VALUES(?, ?, ?)"

    with sqlite3.connect(db_path) as conn:
        conn.execute(query, arg)
        conn.commit()

def get_presidents():
    query = "SELECT * FROM President"
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(query)
        return cursor.fetchall()

def get_parliaments():
    query = "SELECT * FROM Parliament"
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(query)
        return cursor.fetchall()

def get_parliaments_by_constituency(arg):
    query = "SELECT * FROM Parliament WHERE constituency = ?"
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(query, (arg, ))
        return cursor.fetchall()

def get_parties():
    query = "SELECT * FROM Party"
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(query)
        return cursor.fetchall()
        
def get_party_name(arg):
    query = "SELECT name FROM Party where id = ?"
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(query, (arg,))
        return cursor.fetchall()[0][0]

def create_election(arg):
    try:
        query = "Insert into election values(?, ?, ?)"
        with sqlite3.connect(db_path) as conn:
            conn.execute(query, arg)
            conn.commit()

            return True
    except:
        return False

def get_election(arg=''):
    query = "SELECT * FROM Election"
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(query)
        return cursor.fetchall()

def update_election(res, arg=''):
    query = "UPDATE Election set result = ?"
    with sqlite3.connect(db_path) as conn:
        conn.execute(query, (json.dumps(res),))
        conn.commit()

    return True