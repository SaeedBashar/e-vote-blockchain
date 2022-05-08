import socket
import time
import threading
import json
import zlib, bz2, lzma, base64


class Node_connection(threading.Thread):

    def __init__(self, node, sock: socket.socket, id, addr, port):
        
        super(Node_connection, self).__init__()

        self.addr = addr
        self.port = port
        self.node = node
        self.sock = sock
        self.terminate_flag = threading.Event()

        # The id of the connected node
        self.id = str(id) # Make sure the ID is a string

        # End of transmission character for the network streaming messages.
        self.EOT_CHAR = 0x04.to_bytes(1, 'big')

        # Indication that the message has been compressed
        self.COMPR_CHAR = 0x02.to_bytes(1, 'big')

        # Datastore to store additional information concerning the node.
        self.info = {}

        # Use socket timeout to determine problems with the connection
        self.sock.settimeout(10.0)

        # Variables used in start_wait method
        self.cont = False
        self.response_data = None
        
        self.node.debug_print("[NEW CONNECTION]: Started with node %s:%s" % (self.addr, str(self.port)))

    def compress(self, data, compression):

        compressed = b''
        try:
            if compression == 'zlib':
                compressed = base64.b64encode( zlib.compress(data, 6) + b'zlib' )
            
            elif compression == 'bzip2':
                compressed = base64.b64encode( bz2.compress(data) + b'bzip2' )
            
            elif compression == 'lzma':
                compressed = base64.b64encode( lzma.compress(data) + b'lzma' )

            else:
                self.node.debug_print("[UNKNOWN COMPRESSION]: Compression type unknown")

        except Exception as e:
            self.node.debug_print("[COMPRESSION ERROR]: " + str(e))

        self.node.debug_print(data + ":compress:b64encode:" + str(compressed))
        self.node.debug_print(data + ":compress:compression:" + str(int(10000*len(compressed)/len(data))/100) + "%")

        return compressed

    def decompress(self, compressed):
        
        self.node.debug_print(self.id + ":decompress:input: " + str(compressed))
        compressed = base64.b64decode(compressed)
        self.node.debug_print(self.id + ":decompress:b64decode: " + str(compressed))

        try:
            if compressed[-4:] == b'zlib':
                compressed = zlib.decompress(compressed[0:len(compressed)-4])
            
            elif compressed[-5:] == b'bzip2':
                compressed = bz2.decompress(compressed[0:len(compressed)-5])
            
            elif compressed[-4:] == b'lzma':
                compressed = lzma.decompress(compressed[0:len(compressed)-4])
        except Exception as e:
            print("Exception: " + str(e))

        self.node.debug_print(self.id + ":decompress:result: " + str(compressed))

        return compressed

    def send(self, data, encoding_type='utf-8', compression='none'):
        if isinstance(data, str):
            try:
                if compression == 'none':
                    self.sock.sendall( data.encode(encoding_type) + self.EOT_CHAR )
                else:
                    data = self.compress(data.encode(encoding_type), compression)
                    self.sock.sendall(data + self.COMPR_CHAR + self.EOT_CHAR)

            except Exception as e: 
                self.node.debug_print("[ERROR]: Error sending data to node: " + str(e))
                self.stop() 

        elif isinstance(data, dict):
            try:
                if compression == 'none':
                    self.sock.sendall(json.dumps(data).encode(encoding_type) + self.EOT_CHAR)
                else:
                    data = self.compress(json.dumps(data).encode(encoding_type), compression)
                    self.sock.sendall(data + self.COMPR_CHAR + self.EOT_CHAR)

            except TypeError as type_error:
                self.node.debug_print('This dict is invalid')
                self.node.debug_print(type_error)

            except Exception as e: 
                self.node.debug_print("[ERROR]: Error sending data to node: " + str(e))
                self.stop() 

        elif isinstance(data, bytes):
            try:
                if compression == 'none':
                    self.sock.sendall(data + self.EOT_CHAR)
                else:
                    data = self.compress(data, compression)
                    self.sock.sendall(data + self.COMPR_CHAR + self.EOT_CHAR)

            except Exception as e: 
                self.node.debug_print("[ERROR]: Error sending data to node: " + str(e))
                self.stop() 

        else:
            self.node.debug_print('[INVALID DATA TYPE]: Please use str, dict (will be send as json) or bytes')

    def stop(self):
        self.terminate_flag.set()

    def parse_packet(self, packet):
        
        compression_pos = packet.find(self.COMPR_CHAR)
        if compression_pos != -1: # Check if packet was compressed
            packet = self.decompress(packet[0:compression_pos])

        try:
            packet_decoded = packet.decode('utf-8')

            try:
                return json.loads(packet_decoded)

            except json.decoder.JSONDecodeError:
                return packet_decoded

        except UnicodeDecodeError:
            return packet


    def start_wait(self):

        if self.cont:
            return
        time.sleep(1)
        self.cont = True
        return


    def run(self):
                 
        buffer = b'' # Hold the stream that comes in!

        while not self.terminate_flag.is_set():
            chunk = b''

            try:
                chunk = self.sock.recv(4096) 

            except socket.timeout:
                self.node.debug_print("NodeConnection: timeout")

            except Exception as e:
                self.terminate_flag.set() # Exception occurred terminating the connection
                self.node.debug_print('Unexpected error')
                self.node.debug_print(e)

            if chunk != b'':
                buffer += chunk
                eot_pos = buffer.find(self.EOT_CHAR)

                while eot_pos > 0:
                    packet = buffer[:eot_pos]
                    buffer = buffer[eot_pos + 1:]

                    self.node.message_count_recv += 1
                    self.node.node_message( self, self.parse_packet(packet) )

                    eot_pos = buffer.find(self.EOT_CHAR)

            time.sleep(0.01)

        self.sock.settimeout(None)
        self.sock.close()
        self.node.node_disconnected( self )
        self.node.debug_print("[CLOSED]: Connection stopped")

    def set_info(self, key, value):
        self.info[key] = value

    def get_info(self, key):
        return self.info[key]

    def __str__(self):
        return 'NodeConnection: {}:{} <-> {}:{} ({})'.format(self.node.addr, self.node.port, self.addr, self.port, self.id)

    def __repr__(self):
        return '<NodeConnection: Node {}:{} <-> Connection {}:{}>'.format(self.node.addr, self.node.port, self.addr, self.port)
