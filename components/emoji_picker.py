import tkinter as tk

class EmojiPicker:
    def __init__(self, parent, message_entry):
        self.parent = parent
        self.message_entry = message_entry
        self.create_window()

    def get_emoji_font(self):
        """Trả về font hỗ trợ emoji màu"""
        # Ưu tiên các font hỗ trợ emoji màu
        emoji_fonts = [
            ("Segoe UI Emoji", 16),
            ("Apple Color Emoji", 16), 
            ("Noto Color Emoji", 16),
            ("Android Emoji", 16),
            ("Arial", 16)  # Fallback
        ]
        return emoji_fonts[0]  # Ưu tiên Segoe UI Emoji
    
    def create_window(self):
        """Tạo cửa sổ chọn emoji"""
        self.emoji_window = tk.Toplevel(self.parent)
        self.emoji_window.title("Select Emoji")
        self.emoji_window.geometry("300x200")
        self.emoji_window.resizable(False, False)
        self.emoji_window.configure(bg="white")
        
        # Center the window
        self.emoji_window.update_idletasks()
        x = (self.parent.winfo_screenwidth() // 2) - (300 // 2)
        y = (self.parent.winfo_screenheight() // 2) - (200 // 2)
        self.emoji_window.geometry(f'300x200+{x}+{y}')
        
        # Sử dụng font hỗ trợ emoji (thử các font phổ biến)
        emoji_font = self.get_emoji_font()

        # Danh sách emoji phổ biến
        popular_emojis = ["😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "😊", "😇", 
                         "🙂", "🙃", "😉", "😌", "😍", "🥰", "😘", "😗", "😙", "😚"]
        
        emoji_frame = tk.Frame(self.emoji_window, bg="white")
        emoji_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tạo lưới emoji với font hỗ trợ emoji màu
        for i, emoji in enumerate(popular_emojis):
            btn = tk.Button(
                emoji_frame,
                text=emoji,
                font=emoji_font,  # Sử dụng font emoji
                bg="white",
                fg="black",
                relief="flat",
                bd=0,
                cursor="hand2",
                command=lambda e=emoji: self.insert_emoji(e)
            )
            btn.grid(row=i//8, column=i%8, padx=2, pady=2)

            # Thêm hiệu ứng khi di chuột
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#f0f0f0"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg="white"))
    
    def get_emoji_font(self):
        """Trả về font hỗ trợ emoji"""
        # Thử các font phổ biến hỗ trợ emoji
        possible_fonts = ["Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji", "Arial Unicode MS"]
        for font in possible_fonts:
            try:
                test_font = (font, 12)
                return test_font
            except tk.TclError:
                continue
        return ("Arial", 12)

    def insert_emoji(self, emoji):
        """Chèn emoji vào ô nhập tin nhắn"""
        current_text = self.message_entry.get()
        self.message_entry.delete(0, tk.END)
        self.message_entry.insert(0, current_text + emoji)
        self.emoji_window.destroy()