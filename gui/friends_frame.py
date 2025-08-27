import tkinter as tk
from tkinter import ttk

class FriendsFrame:
    def __init__(self, parent, socket_client, start_chat_callback):
        self.parent = parent
        self.socket_client = socket_client
        self.start_chat_callback = start_chat_callback
        self.create_widgets()
    
    def create_widgets(self):
        self.main_frame = tk.Frame(self.parent, bg="white")
        
        # Friends list
        self.friends_listbox = tk.Listbox(
            self.main_frame, 
            bg="white",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Arial", 10)
        )
        self.friends_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10), padx=10)
        
        # Thêm bạn bè mẫu
        sample_friends = ["john_doe", "jane_smith", "bob_wilson", "alice_brown"]
        for friend in sample_friends:
            self.friends_listbox.insert(tk.END, friend)
        
        # Bind sự kiện click
        self.friends_listbox.bind("<Double-Button-1>", self.on_friend_select)
    
    def on_friend_select(self, event):
        """Xử lý khi chọn một người bạn"""
        selection = self.friends_listbox.curselection()
        if selection:
            friend = self.friends_listbox.get(selection[0])
            self.start_chat_callback(friend, False)
    
    def show(self):
        """Hiển thị frame"""
        self.main_frame.pack(fill=tk.BOTH, expand=True)
    
    def hide(self):
        """Ẩn frame"""
        self.main_frame.pack_forget()