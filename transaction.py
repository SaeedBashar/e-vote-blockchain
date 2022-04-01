
###################################
## Transaction Class

class Transaction():
    def __init__(self, t, v, pv, fv, tp) -> None:
        self.timestamp = t
        self.voter_addr = v
        self.voted = False
        self.type = tp
        self.voted_candidates = {
                "president": pv,
                "finance": fv 
            }
        self.setTransaction()

    def setTransaction(self):
        self.tx_item = {
            "type": self.type,
            "timestamp": self.timestamp,
            "voter_addr" : self.voter_addr,
            "voted" : self.voted,
            "voted_candidates" : self.voted_candidates
        }

