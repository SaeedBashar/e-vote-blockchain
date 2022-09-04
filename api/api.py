
from util.util import *
from flask import request

class API:
    def __init__(self):
        pass

    @classmethod
    def get_url(self, arg):

        if arg == 'blocks':
            return get_blocks()
        
        elif arg == 'transactions':
            return get_transactions()
        
        elif arg == 'mined-transactions':
            return get_mined_transactions()

        elif arg == 'contracts':
            return get_contracts()

        elif arg == 'block':
            return get_block()

        elif arg == 'transaction':
            return get_transaction()

        elif arg == 'contract':
            addr = request.args.get('address', None)
            return get_contract(addr)

        elif arg == 'contract-transactions':
            addr = request.args.get('address', None)
            return get_contract_transactions(addr)