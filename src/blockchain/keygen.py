
import binascii
from cryptography.fernet import Fernet

import Crypto
import Crypto.Random
from Crypto.Hash import  SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

from pathlib import Path
import json

path = Path('data/keypair.json')

def gen_key_pair():
    key = RSA.generate(1024)
    private_key = key.exportKey(format='DER')
    public_key = key.publickey().exportKey(format='DER')
    
    result = {
        'private_key': hex_key(private_key),
        'public_key': hex_key(public_key)
    }

    result1 = result.copy()
    result1['key_pair'] = key
    return result1

def hex_key(key):
    return binascii.hexlify(key).decode('ascii')

def unhex_key(key):
    return binascii.unhexlify(key)

# use for and encrypting and decrypting text
def get_sym_key():
    p = Path('sym_key.txt')

    if not p.exists():
        key = Fernet.generate_key()
        p.write_bytes(key)

    cipher = Fernet(p.read_bytes())

    return cipher


