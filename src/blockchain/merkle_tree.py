# coding:utf-8
import hashlib
from collections import OrderedDict
import json

from src.blockchain.transaction import Transaction


class Merkle_tree(object):
    def __init__(self, transaction_list=None):
        self.transaction_list = transaction_list
        self.transactions = transaction_list
        self.transaction_tree = OrderedDict()
        self.create_tree()

    def create_tree(self):
        transaction_list = self.transaction_list
        transaction_tree = self.transaction_tree
        temp_transaction = []

        if len(transaction_list) != 0:
            if len(transaction_list) != 1:
                # print transaction_list

                for index in range(0, len(transaction_list), 2):
                    left_leaf = transaction_list[index]

                    if index + 1 != len(transaction_list):
                        right_leaf = transaction_list[index + 1]
                    else:
                        right_leaf = transaction_list[index]

                    if isinstance(left_leaf, Transaction):
                        left_leaf = left_leaf.tx_hash
                    if isinstance(right_leaf, Transaction):
                        right_leaf = right_leaf.tx_hash

                    left_leaf_hash = hashlib.sha256(str(left_leaf).encode()).hexdigest()  
                    right_leaf_hash = hashlib.sha256(str(right_leaf).encode()).hexdigest() 

                    transaction_tree[left_leaf] = left_leaf_hash
                    transaction_tree[right_leaf] = right_leaf_hash

                    temp_transaction.append(left_leaf_hash + right_leaf_hash)

                self.transaction_list = temp_transaction
                self.transaction_tree = transaction_tree
                self.create_tree()
            else:
                root_leaf = transaction_list[0]
                if isinstance(root_leaf, Transaction):
                    root_leaf = root_leaf.tx_hash
                else:
                    root_leaf = root_leaf

                root_leaf_hash = hashlib.sha256(json.dumps(root_leaf).encode()).hexdigest()
                transaction_tree[root_leaf] = root_leaf_hash
                self.transaction_tree = transaction_tree


    def get_transaction_tree(self):
        return self.transaction_tree

    def get_transaction_list(self):
        return self.transactions

    def get_root_leaf(self):
        if len(self.transaction_list) != 0:
            last_key = list(self.transaction_tree.keys())[-1]
            return self.transaction_tree[last_key]
        else:
            return hashlib.sha256(str(0).encode()).hexdigest()

