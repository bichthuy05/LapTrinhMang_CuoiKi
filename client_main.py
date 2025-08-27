import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import sys
import os

# Thêm đường dẫn để import các module từ cùng thư mục
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import các module GUI
from gui.login_window import LoginWindow
from gui.main_window import MainWindow

class SocketClient:
    """Lớp giả lập kết nối socket cho demo"""
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.connected = True  # Luôn kết nối cho demo
        self.username = None
        
    def connect(self):
        return True
        
    def login(self, username, password):
        # Kiểm tra đăng nhập đơn giản
        if username and password:
            self.username = username
            return True, "Login successful"
        return False, "Login failed"
        
    def signup(self, email, username, password):
        # Kiểm tra đăng ký đơn giản
        if email and username and password:
            return True, "Signup successful"
        return False, "Signup failed"
        
    def logout(self):
        self.username = None
        
    def add_friend(self, username):
        return True
        
    def create_group(self, group_name):
        return True
        
    def send_message(self, message):
        return True

class ChatAppClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Chat App")
        self.root.geometry("450x600")
        self.root.resizable(False, False)
        self.root.configure(bg="white")
        
        # Center the window
        self.center_window()
        
        # Kết nối mạng (demo)
        self.socket_client = SocketClient()
        
        # Biến để lưu trạng thái
        self.current_user = None
        
        # Hiển thị màn hình đăng nhập đầu tiên
        self.show_login_screen()
        
    def center_window(self):
        """Căn giữa cửa sổ"""
        self.root.update_idletasks()
        width = 450
        height = 600
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def show_login_screen(self):
        """Hiển thị màn hình đăng nhập"""
        for widget in self.root.winfo_children():
            widget.destroy()
            
        self.login_window = LoginWindow(
            self.root, 
            self.handle_login, 
            self.handle_signup,
        )
        
    def show_main_app(self, username):
        """Hiển thị màn hình chính sau khi đăng nhập thành công"""
        for widget in self.root.winfo_children():
            widget.destroy()
            
        self.main_window = MainWindow(
            self.root, 
            username,
            self.handle_logout,
            self.socket_client
        )
        
    def handle_login(self, username_or_email, password):
        """Xử lý sự kiện đăng nhập - nhận email hoặc username"""
        # Gửi yêu cầu đăng nhập đến server
        success, message = self.socket_client.login(username_or_email, password)
        try: 
            if success:
                self.current_user = username_or_email
                self.show_main_app(username_or_email)
                return True
            else:
                messagebox.showerror("Login Failed", message)
                return False
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi kết nối: {str(e)}")
            return False
            
    def handle_signup(self, email, username, password, confirm_password):
        """Xử lý sự kiện đăng ký"""
        # Kiểm tra mật khẩu trùng khớp
        try:
            if password != confirm_password:
                messagebox.showerror("Signup Failed", "Passwords do not match")
                return False
                
            # Kiểm tra định dạng email
            if "@" not in email or "." not in email:
                messagebox.showerror("Error", "Please enter a valid email address")
                return False
                
            # Gửi yêu cầu đăng ký đến server
            success, message = self.socket_client.signup(email, username, password)
            
            if success:
                messagebox.showinfo("Signup Success", message)
                return True
            else:
                messagebox.showerror("Signup Failed", message)
                return False
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi kết nối: {str(e)}")
            return False
            
    def handle_logout(self):
        """Xử lý sự kiện đăng xuất"""
        self.socket_client.logout()
        self.current_user = None
        self.show_login_screen()
        
    def run(self):
        """Chạy ứng dụng"""
        self.root.mainloop()

if __name__ == "__main__":
    app = ChatAppClient()
    app.run()