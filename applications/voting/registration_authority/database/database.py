import sqlite3
import json
from pathlib import Path

import os.path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "evoting.sqlite3")

def auth_registrar(arg):
    query = "SELECT * FROM Registrar WHERE name = ? AND pword = ?"
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
            print(out)
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