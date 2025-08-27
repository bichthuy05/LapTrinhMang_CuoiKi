import tkinter as tk

class EmojiPicker:
    def __init__(self, parent, message_entry):
        self.parent = parent
        self.message_entry = message_entry
        
        self.create_window()
    
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
        
        # Danh sách emoji phổ biến
        popular_emojis = ["😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "😊", "😇", 
                         "🙂", "🙃", "😉", "😌", "😍", "🥰", "😘", "😗", "😙", "😚"]
        
        emoji_frame = tk.Frame(self.emoji_window, bg="white")
        emoji_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tạo lưới emoji
        for i, emoji in enumerate(popular_emojis):
            btn = tk.Button(
                emoji_frame,
                text=emoji,
                font=("Arial", 16),
                bg="white",
                relief="flat",
                bd=0,
                cursor="hand2",
                command=lambda e=emoji: self.insert_emoji(e)
            )
            btn.grid(row=i//5, column=i%5, padx=5, pady=5)
    
    def insert_emoji(self, emoji):
        """Chèn emoji vào ô nhập tin nhắn"""
        current_text = self.message_entry.get()
        self.message_entry.delete(0, tk.END)
        self.message_entry.insert(0, current_text + emoji)
        self.emoji_window.destroy()