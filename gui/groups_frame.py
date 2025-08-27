import tkinter as tk
from tkinter import ttk

class GroupsFrame:
    def __init__(self, parent, socket_client):
        self.parent = parent
        self.socket_client = socket_client
        
        self.create_widgets()
    
    def create_widgets(self):
        self.main_frame = tk.Frame(self.parent, bg="white")
        
        # Groups list
        self.groups_listbox = tk.Listbox(
            self.main_frame, 
            bg="white",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Arial", 10)
        )
        self.groups_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10), padx=10)
        
        # Thêm nhóm mẫu
        sample_groups = ["Work Team", "Family", "Friends Group", "Project Team"]
        for group in sample_groups:
            self.groups_listbox.insert(tk.END, group)
        
        # Bind sự kiện click
        self.groups_listbox.bind("<Double-Button-1>", self.on_group_select)
    
    def on_group_select(self, event):
        """Xử lý khi chọn một nhóm"""
        selection = self.groups_listbox.curselection()
        if selection:
            index = selection[0]
            group = self.groups_listbox.get(index)
            print(f"Selected group: {group}")
    
    def show(self):
        """Hiển thị frame"""
        self.main_frame.pack(fill=tk.BOTH, expand=True)
    
    def hide(self):
        """Ẩn frame"""
        self.main_frame.pack_forget()