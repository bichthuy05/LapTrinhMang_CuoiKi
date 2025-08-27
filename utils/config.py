import json
import os

class Config:
    def __init__(self):
        self.config_file = os.path.expanduser("~/.chatapp/config.json")
        self.config_dir = os.path.dirname(self.config_file)
        self.config = self.load_config()
        
    def load_config(self):
        """Tải cấu hình từ file"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
        
    def save_config(self):
        """Lưu cấu hình vào file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except:
            return False
            
    def get(self, key, default=None):
        """Lấy giá trị cấu hình"""
        return self.config.get(key, default)
        
    def set(self, key, value):
        """Thiết lập giá trị cấu hình"""
        self.config[key] = value
        return self.save_config()
        
    def delete(self, key):
        """Xóa giá trị cấu hình"""
        if key in self.config:
            del self.config[key]
            return self.save_config()
        return False