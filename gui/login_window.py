import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime, timedelta

class LoginWindow:
    def __init__(self, parent, login_callback, signup_callback):
        self.parent = parent
        self.login_callback = login_callback
        self.signup_callback = signup_callback
        self.login_attempts = 0
        self.max_attempts = 5
        self.locked_until = None
        
        self.create_widgets()
        self.load_saved_credentials()
    
    def create_widgets(self):
        # Main frame với nền trắng
        self.main_frame = tk.Frame(self.parent, bg="white", padx=40, pady=40)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title - LOGIN
        title_label = tk.Label(
            self.main_frame, 
            text="Login",
            font=("Arial", 22, "bold"),
            foreground="#1f2937",
            bg="white"
        )
        title_label.pack(pady=(0, 40))

        # Username/Email Frame
        email_frame = tk.Frame(self.main_frame, bg="white")
        email_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(email_frame, text="Enter your email or username", font=("Arial", 11), 
                foreground="#4b5563", bg="white").pack(anchor=tk.W, pady=(0, 5))
        
        # Frame cho ô nhập email
        email_input_frame = tk.Frame(email_frame, bg="white")
        email_input_frame.pack(fill=tk.X)
        
        entry_frame = tk.Frame(email_input_frame, bg="white", highlightbackground="#e0e0e0", 
                              highlightcolor="#e0e0e0", highlightthickness=1, bd=0)
        entry_frame.pack(fill=tk.X)
        
        self.username_entry = tk.Entry(entry_frame, font=("Arial", 12), 
                                     bg="white", fg="#1f2937", relief="flat",
                                     bd=0, highlightthickness=0,
                                     width=30)
        self.username_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, padx=(10, 0))
        
        # Thêm placeholder trống để cân bằng với password field
        tk.Label(entry_frame, text="", bg="white", padx=10).pack(side=tk.RIGHT)
        
        # Password Frame
        password_frame = tk.Frame(self.main_frame, bg="white")
        password_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(password_frame, text="Enter your password?", font=("Arial", 11), 
                foreground="#4b5563", bg="white").pack(anchor=tk.W, pady=(0, 5))
        
        # Frame chứa ô nhập password và con mắt
        password_input_frame = tk.Frame(password_frame, bg="white")
        password_input_frame.pack(fill=tk.X)
        
        # Frame cho ô nhập password
        entry_frame = tk.Frame(password_input_frame, bg="white", highlightbackground="#e0e0e0", 
                              highlightcolor="#e0e0e0", highlightthickness=1, bd=0)
        entry_frame.pack(fill=tk.X)
        
        self.password_entry = tk.Entry(entry_frame, font=("Arial", 12), 
                                     bg="white", fg="#1f2937", relief="flat",
                                     show="•", bd=0, highlightthickness=0,
                                     width=30)
        self.password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, padx=(10, 0))
        
        # Nút hiển thị mật khẩu
        self.show_password_btn = tk.Label(
            entry_frame,
            text="👁",
            font=("Arial", 12),
            bg="white",
            fg="#6b7280",
            cursor="hand2",
            padx=10
        )
        self.show_password_btn.pack(side=tk.RIGHT)
        self.show_password_btn.bind("<Button-1>", lambda e: self.toggle_password_visibility())
        self.password_visible = False
        
        # Forgot password
        forgot_frame = tk.Frame(self.main_frame, bg="white")
        forgot_frame.pack(fill=tk.X, pady=(0, 30))
        
        forgot_label = tk.Label(
            forgot_frame, 
            text="Forgot password?",
            font=("Arial", 10),
            fg="#33ccff",
            bg="white",
            cursor="hand2"
        )
        forgot_label.pack(side=tk.RIGHT)
        forgot_label.bind("<Button-1>", lambda e: self.forgot_password())
        
        # Login button
        login_btn = tk.Button(
            self.main_frame, 
            text="LOGIN",
            font=("Arial", 12, "bold"),
            bg="#33ccff",
            fg="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.attempt_login
        )
        login_btn.pack(pady=(0, 25), fill=tk.X, ipady=12)
        
        # Signup link
        signup_frame = tk.Frame(self.main_frame, bg="white")
        signup_frame.pack(fill=tk.X)
        
        tk.Label(signup_frame, text="Don't have an account?", 
                font=("Arial", 10), fg="#6b7280", bg="white").pack(side=tk.LEFT)
        
        signup_label = tk.Label(
            signup_frame, 
            text="SIGNUP",
            font=("Arial", 10, "bold"),
            fg="#33ccff",
            bg="white",
            cursor="hand2"
        )
        signup_label.pack(side=tk.RIGHT)
        signup_label.bind("<Button-1>", lambda e: self.open_signup())
        
    def toggle_password_visibility(self):
        if self.password_visible:
            self.password_entry.config(show="•")
            self.show_password_btn.config(fg="#6b7280")
        else:
            self.password_entry.config(show="")
            self.show_password_btn.config(fg="#33ccff")
        self.password_visible = not self.password_visible
        
    def attempt_login(self):
        """Xử lý đăng nhập với giới hạn attempt"""
        # Kiểm tra khóa tài khoản
        if self.locked_until and datetime.now() < self.locked_until:
            remaining = (self.locked_until - datetime.now()).seconds
            messagebox.showerror("Bị khóa", f"Tài khoản bị khóa. Thử lại sau {remaining} giây")
            return
        
        username_or_email = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username_or_email or not password:
            messagebox.showerror("Error", "Vui lòng điền đầy đủ thông tin")
            return
            
        self.login_attempts += 1

        # Kiểm tra số lần attempt
        if self.login_attempts >= self.max_attempts:
            self.locked_until = datetime.now() + timedelta(minutes=2)
            messagebox.showerror("Bị khóa", "Quá nhiều lần thử sai. Tài khoản bị khóa 2 phút.")
            return
            
        success = self.login_callback(username_or_email, password)
        
        if success:
            self.login_attempts = 0  # Reset attempt
            if self.remember_me.get():
                self.save_credentials(username_or_email)
            else:
                self.clear_credentials()
        else:
            remaining_attempts = self.max_attempts - self.login_attempts
            if remaining_attempts > 0:
                messagebox.showerror("Lỗi", f"Sai username hoặc password. Còn {remaining_attempts} lần thử.")
            else:
                self.locked_until = datetime.now() + timedelta(minutes=2)
                messagebox.showerror("Bị khóa", "Quá nhiều lần thử sai. Tài khoản bị khóa 2 phút.")

            
    def open_signup(self):
        """Mở cửa sổ đăng ký"""
        from .signup_window import SignupWindow
        for widget in self.parent.winfo_children():
            widget.destroy()
        signup_window = SignupWindow(self.parent, self.login_callback, self.signup_callback)
            
    def forgot_password(self):
        """Xử lý quên mật khẩu"""
        messagebox.showinfo("Quên mật khẩu", 
                            "Vui lòng liên hệ quản trị viên để reset mật khẩu.\n"
                            "Email: admin@chatapp.com\n"
                            "Hotline: 0123-456-789")       
    def save_credentials(self, username):
        config_dir = os.path.expanduser("~/.chatapp")
        os.makedirs(config_dir, exist_ok=True)
        
        with open(os.path.join(config_dir, "credentials.json"), 'w') as f:
            json.dump({'username': username}, f)

    def clear_credentials(self):
        """Xóa thông tin đã lưu"""
        config_dir = os.path.expanduser("~/.chatapp")
        config_file = os.path.join(config_dir, "credentials.json")
        if os.path.exists(config_file):
            os.remove(config_file)
            
    def load_saved_credentials(self):
        config_file = os.path.expanduser("~/.chatapp/credentials.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    self.username_entry.insert(0, data.get('username', ''))
            except:
                pass