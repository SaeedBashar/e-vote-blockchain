import json
from pyrsistent import b

from blockchain import Blockchain
from transaction import Transaction



blockchain = Blockchain()

blockchain.add_transaction(Transaction(23, 33, 44, 5, 'block_tx'))
blockchain.add_transaction(Transaction(11, 22, 33, 6, 'block_tx'))
blockchain.add_transaction(Transaction(15, 66, 77, 7, 'block_tx'))

blockchain.add_block(blockchain.tx_to_add_block())

for b in blockchain.chain:
    print(json.dumps(b.block_item,indent=4))

print('end program')
print(blockchain.pending_tx[0].tx_item)