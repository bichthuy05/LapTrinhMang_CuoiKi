import socket
import threading

class SocketClient:
    def __init__(self, host='127.0.0.1', port=8888):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.connected = False

    def connect(self):
        try:
            self.sock.connect((self.host, self.port))
            self.connected = True
            threading.Thread(target=self.listen_server, daemon=True).start()
        except Exception as e:
            print(f"Không thể kết nối tới server: {e}")

    def send(self, data: str):
        if self.connected:
            self.sock.sendall(data.encode('utf-8'))

    def listen_server(self):
        while True:
            try:
                data = self.sock.recv(4096).decode('utf-8')
                if data:
                    print(f"Server gửi: {data}")
                    # TODO: Gọi protocol_handler xử lý
            except Exception as e:
                print(f"Lỗi khi nhận dữ liệu: {e}")
                break
