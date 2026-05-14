import socket
import json
import threading
from PyQt5.QtCore import QThread, pyqtSignal

class ClientSocket(QThread):
    message_received = pyqtSignal(dict)
    connected = pyqtSignal()
    disconnected = pyqtSignal()

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.sock = None
        self.running = False

    def connect_to_server(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            self.running = True
            self.connected.emit()
            return True
        except Exception as e:
            print(f"[BAĞLANTI HATASI] {e}")
            return False

    def send(self, msg: dict):
        try:
            data = json.dumps(msg) + "\n"
            self.sock.sendall(data.encode())
        except Exception as e:
            print(f"[GÖNDERME HATASI] {e}")

    def run(self):
        buffer = ""
        try:
            while self.running:
                data = self.sock.recv(1024).decode()
                if not data:
                    break
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if not line.strip():
                        continue
                    msg = json.loads(line)
                    self.message_received.emit(msg)
        except Exception as e:
            print(f"[OKUMA HATASI] {e}")
        finally:
            self.running = False
            self.disconnected.emit()

    def disconnect(self):
        self.running = False
        if self.sock:
            self.sock.close()