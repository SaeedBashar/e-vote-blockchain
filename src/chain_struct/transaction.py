
###################################
## Transaction Class

class Transaction():
    def __init__(self, t, voter_addr, candidates) -> None:
        self.timestamp = t
        self.voter_addr = voter_addr
        self.voted = False
        self.voted_candidates = {
                "president": candidates['pv'],
                "finance": candidates['fv']
            }
        self.set_transaction()

    def set_transaction(self):
        self.tx_item = {
            "timestamp": self.timestamp,
            "voter_addr" : self.voter_addr,
            "voted" : self.voted,
            "voted_candidates" : self.voted_candidates
        }

