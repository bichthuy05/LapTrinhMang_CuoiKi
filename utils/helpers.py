import re
import time
from datetime import datetime

def validate_email(email):
    """Kiểm tra định dạng email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    """Kiểm tra định dạng username"""
    # Username chỉ được chứa chữ cái, số, dấu gạch dưới và dấu chấm
    pattern = r'^[a-zA-Z0-9_.]+$'
    return re.match(pattern, username) is not None

def validate_password(password):
    """Kiểm tra độ mạnh mật khẩu"""
    # Ít nhất 8 ký tự, có chữ hoa, chữ thường, số và ký tự đặc biệt
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(char.isupper() for char in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(char.islower() for char in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one digit"
    
    return True, "Password is strong"

def format_timestamp(timestamp):
    """Định dạng thời gian"""
    now = time.time()
    diff = now - timestamp
    
    if diff < 60:
        return "Just now"
    elif diff < 3600:
        minutes = int(diff / 60)
        return f"{minutes}m ago"
    elif diff < 86400:
        hours = int(diff / 3600)
        return f"{hours}h ago"
    else:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")

def truncate_text(text, max_length=50):
    """Cắt ngắn văn bản nếu quá dài"""
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text