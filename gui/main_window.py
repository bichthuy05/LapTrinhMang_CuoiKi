import tkinter as tk
from tkinter import ttk

class MainWindow:
    def __init__(self, parent, username, logout_callback, socket_client):
        self.parent = parent
        self.username = username
        self.logout_callback = logout_callback
        self.socket_client = socket_client
        
        self.parent.geometry("1000x700")
        self.parent.title(f"CHATAPP - {username.upper()}")
        self.parent.configure(bg="#f0f2f5")
        
        # Import và khởi tạo các frame
        from gui.friends_frame import FriendsFrame
        from gui.groups_frame import GroupsFrame
        from gui.chat_frame import ChatFrame
        
        self.create_main_widgets()
        
        # Khởi tạo các frame
        self.friends_frame = FriendsFrame(self.sidebar_frame, self.socket_client)
        self.groups_frame = GroupsFrame(self.sidebar_frame, self.socket_client)
        self.chat_frame = ChatFrame(self.chat_container, self.username, self.socket_client)
        
        # Hiển thị friends frame mặc định
        self.show_friends()
        
    def create_main_widgets(self):
        # Main container
        self.main_container = tk.Frame(self.parent, bg="#f0f2f5")
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header - Tên ở giữa như trong ảnh
        header_frame = tk.Frame(self.main_container, bg="#2d89ef", height=60)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)
        
        # Tên ứng dụng ở giữa header
        title_label = tk.Label(
            header_frame, 
            text=f"CHAT APP - {self.username.upper()}", 
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#2d89ef"
        )
        title_label.pack(expand=True)  # Căn giữa
        
        # Nút logout ở bên phải
        logout_btn = tk.Button(
            header_frame,
            text="Logout",
            font=("Arial", 10, "bold"),
            bg="#1e6ac8",
            fg="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.logout_callback
        )
        logout_btn.pack(side=tk.RIGHT, padx=10)
        
        # Main content area
        content_frame = tk.Frame(self.main_container, bg="#f0f2f5")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left sidebar
        self.sidebar_frame = tk.Frame(content_frame, width=250, bg="white", relief="flat", bd=1)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        self.sidebar_frame.pack_propagate(False)
        
        # Thanh tìm kiếm (nằm trên FRIENDS/GROUPS)
        search_frame = tk.Frame(self.sidebar_frame, bg="white")
        search_frame.pack(fill=tk.X, pady=(10, 5), padx=10)
        
        search_entry = tk.Entry(
            search_frame,
            width=20,
            font=("Arial", 10),
            relief="flat",
            bd=1,
            bg="#f5f5f5"
        )
        search_entry.insert(0, "Search...")
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(5, 0))
        
        search_icon = tk.Label(
            search_frame,
            text="🔍",
            font=("Arial", 12),
            bg="#f5f5f5",
            fg="#555555",
            padx=5
        )
        search_icon.pack(side=tk.RIGHT, fill=tk.Y, ipadx=5)
        
        # Tab selection - FRIENDS và GROUPS nằm ngang
        tabs_frame = tk.Frame(self.sidebar_frame, bg="white")
        tabs_frame.pack(fill=tk.X, pady=(0, 5), padx=10)
        
        # Friends tab
        self.friends_tab = tk.Label(
            tabs_frame, 
            text="FRIENDS", 
            font=("Arial", 12, "bold"),
            bg="#2d89ef",
            fg="white",
            padx=20,
            pady=8,
            cursor="hand2",
            relief="flat"
        )
        self.friends_tab.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.friends_tab.bind("<Button-1>", lambda e: self.show_friends())
        
        # Groups tab
        self.groups_tab = tk.Label(
            tabs_frame, 
            text="GROUPS", 
            font=("Arial", 12, "bold"),
            bg="#e0e0e0",
            fg="#555555",
            padx=20,
            pady=8,
            cursor="hand2",
            relief="flat"
        )
        self.groups_tab.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        self.groups_tab.bind("<Button-1>", lambda e: self.show_groups())
        
        # Main chat area
        self.chat_container = tk.Frame(content_frame, bg="white", relief="flat", bd=1)
        self.chat_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    
    def show_friends(self):
        """Hiển thị danh sách bạn bè"""
        self.friends_tab.config(bg="#2d89ef", fg="white")
        self.groups_tab.config(bg="#e0e0e0", fg="#555555")
        
        # Ẩn groups frame, hiện friends frame
        self.groups_frame.hide()
        self.friends_frame.show()
    
    def show_groups(self):
        """Hiển thị danh sách nhóm"""
        self.friends_tab.config(bg="#e0e0e0", fg="#555555")
        self.groups_tab.config(bg="#2d89ef", fg="white")
        
        # Ẩn friends frame, hiện groups frame
        self.friends_frame.hide()
        self.groups_frame.show()