
import binascii
import os
from cryptography.fernet import Fernet

import Crypto
import Crypto.Random
from Crypto.Hash import  SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5


def gen_key_pair():
    key = RSA.generate(1024)
    private_key = key.exportKey(format='DER')
    public_key = key.publickey().exportKey(format='DER')
    
    result = {
        'private_key': (private_key.hex()),
        'public_key': (public_key.hex())
    }

    return result


def hex_key(key):
    return binascii.hexlify(key).decode('ascii')

def unhex_key(key):
    return binascii.unhexlify(key)

