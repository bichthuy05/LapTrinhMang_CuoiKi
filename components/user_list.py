import tkinter as tk

class UserList:
    def __init__(self, parent, users, title):
        self.parent = parent
        self.users = users
        self.title = title
        
        self.create_widgets()
    
    def create_widgets(self):
        self.main_frame = tk.Frame(self.parent, bg="white")
        
        # Title
        title_label = tk.Label(
            self.main_frame,
            text=self.title,
            font=("Arial", 12, "bold"),
            bg="white",
            fg="#555555"
        )
        title_label.pack(anchor=tk.W, pady=(10, 5), padx=10)
        
        # Listbox
        self.listbox = tk.Listbox(
            self.main_frame, 
            bg="white",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Arial", 10)
        )
        self.listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 10), padx=10)
        
        # Thêm users
        for user in self.users:
            self.listbox.insert(tk.END, user)
    
    def pack(self, **kwargs):
        self.main_frame.pack(**kwargs)
    
    def pack_forget(self):
        self.main_frame.pack_forget()