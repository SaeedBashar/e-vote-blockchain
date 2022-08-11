import Crypto
import Crypto.Random
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5


class Wallet:
    def __init__(self) -> None:
        pass

    @classmethod
    def generate_key(self):
        key = RSA.generate(1024)
        priv_key = key.exportKey()
        pub_key = key.publickey().exportKey()
        
        keys = {
            'private_key': priv_key.decode(),
            'public_key': pub_key.decode()
        }

        return keys

    @classmethod
    def sign_transaction(self, pv_key, data):

        priv_key = RSA.importKey(pv_key.encode())
        signer = PKCS1_v1_5.new(priv_key)

        tmp = ""
        for x in data:
            tmp += x

        h = SHA256.new(tmp.encode())
        sig = signer.sign(h)

        return str(sig)

    @classmethod
    def verify_transaction(self, sig, pb_key, data):

        tmp = ""
        for x in data:
            tmp += x
        
        h = SHA256.new(tmp.encode())
        try:
            pub_key = RSA.importKey(pb_key.encode())
            verifier = PKCS1_v1_5.new(pub_key)

            verifier.verify(h, sig.encode())
            return {
                'status': True,
                'msg': 'Verification Success'
            }
        except ValueError as e:
            print("Verification Failed")
            return {
                'status': False,
                'msg': 'Verification Failed'
            }
        except Exception as e:
            print("Unexpected Error occured!!")
            return  {
                'status': False,
                'msg': 'Unexpected Error occured!!'
            }
