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
    def auth_user(self, data):
        query = "Select * from Profile where u_name = ? and password = ?"

        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(query, data)
            return cursor.fetchall()

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