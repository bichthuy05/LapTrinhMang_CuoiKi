import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

class SignupWindow:
    def __init__(self, parent, login_callback, signup_callback):
        self.parent = parent
        self.login_callback = login_callback
        self.signup_callback = signup_callback
        
        self.parent.title("Sign Up")
        self.parent.geometry("450x600")
        self.parent.configure(bg="white")
        
        self.create_widgets()
    
    def create_widgets(self):
        # Main frame với nền trắng
        self.main_frame = tk.Frame(self.parent, bg="white", padx=40, pady=40)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title - SIGNUP
        title_label = tk.Label(
            self.main_frame, 
            text="Signup",
            font=("Arial", 28, "bold"),
            foreground="#1f2937",
            bg="white"
        )
        title_label.pack(pady=(0, 20))
        
        # Email Frame
        email_frame = tk.Frame(self.main_frame, bg="white")
        email_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(email_frame, text="Enter your email", font=("Arial", 11), 
                foreground="#4b5563", bg="white").pack(anchor=tk.W, pady=(0, 5))
        
        # Frame cho ô nhập email
        email_input_frame = tk.Frame(email_frame, bg="white")
        email_input_frame.pack(fill=tk.X)
        
        entry_frame = tk.Frame(email_input_frame, bg="white", highlightbackground="#e0e0e0", 
                              highlightcolor="#e0e0e0", highlightthickness=1, bd=0)
        entry_frame.pack(fill=tk.X)
        
        self.email_entry = tk.Entry(entry_frame, font=("Arial", 12), 
                                  bg="white", fg="#1f2937", relief="flat",
                                  bd=0, highlightthickness=0,
                                  width=30)
        self.email_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, padx=(10, 0))
        
        # Thêm placeholder trống
        tk.Label(entry_frame, text="", bg="white", padx=10).pack(side=tk.RIGHT)
        
        # Username Frame
        username_frame = tk.Frame(self.main_frame, bg="white")
        username_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(username_frame, text="Username", font=("Arial", 11), 
                foreground="#4b5563", bg="white").pack(anchor=tk.W, pady=(0, 5))
        
        # Frame cho ô nhập username
        username_input_frame = tk.Frame(username_frame, bg="white")
        username_input_frame.pack(fill=tk.X)
        
        entry_frame = tk.Frame(username_input_frame, bg="white", highlightbackground="#e0e0e0", 
                              highlightcolor="#e0e0e0", highlightthickness=1, bd=0)
        entry_frame.pack(fill=tk.X)
        
        self.new_username_entry = tk.Entry(entry_frame, font=("Arial", 12), 
                                         bg="white", fg="#1f2937", relief="flat",
                                         bd=0, highlightthickness=0,
                                         width=30)
        self.new_username_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, padx=(10, 0))
        
        # Thêm placeholder trống
        tk.Label(entry_frame, text="", bg="white", padx=10).pack(side=tk.RIGHT)
        
        # Password Frame
        password_frame = tk.Frame(self.main_frame, bg="white")
        password_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(password_frame, text="Create a password", font=("Arial", 11), 
                foreground="#4b5563", bg="white").pack(anchor=tk.W, pady=(0, 5))
        
        # Frame chứa ô nhập password và con mắt
        password_input_frame = tk.Frame(password_frame, bg="white")
        password_input_frame.pack(fill=tk.X)
        
        # Frame cho ô nhập password
        entry_frame = tk.Frame(password_input_frame, bg="white", highlightbackground="#e0e0e0", 
                              highlightcolor="#e0e0e0", highlightthickness=1, bd=0)
        entry_frame.pack(fill=tk.X)
        
        self.new_password_entry = tk.Entry(entry_frame, font=("Arial", 12), 
                                         bg="white", fg="#1f2937", relief="flat",
                                         show="•", bd=0, highlightthickness=0,
                                         width=30)
        self.new_password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, padx=(10, 0))
        
        self.new_show_password_btn = tk.Label(
            entry_frame,
            text="👁",
            font=("Arial", 12),
            bg="white",
            fg="#6b7280",
            cursor="hand2",
            padx=10
        )
        self.new_show_password_btn.pack(side=tk.RIGHT)
        self.new_show_password_btn.bind("<Button-1>", lambda e: self.toggle_new_password_visibility())
        self.new_password_visible = False
        
        # Confirm Password Frame
        confirm_frame = tk.Frame(self.main_frame, bg="white")
        confirm_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(confirm_frame, text="Confirm your password", font=("Arial", 11), 
                foreground="#4b5563", bg="white").pack(anchor=tk.W, pady=(0, 5))
        
        # Frame chứa ô nhập confirm password và con mắt
        confirm_input_frame = tk.Frame(confirm_frame, bg="white")
        confirm_input_frame.pack(fill=tk.X)
        
        # Frame cho ô nhập confirm password
        confirm_entry_frame = tk.Frame(confirm_input_frame, bg="white", highlightbackground="#e0e0e0", 
                                     highlightcolor="#e0e0e0", highlightthickness=1, bd=0)
        confirm_entry_frame.pack(fill=tk.X)
        
        self.confirm_password_entry = tk.Entry(confirm_entry_frame, font=("Arial", 12), 
                                             bg="white", fg="#1f2937", relief="flat",
                                             show="•", bd=0, highlightthickness=0,
                                             width=30)
        self.confirm_password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, padx=(10, 0))
        
        self.confirm_show_password_btn = tk.Label(
            confirm_entry_frame,
            text="👁",
            font=("Arial", 12),
            bg="white",
            fg="#6b7280",
            cursor="hand2",
            padx=10
        )
        self.confirm_show_password_btn.pack(side=tk.RIGHT)
        self.confirm_show_password_btn.bind("<Button-1>", lambda e: self.toggle_confirm_password_visibility())
        self.confirm_password_visible = False

        # Signup button
        signup_btn = tk.Button(
            self.main_frame, 
            text="SIGNUP",
            font=("Arial", 11, "bold"),
            bg="#33ccff",
            fg="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.attempt_signup
        )
        signup_btn.pack(pady=(0, 10), fill=tk.X, ipady=8)
        
        # Login link
        login_frame = tk.Frame(self.main_frame, bg="white")
        login_frame.pack(fill=tk.X, pady=(5, 0))
      
        tk.Label(login_frame, text="Already have an account?", 
                font=("Arial", 10), fg="#6b7280", bg="white").pack(side=tk.LEFT)
        
        login_label = tk.Label(
            login_frame, 
            text="LOGIN",
            font=("Arial", 10, "bold"),
            fg="#33ccff",
            bg="white",
            cursor="hand2",
        )
        login_label.pack(side=tk.RIGHT)
        login_label.bind("<Button-1>", lambda e: self.open_login())
        
    def toggle_new_password_visibility(self):
        if self.new_password_visible:
            self.new_password_entry.config(show="•")
            self.new_show_password_btn.config(fg="#6b7280")
        else:
            self.new_password_entry.config(show="")
            self.new_show_password_btn.config(fg="#33ccff")
        self.new_password_visible = not self.new_password_visible
        
    def toggle_confirm_password_visibility(self):
        if self.confirm_password_visible:
            self.confirm_password_entry.config(show="•")
            self.confirm_show_password_btn.config(fg="#6b7280")
        else:
            self.confirm_password_entry.config(show="")
            self.confirm_show_password_btn.config(fg="#33ccff")
        self.confirm_password_visible = not self.confirm_password_visible

    def validate_password(self, password):
        """Kiểm tra độ mạnh mật khẩu"""
        if len(password) < 6:
            return False, "Mật khẩu phải có ít nhất 6 ký tự"
        
        has_upper = any(char.isupper() for char in password)
        has_lower = any(char.islower() for char in password)
        has_digit = any(char.isdigit() for char in password)
        has_special = any(not char.isalnum() for char in password)
        
        if not (has_upper and has_lower and has_digit and has_special):
            return False, "Mật khẩu phải chứa chữ hoa, chữ thường, số và ký tự đặc biệt"
        
        return True, ""
        
    def attempt_signup(self):
        email = self.email_entry.get().strip()
        username = self.new_username_entry.get().strip()
        password = self.new_password_entry.get()
        confirm_password = self.confirm_password_entry.get()

        # Kiểm tra không để trống
        if not all([email, username, password, confirm_password]):
            messagebox.showerror("Error", "Please fill in all fields")

        # Kiểm tra độ dài username
        if len(username) < 3:
            messagebox.showerror("Error", "Username phải có ít nhất 3 ký tự")
            return
        
        # Kiểm tra mật khẩu mạnh
        is_valid, error_msg = self.validate_password(password)
        if not is_valid:
            messagebox.showerror("Error", error_msg)
            return
        
        # Kiểm tra mật khẩu trùng khớp
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            return
        
        # Kiểm tra email hợp lệ
        if "@" not in email or "." not in email:
            messagebox.showerror("Error", "Please enter a valid email address")
            return
            
        success = self.signup_callback(email, username, password, confirm_password)
        if success:
            messagebox.showinfo("Thành công", "Đăng ký thành công! Vui lòng đăng nhập.")
            self.open_login()
            
    def open_login(self):
        """Mở cửa sổ đăng nhập"""
        from .login_window import LoginWindow
        for widget in self.parent.winfo_children():
            widget.destroy()
        login_window = LoginWindow(self.parent, self.login_callback, self.signup_callback)
        
    