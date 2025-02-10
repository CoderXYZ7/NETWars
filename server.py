import socket
import threading
import json
import traceback
import select

class MessageServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = {}
    
    def start(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            self.server_socket.setblocking(False)
            
            print(f"Server listening on {self.host}:{self.port}")
            
            self.accept_connections()
        except Exception as e:
            print(f"Server startup error: {e}")
            traceback.print_exc()
    
    def accept_connections(self):
        inputs = [self.server_socket]
        
        while inputs:
            try:
                readable, _, _ = select.select(inputs, [], [], 1)
                
                for sock in readable:
                    if sock is self.server_socket:
                        client_socket, address = self.server_socket.accept()
                        client_socket.setblocking(False)
                        inputs.append(client_socket)
                        print(f"Connection from {address}")
                    else:
                        try:
                            self.handle_client_message(sock)
                        except (ConnectionResetError, BrokenPipeError):
                            inputs.remove(sock)
                            sock.close()
            
            except Exception as e:
                print(f"Connection accept error: {e}")
                break
    
    def handle_client_message(self, client_socket):
        try:
            data = client_socket.recv(1024)
            if not data:
                # Client disconnected
                return
            
            message = json.loads(data.decode('utf-8'))
            
            if 'username' in message:
                # Registration
                username = message['username']
                self.clients[username] = client_socket
                print(f"User {username} registered")
            else:
                # Message routing
                target = message.get('target')
                if target in self.clients:
                    target_socket = self.clients[target]
                    target_socket.send(json.dumps({
                        'sender': message['sender'],
                        'content': message['content']
                    }).encode('utf-8'))
                else:
                    client_socket.send(json.dumps({
                        'error': f'Target {target} not found'
                    }).encode('utf-8'))
        
        except json.JSONDecodeError:
            print("Invalid JSON received")
        except Exception as e:
            print(f"Client message error: {e}")
            traceback.print_exc()

if __name__ == '__main__':
    server = MessageServer()
    server.start()