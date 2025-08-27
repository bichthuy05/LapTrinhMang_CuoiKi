import tkinter as tk
from datetime import datetime

class MessageBubble:
    def __init__(self, parent, sender, text, is_me=False):
        self.parent = parent
        self.sender = sender
        self.text = text
        self.is_me = is_me
        
        self.create_widgets()
    
    def create_widgets(self):
        msg_frame = tk.Frame(self.parent, bg="white")
        msg_frame.pack(fill=tk.X, pady=2)
        
        if self.is_me:
            msg_frame.pack(anchor=tk.E)
        
        # Avatar
        avatar_text = self.sender[0].upper() if self.sender else "U"
        avatar_color = "#87CEEB" if self.is_me else "#C0C0C0"
        
        avatar = tk.Label(
            msg_frame,
            text=avatar_text,
            font=("Arial", 10, "bold"),
            bg=avatar_color,
            fg="white",
            width=2,
            height=1,
            relief="flat",
            bd=0
        )
        
        # Bubble tin nhắn
        bubble_bg = "#87CEEB" if self.is_me else "#C0C0C0"
        msg_text = tk.Label(
            msg_frame, 
            text=self.text,
            font=("Arial", 11),
            background=bubble_bg,
            fg="black",
            padding=(10, 8),
            borderwidth=0,
            relief="flat",
            wraplength=300,
            justify=tk.LEFT
        )
        
        # Timestamp
        timestamp = tk.Label(
            msg_frame,
            text=datetime.now().strftime("%H:%M"),
            font=("Arial", 9),
            bg="white",
            fg="#777777"
        )
        
        # Sắp xếp các thành phần
        if self.is_me:
            avatar.pack(side=tk.RIGHT, padx=(5, 0))
            msg_text.pack(side=tk.RIGHT, padx=5)
            timestamp.pack(side=tk.RIGHT, padx=5)
        else:
            avatar.pack(side=tk.LEFT, padx=(0, 5))
            msg_text.pack(side=tk.LEFT, padx=5)
            timestamp.pack(side=tk.LEFT, padx=5)