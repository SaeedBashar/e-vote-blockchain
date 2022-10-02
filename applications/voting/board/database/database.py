import sqlite3
import json
from pathlib import Path

import os.path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "board_db.sqlite3")

def signin(arg):
    query = "SELECT * FROM board WHERE uname = ? AND pword = ?"
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(query, arg)
        return cursor.fetchall()

def update_data(arg):
    query = "UPDATE board set public_key = ?, private_key = ? where uname=? and pword=?"
    with sqlite3.connect(db_path) as conn:
        conn.execute(query, arg)
        conn.commit()

    return True

def get_user(data):
    query = "SELECT * FROM board WHERE uname = ? AND pword = ?"

    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(query, data)
        return cursor.fetchall()

def add_user(data):
    query = "INSERT INTO board VALUES(?, ?, ?, ?, '', '')"
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute(query, data)
            conn.commit()

        return True
    except Exception as e:
        print(e)
        return False

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

def add_candidate(portfolio, arg):

    if portfolio == 'pres':
        query = "INSERT INTO President VALUES(?, ?, ?, ?, ?)"

        with sqlite3.connect(db_path) as conn:
            conn.execute(query, arg)
            conn.commit()
    elif portfolio == 'parl':
        query = "INSERT INTO Parliament VALUES(?, ?, ?, ?, ?)"

        with sqlite3.connect(db_path) as conn:
            conn.execute(query, arg)
            conn.commit()

# def add_party_info(arg):
#     query = "INSERT INTO Party_info VALUES(?, ?)"

#     with sqlite3.connect(db_path) as conn:
#         conn.execute(query, arg)
#         conn.commit()

# def get_party_info():
#     query = "SELECT * FROM Party_info"
#     with sqlite3.connect(db_path) as conn:
#         cursor = conn.execute(query)
#         return cursor.fetchall()
