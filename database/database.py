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
