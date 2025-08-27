import socket
import json
import threading

class SocketClient:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.username = None
        self.message_callback = None
        
    def connect(self):
        """Kết nối đến server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            # Bắt đầu thread lắng nghe tin nhắn
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
            
    def disconnect(self):
        """Ngắt kết nối với server"""
        if self.socket:
            self.socket.close()
        self.connected = False
        self.username = None
        
    def receive_messages(self):
        """Lắng nghe tin nhắn từ server"""
        while self.connected:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if data:
                    message = json.loads(data)
                    if self.message_callback:
                        self.message_callback(message)
            except:
                break
                
    def send_message(self, message):
        """Gửi tin nhắn đến server"""
        if self.connected and self.username:
            try:
                data = json.dumps({
                    'type': 'message',
                    'username': self.username,
                    'content': message
                })
                self.socket.send(data.encode('utf-8'))
                return True
            except Exception as e:
                print(f"Send error: {e}")
                return False
        return False
        
    def login(self, username, password):
        """Gửi yêu cầu đăng nhập"""
        if not self.connected:
            if not self.connect():
                return False, "Cannot connect to server"
                
        try:
            data = json.dumps({
                'type': 'login',
                'username': username,
                'password': password
            })
            self.socket.send(data.encode('utf-8'))
            
            # Nhận phản hồi (trong thực tế cần xử lý phản hồi từ server)
            self.username = username
            return True, "Login successful"
        except Exception as e:
            return False, f"Login error: {e}"
            
    def signup(self, email, username, password):
        """Gửi yêu cầu đăng ký"""
        if not self.connected:
            if not self.connect():
                return False, "Cannot connect to server"
                
        try:
            data = json.dumps({
                'type': 'signup',
                'email': email,
                'username': username,
                'password': password
            })
            self.socket.send(data.encode('utf-8'))
            
            # Nhận phản hồi (trong thực tế cần xử lý phản hồi từ server)
            return True, "Signup successful"
        except Exception as e:
            return False, f"Signup error: {e}"
            
    def logout(self):
        """Đăng xuất"""
        if self.connected:
            try:
                data = json.dumps({
                    'type': 'logout',
                    'username': self.username
                })
                self.socket.send(data.encode('utf-8'))
            except:
                pass
        self.disconnect()
        
    def add_friend(self, username):
        """Gửi yêu cầu kết bạn"""
        if self.connected:
            try:
                data = json.dumps({
                    'type': 'add_friend',
                    'from_user': self.username,
                    'to_user': username
                })
                self.socket.send(data.encode('utf-8'))
                return True
            except:
                return False
        return False
        
    def create_group(self, group_name):
        """Tạo nhóm mới"""
        if self.connected:
            try:
                data = json.dumps({
                    'type': 'create_group',
                    'group_name': group_name,
                    'creator': self.username
                })
                self.socket.send(data.encode('utf-8'))
                return True
            except:
                return False
        return False
        
    def set_message_callback(self, callback):
        """Thiết lập callback cho tin nhắn đến"""
        self.message_callback = callback