import tkinter as tk

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        """Hiển thị tooltip"""
        if self.tooltip:
            return
            
        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 5
        y = self.widget.winfo_rooty() + self.widget.winfo_height() // 2
        
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(
            self.tooltip, 
            text=self.text, 
            background="#000000", 
            foreground="#ffffff",
            relief="solid", 
            borderwidth=1,
            font=("Arial", 8)
        )
        label.pack()
    
    def hide_tooltip(self, event=None):
        """Ẩn tooltip"""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None