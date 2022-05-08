import time
import json
import hashlib

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as PKCS1_v1_5_Cipher
from Crypto.Signature import PKCS1_v1_5 as PKCS1_v1_5_Signature
from Crypto.Hash import  SHA256
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto import Random
from base64 import b64decode, b64encode

from src.node_pack.node import Node
from src.chain_struct.blockchain import Blockchain


class SecureNode(Node):

    # Python class constructor
    def __init__(self, host, port, callback=None):
        
        super(SecureNode, self).__init__(host, port, callback)

        self.discovery_messages = {}

        self.rsa_key = None

        # self.blockchain = Blockchain()

    def node_message(self, conn_node, message):
        
        #try:
        print("node_message from " + conn_node.id + ": " + str(message))

        if self.check_message(message):
            if ( '_type' in message ):
                if (message['_type'] == 'ping'):
                    self.received_ping(conn_node, message)

                elif (message['_type'] == 'pong'):
                    self.received_pong(conn_node, message)
                    
                elif (message['_type'] == 'discovery'):
                    self.received_discovery(conn_node, message)

                elif (message['_type'] == 'discovery_answer'):
                    self.received_discovery_answer(conn_node, message)

                else:
                    self.debug_print("node_message: message type unknown: " + conn_node.id + ": " + str(message))

        else:
            print("Received message is corrupted and cannot be processed!")
               
    def create_message(self, data):
        
        for el in ['_id', '_timestamp', '_message_id', '_hash', '_signature', '_public_key']: # Clean up the data, to make sure we calculatie the right things!
            if ( el in data ):
                del data[el]

        try:
            data['_mcs']        = self.message_count_send
            data['_mcr']        = self.message_count_recv
            data['_id']         = self.id
            data['_timestamp']  = time.time()
            data['_message_id'] = self.get_hash(data)

            self.debug_print("Message creation:")
            self.debug_print("Message hash based on: " + self.get_data_uniq_string(data))

            data['_hash']       = self.get_hash(data)

            self.debug_print("Message signature based on: " + self.get_data_uniq_string(data))

            data['_signature']  = self.sign_data(data)
            data['_public_key'] = self.get_public_key().decode('utf-8')

            self.debug_print("_hash: " + data['_hash'])
            self.debug_print("_signature: " + data['_signature'])
            self.debug_print("_public_key: " + data['_public_key'])

            return data

        except Exception as e:
            self.debug_print("SecureNode: Failed to create message " + str(e))

    def check_message(self, data):
        
        self.debug_print("Incoming message information:")
        # self.debug_print("_hash: " + data['_hash'])
        # self.debug_print("_signature: " + data['_signature'])

        # signature  = data['_signature']
        # public_key = data['_public_key']
        # data_hash  = data['_hash']
        # message_id = data['_message_id']
        # timestamp  = data['_timestamp']

        # 1. Check the signature!
        # del data['_public_key']
        # del data['_signature']
        # checkSignature = self.verify_data(data, public_key, signature)
        
        # 2. Check the hash of the data
        # del data['_hash']
        # checkDataHash = (self.get_hash(data) == data_hash)

        # 3. Check the message id
        # del data['_message_id']
        # checkMessageId = (self.get_hash(data) == message_id)

        # 4. Restore the data
        # data['_signature']  = signature
        # data['_public_key'] = public_key
        # data['_hash']       = data_hash
        # data['_message_id'] = message_id
        # data['_timestamp']  = timestamp

        # self.debug_print("Checking incoming message:")
        # self.debug_print(" signature : " + str(checkSignature))
        # self.debug_print(" data hash : " + str(checkDataHash))
        # self.debug_print(" message id: " + str(checkMessageId))

        # return checkSignature and checkDataHash and checkMessageId

        return True

    def send_message(self, message):
        
        self.send_to_nodes(self.create_message({ "_type": "message", "message": message }))

    #######################################################
    # Hashing of Python variables methods                 #
    #######################################################

    def get_data_uniq_string(self, data):
        
        return json.dumps(data, sort_keys=True)

    def get_hash(self, data):
        
        try:
            h = hashlib.sha256()
            message = self.get_data_uniq_string(data)

            self.debug_print("Hashing the data:")
            self.debug_print("Message: " + message)

            h.update(message.encode("utf-8"))

            self.debug_print("Hash of the message: " + h.hexdigest())

            return h.hexdigest()

        except Exception as e:
            print("Failed to hash the message: " + str(e))

    #######################################################
    # RSA En-Decryption methods                           #
    #######################################################

    def get_public_key(self):
        return self.rsa_key.publickey().exportKey("PEM")

    def get_private_key(self):
        return self.rsa_key.exportKey("PEM")

    def encrypt(self, message, public_key):
        try:
            key = RSA.importKey(public_key)
            cipher = PKCS1_v1_5_Cipher.new(key)
            return b64encode( cipher.encrypt(message) )

        except Exception as e:
            print("Failed to encrypt the message: " + str(e))

    def decrypt(self, ciphertext):
        try:
            ciphertext = b64decode( ciphertext )
            cipher = PKCS1_v1_5_Cipher.new(self.rsa_key)
            sentinal = "sentinal" # What is this again?
            return cipher.decrypt(ciphertext, sentinal)

        except Exception as e:
            print("Failed to decrypt the message: " + str(e))

    def sign(self, message):
        try:
            message_hash = SHA256.new(message.encode('utf-8'))

            self.debug_print("Signing the message:")
            self.debug_print("Message to be hashed: " + message)
            self.debug_print("Hash of the message: " + message_hash.hexdigest())

            signer = PKCS1_v1_5_Signature.new(self.rsa_key)
            signature = b64encode(signer.sign(message_hash))
            return signature.decode('utf-8')

        except Exception as e:
            print("Failed to sign the message: " + str(e))

    def sign_data(self, data):
        
        message = self.get_data_uniq_string(data)        
        return self.sign(message)

    def verify(self, message, public_key, signature):
        try:
            signature = b64decode( signature.encode('utf-8') )
            key = RSA.importKey(public_key)
            h = SHA256.new(message.encode('utf-8'))
            verifier = PKCS1_v1_5_Signature.new(key)
            
            self.debug_print("Message to verify: " + message)
            self.debug_print("Hash of the message: " + h.hexdigest())
            
            return verifier.verify(h, signature)

        except Exception as e:
            self.debug_print("verify: " + str(e))

    def verify_data(self, data, public_key, signature):
        
        message = self.get_data_uniq_string(data)
        return self.verify(message, public_key, signature)

    #######################################################
    # AES En-Decryption methods                           #
    #######################################################

    def encryption_key_from_password(self, salt, password, total_bytes_key):
        
        key = PBKDF2(password, salt, total_bytes_key)
        self.debug_print("encryption_key_from_password salt: " + str(salt))
        self.debug_print("encryption_key_from_password  key: " + str(key))
        return key

    def encrypt_aes_pad(self, s):
        
        return s + b"\0" * (AES.block_size - len(s) % AES.block_size)

    def encrypt_aes(self, plaintext, key, key_size=256):
        plaintext = self.encrypt_aes_pad(plaintext)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return iv + cipher.encrypt(plaintext)

    def encrypt_aes_pw(self, plaintext, password):
        plaintext = self.encrypt_aes_pad(plaintext)
        salt = Random.new().read(16)
        key = self.encryption_key_from_password(salt, password, 32) # 256-bit key
        return salt + self.encrypt_aes(plaintext, key)

    def decrypt_aes(self, ciphertext, key):
        iv = ciphertext[:AES.block_size]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        plaintext = cipher.decrypt(ciphertext[AES.block_size:])
        return plaintext.rstrip(b"\0")

    def decrypt_aes_pw(self, ciphertext, password):
        salt = ciphertext[:16]
        key = self.encryption_key_from_password(salt, password, 32) # 256-bit key
        return self.decrypt_aes(ciphertext[16:], key)

    def encrypt_aes_file(self, file_name, plaintext, key):
        enc = self.encrypt_aes(plaintext, key)
        with open(file_name, 'wb') as fo:
            fo.write(enc)

    def decrypt_aes_file(self, file_name, key):
        with open(file_name, 'rb') as fo:
            ciphertext = fo.read()
        return self.decrypt_aes(ciphertext, key)

    def encrypt_aes_file_pw(self, file_name, plaintext, password):
        enc = self.encrypt_aes_pw(plaintext, password)
        with open(file_name, 'wb') as fo:
            fo.write(enc)

    def decrypt_aes_file_pw(self, file_name, password):
        with open(file_name, 'rb') as fo:
            ciphertext = fo.read()
        return self.decrypt_aes_pw(ciphertext, password)

    #######################################################
    # Public and private key storage and retrieval        #
    #######################################################

    def key_pair_generate (self):
        self.rsa_key = RSA.generate(4096)

    def key_pair_save (self, file_name, password):
        try:
            key_string = self.rsa_key.exportKey('PEM', password)
            key_string = self.encrypt_aes_pw(key_string, password)
            with open(file_name, 'wb') as fo:
                fo.write(key_string)

        except Exception as e:
            self.debug_print("key_pair_generate: " + str(e))

    def key_pair_load (self, file_name, password):
        try:
            with open(file_name, 'rb') as fo:
                key_string = self.decrypt_aes_pw(fo.read(), password)
                self.rsa_key = RSA.importKey(key_string, password)

        except Exception as e:
            self.debug_print("key_pair_generate: " + str(e))

    #######################################################
    # PING / PONG Message packets                         #
    #######################################################

    def send_ping(self):
        self.send_to_nodes(self.create_message( {'_type': 'ping', 'timestamp': time.time(), 'id': self.id} ))

    def send_pong(self, node, timestamp):
        node.send(self.create_message( {'_type': 'pong', 'timestamp': timestamp, 'timestamp_node': time.time(), 'id': self.id} ))

    def received_ping(self, node, data):
        self.send_pong(node, data['timestamp'])

    def received_pong(self, node, data):
        latency = time.time() - data['timestamp']
        node.set_info('ping', latency)
        self.debug_print("Received pong message with latency " + str(latency))

    #######################################################
    # DISCOVERY                                           #
    #######################################################

    def send_discovery(self):
        
        self.send_to_nodes(self.create_message({'_type': 'discovery', 'id': self.id, 'timestamp': time.time() }))

    def send_discovery_answer(self, node, data):
       
        nodes = []
        for n in self.nodes_inbound:
            nodes.append({'id': n.id, 'ip': n.host, 'port': n.main_node.port, 'connection': 'inbound'})
        for n in self.nodes_outbound:
            nodes.append({'id': n.id, 'ip': n.host, 'port': n.port, 'connection': 'outbound'})

        node.send(self.create_message({'id': data['id'], '_type': 'discovery_answer', 'timestamp': data['timestamp'], 'nodes': nodes}))

    def received_discovery(self, node, data):
        
        if data['id'] in self.discovery_messages:
            self.debug_print("discovery_message: message already received, so not sending it")

        else:
            self.debug_print("discovery_message: process message")
            self.discovery_messages[data['id']] = node
            self.send_discovery_answer(node, data)
            self.send_to_nodes(self.create_message({'_type': 'discovery', 'id': data['id'], 'timestamp': data['timestamp']}), [node])

    def received_discovery_answer(self, node, data):
        
        if data['id'] in self.discovery_messages: # needs to be relayed
            self.send_discovery_answer(self.discovery_messages[data['id']], data)

        else:
            if ( data['id'] == self.id ):
                self.debug_print("discovery_message_answer: This is for me!: " + str(data) + ":" + str(time.time()-data['timestamp']))

            else:
                self.debug_print("unknwon state!")
