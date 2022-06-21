
###################################
## Transaction Class

import hashlib
import json


class Transaction():
    def __init__(self, t, voter_addr, candidates) -> None:
        self.timestamp = int(t)
        self.voter_addr = voter_addr
        self.voted = False
        self.voted_candidates = {
                "pv": candidates['pv'],
                "fv": candidates['fv']
            }
        self.tx_hash = self.get_hash()
        self.set_transaction()

    def set_transaction(self):
        self.tx_item = {
            "timestamp": self.timestamp,
            "voter_addr" : self.voter_addr,
            "voted" : self.voted,
            "voted_candidates" : self.voted_candidates,
            'tx_hash': self.tx_hash
        }

    def get_hash(self):
        str_val = str(self.timestamp) + str(self.voter_addr) + str(self.voted) + json.dumps(self.voted_candidates)
        return hashlib.sha256(str_val.encode()).hexdigest()

