import socket
import json
import threading
import sys
import time

class MessageClient:
    def __init__(self, host='localhost', port=5000, retry_delay=2, max_retries=5):
        self.host = host
        self.port = port
        self.username = None
        self.client_socket = None
        self.retry_delay = retry_delay
        self.max_retries = max_retries

    def connect(self, username):
        for attempt in range(self.max_retries):
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.host, self.port))
                self.username = username
                
                # Robust username registration
                reg_message = json.dumps({'username': username})
                self.client_socket.send(reg_message.encode('utf-8'))
                
                # Start receive thread
                receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
                receive_thread.start()
                
                return True
            except ConnectionRefusedError:
                print(f"Connection attempt {attempt + 1} failed. Retrying...")
                time.sleep(self.retry_delay)
            except Exception as e:
                print(f"Connection error: {e}")
                break
        
        print("Failed to connect to server after multiple attempts.")
        return False

    def send_message(self, target, content):
        try:
            message = {
                'sender': self.username,
                'target': target,
                'content': content
            }
            self.client_socket.send(json.dumps(message).encode('utf-8'))
            print(f"Sent to {target}: {content}")
        except BrokenPipeError:
            print("Connection lost. Attempting to reconnect...")
            self.connect(self.username)
        except Exception as e:
            print(f"Send error: {e}")

    def receive_messages(self):
        while True:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    print("Server connection lost")
                    break
                
                message = json.loads(data.decode('utf-8'))
                
                if 'error' in message:
                    print(f"Error: {message['error']}")
                elif 'sender' in message:
                    print(f"\n{message['sender']}: {message['content']}")
            
            except ConnectionResetError:
                print("Connection reset by server")
                break
            except Exception as e:
                print(f"Receive error: {e}")
                break

    def start_interactive_mode(self):
        print(f"Connected as {self.username}. Type 'target:message' to send.")
        print("Type 'quit' to exit.")
        
        while True:
            try:
                message = input("> ")
                
                if message.lower() == 'quit':
                    break
                
                parts = message.split(':', 1)
                if len(parts) == 2:
                    target, content = parts[0].strip(), parts[1].strip()
                    self.send_message(target, content)
                else:
                    print("Invalid message format. Use 'target:message'")
            
            except KeyboardInterrupt:
                break
        
        if self.client_socket:
            self.client_socket.close()

def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <username>")
        sys.exit(1)
    
    client = MessageClient()
    if client.connect(sys.argv[1]):
        client.start_interactive_mode()

if __name__ == '__main__':
    main()