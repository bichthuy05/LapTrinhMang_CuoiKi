import tkinter as tk
from tkinter import ttk
from datetime import datetime
from components.message_bubble import MessageBubble

class ChatFrame:
    def __init__(self, parent, username, socket_client):
        self.parent = parent
        self.username = username
        self.socket_client = socket_client
        
        self.create_widgets()
        self.add_sample_messages()
    
    def create_widgets(self):
        # Main frame
        self.main_frame = tk.Frame(self.parent, bg="white")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Chat header
        chat_header = tk.Frame(self.main_frame, height=60, bg="#f5f5f5")
        chat_header.pack(fill=tk.X)
        chat_header.pack_propagate(False)
        
        chat_info_frame = tk.Frame(chat_header, bg="#f5f5f5")
        chat_info_frame.pack(side=tk.LEFT, padx=15)
        
        chat_avatar = tk.Label(
            chat_info_frame,
            text="G",
            font=("Arial", 14, "bold"),
            bg="#87CEEB",
            fg="white",
            width=3,
            height=1,
            relief="flat",
            bd=0
        )
        chat_avatar.pack(side=tk.LEFT, padx=(0, 10))
        
        self.chat_title = tk.Label(
            chat_info_frame, 
            text="GROUP CHAT", 
            font=("Arial", 14, "bold"),
            bg="#f5f5f5"
        )
        self.chat_title.pack(side=tk.LEFT)
        
        # Messages area
        messages_container = tk.Frame(self.main_frame, bg="white")
        messages_container.pack(fill=tk.BOTH, expand=True)
        
        # Canvas và scrollbar
        self.message_canvas = tk.Canvas(messages_container, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(messages_container, orient="vertical", command=self.message_canvas.yview)
        self.scrollable_frame = tk.Frame(self.message_canvas, bg="white")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.message_canvas.configure(scrollregion=self.message_canvas.bbox("all"))
        )
        
        self.message_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.message_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.message_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Message input area - QUAN TRỌNG: THANH NHẬP TIN NHẮN
        input_frame = tk.Frame(self.main_frame, height=70, bg="#f5f5f5")
        input_frame.pack(fill=tk.X, side=tk.BOTTOM)
        input_frame.pack_propagate(False)
        
        input_inner_frame = tk.Frame(input_frame, bg="#f5f5f5", padx=10, pady=10)
        input_inner_frame.pack(fill=tk.BOTH, expand=True)
        
        # Emoji button
        emoji_btn = tk.Button(
            input_inner_frame,
            text="😊",
            font=("Arial", 14),
            bg="#f5f5f5",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.show_emoji_picker
        )
        emoji_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Message entry
        self.message_entry = tk.Entry(
            input_inner_frame,
            font=("Arial", 12),
            relief="flat",
            bd=1,
            bg="white"
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 10))
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        
        # Send button
        send_btn = tk.Button(
            input_inner_frame,
            text="➤",
            font=("Arial", 14, "bold"),
            bg="#2d89ef",
            fg="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.send_message
        )
        send_btn.pack(side=tk.RIGHT)
    
    def add_message(self, sender, text, is_me=False):
        """Thêm tin nhắn vào khung chat"""
        MessageBubble(self.scrollable_frame, sender, text, is_me)
        
        # Cuộn xuống dưới cùng
        self.scrollable_frame.update_idletasks()
        self.message_canvas.yview_moveto(1.0)
    
    def add_sample_messages(self):
        """Thêm tin nhắn mẫu vào khung chat"""
        self.add_message("john_doe", "Hello there! How are you?", False)
        self.add_message("me", "I'm good, thanks for asking!", True)
        self.add_message("john_doe", "What are you working on today?", False)
        self.add_message("me", "I'm building a chat app with Python!", True)
    
    def show_emoji_picker(self):
        """Hiển thị bảng chọn emoji"""
        from components.emoji_picker import EmojiPicker
        EmojiPicker(self.parent, self.message_entry)
        
    def send_message(self):
        """Gửi tin nhắn"""
        message = self.message_entry.get().strip()
        if message:
            self.add_message("me", message, True)
            self.socket_client.send_message(message)
            self.message_entry.delete(0, tk.END)