import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

import binascii

class wallet:
    def __init__(self) -> None:

        self.private_key = None
        self.public_key = None
        self.gen_random = Crypto.Random.new().read

    def generate_key(self):
        private_key = RSA.generate(1024, self.gen_random)
        public_key = self.private_key.publickey()
        
        self.private_key = binascii.hexlify(self.private_key.exportKey(format='DER')).decode('ascii')
        self.public_key = binascii.hexlify(self.public_key.exportKey(format='DER')).decode('ascii')
        
        key_pair = {
            'private_key': self.private_key,
            'public_key': self.public_key
        }
        return key_pair

    def get_key_pair(self):
        return {
            'private_key': self.private_key,
            'public_key': self.public_key
        }

    def sign_transaction(self, transaction):
        private_key = RSA.importKey(binascii.unhexlify(self.private_key))
        signer = PKCS1_v1_5.new(private_key)
        h = SHA.new(str(transaction).encode('utf8'))
        return binascii.hexlify(signer.sign(h)).decode('ascii')

    def verify_transaction(self, sender_address, signature, transaction):
        public_key = RSA.importKey(binascii.unhexlify(sender_address))
        verifier = PKCS1_v1_5.new(public_key)
        h = SHA.new(str(transaction).encode('utf8'))
        return verifier.verify(h, binascii.unhexlify(signature))
