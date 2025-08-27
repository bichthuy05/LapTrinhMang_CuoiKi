import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

class MainWindow:
    def __init__(self, parent, username, logout_callback, socket_client):
        self.parent = parent
        self.username = username
        self.logout_callback = logout_callback
        self.socket_client = socket_client
        self.current_chat = None
        
        self.parent.geometry("1000x700")
        self.parent.title(f"CHATAPP - {username.upper()}")
        self.parent.configure(bg="#f0f2f5")
        
        # Import và khởi tạo các frame
        from gui.friends_frame import FriendsFrame
        from gui.groups_frame import GroupsFrame
        from gui.chat_frame import ChatFrame
        
        self.create_main_widgets()
        
        # Khởi tạo các frame
        self.friends_frame = FriendsFrame(self.sidebar_frame, self.socket_client, self.start_chat)
        self.groups_frame = GroupsFrame(self.sidebar_frame, self.socket_client, self.start_chat)
        self.chat_frame = ChatFrame(self.chat_container, self.username, self.socket_client)
        
        # Hiển thị friends frame mặc định
        self.show_friends()

    def get_emoji_font(self):
        """Trả về font hỗ trợ emoji màu"""
        # Thử các font hỗ trợ emoji màu
        emoji_fonts = [
            ("Segoe UI Emoji", 14),
            ("Apple Color Emoji", 14),
            ("Noto Color Emoji", 14),
            ("Android Emoji", 14),
            ("Arial", 14)  # Fallback
        ]

        return emoji_fonts[0]  # Ưu tiên Segoe UI Emoji trên Windows
        
    def create_main_widgets(self):
        # Main container
        self.main_container = tk.Frame(self.parent, bg="#f0f2f5")
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header - Tên ở giữa
        header_frame = tk.Frame(self.main_container, bg="#2d89ef", height=60)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)
        
        # Tên ứng dụng ở giữa header
        self.header_title = tk.Label(
            header_frame, 
            text=f"CHAT APP - {self.username.upper()}", 
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#2d89ef"
        )
        self.header_title.pack(expand=True)
        
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
        
        # Thanh tìm kiếm với các biểu tượng
        search_frame = tk.Frame(self.sidebar_frame, bg="white")
        search_frame.pack(fill=tk.X, pady=(10, 5), padx=10)
        
        # Biểu tượng "Thêm bạn"
        self.add_friend_btn = tk.Label(
            search_frame,
            text="👥",
            font=("Arial", 14),
            bg="white",
            fg="#555555",
            cursor="hand2",
            padx=5
        )
        self.add_friend_btn.pack(side=tk.LEFT)
        self.add_friend_btn.bind("<Enter>", lambda e: self.show_simple_tooltip("Thêm bạn"))
        self.add_friend_btn.bind("<Leave>", lambda e: self.hide_simple_tooltip())
        self.add_friend_btn.bind("<Button-1>", self.add_friend)
        
        # Biểu tượng "Tạo nhóm chat"
        self.create_group_btn = tk.Label(
            search_frame,
            text="👪",
            font=("Arial", 14),
            bg="white",
            fg="#555555",
            cursor="hand2",
            padx=5
        )
        self.create_group_btn.pack(side=tk.LEFT)
        self.create_group_btn.bind("<Enter>", lambda e: self.show_simple_tooltip("Tạo nhóm chat"))
        self.create_group_btn.bind("<Leave>", lambda e: self.hide_simple_tooltip())
        self.create_group_btn.bind("<Button-1>", self.create_group)
        
        # Ô tìm kiếm
        self.search_entry = tk.Entry(
            search_frame,
            width=15,
            font=("Arial", 10),
            relief="flat",
            bd=1,
            bg="#f5f5f5"
        )
        self.search_entry.insert(0, "Search...")
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(5, 0))
        
        # Biểu tượng kính lúp
        search_icon = tk.Label(
            search_frame,
            text="🔍",
            font=("Arial", 12),
            bg="#f5f5f5",
            fg="#555555",
            padx=5
        )
        search_icon.pack(side=tk.RIGHT, fill=tk.Y, ipadx=5)
        
        # Tab selection
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
        
        # Tạo label cho tooltip đơn giản
        self.tooltip_label = tk.Label(
            self.sidebar_frame,
            text="",
            bg="#000000",
            foreground="#ffffff",
            font=("Arial", 8),
            relief="solid",
            borderwidth=1
        )
    
    def show_simple_tooltip(self, text):
        """Hiển thị tooltip đơn giản"""
        self.tooltip_label.config(text=text)
        self.tooltip_label.place(x=50, y=50)  # Vị trí tạm thời
    
    def hide_simple_tooltip(self):
        """Ẩn tooltip"""
        self.tooltip_label.place_forget()
    
    def add_friend(self, event):
        """Xử lý thêm bạn"""
        username = simpledialog.askstring("Thêm bạn", "Nhập username bạn muốn thêm:")
        if username:
            success = self.socket_client.add_friend(username)
            if success:
                messagebox.showinfo("Thành công", f"Đã gửi lời mời kết bạn tới {username}")
            else:
                messagebox.showerror("Lỗi", "Không thể thêm bạn")
    
    def create_group(self, event):
        """Xử lý tạo nhóm chat"""
        group_name = simpledialog.askstring("Tạo nhóm chat", "Nhập tên nhóm:")
        if group_name:
            success = self.socket_client.create_group(group_name)
            if success:
                messagebox.showinfo("Thành công", f"Đã tạo nhóm {group_name}")
            else:
                messagebox.showerror("Lỗi", "Không thể tạo nhóm")
    
    def show_friends(self):
        """Hiển thị danh sách bạn bè"""
        self.friends_tab.config(bg="#2d89ef", fg="white")
        self.groups_tab.config(bg="#e0e0e0", fg="#555555")
        self.groups_frame.hide()
        self.friends_frame.show()
    
    def show_groups(self):
        """Hiển thị danh sách nhóm"""
        self.friends_tab.config(bg="#e0e0e0", fg="#555555")
        self.groups_tab.config(bg="#2d89ef", fg="white")
        self.friends_frame.hide()
        self.groups_frame.show()
    
    def start_chat(self, name, is_group=False):
        """Bắt đầu chat với bạn bè hoặc nhóm"""
        self.current_chat = {"name": name, "is_group": is_group}
        self.chat_frame.update_chat_title(name, is_group)