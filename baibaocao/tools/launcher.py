# tools/launcher.py
import subprocess
import time
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    import webview
except ImportError:
    print("PyWebview chưa được cài đặt. Chạy lệnh sau:")
    print("pip install pywebview")
    sys.exit(1)

def start_server():
    """Khởi động backend server"""
    print("🔄 Khởi động backend server...")
    return subprocess.Popen([
        sys.executable, "tools/server_async.py"
    ], cwd=os.path.dirname(os.path.dirname(__file__)))

def start_gateway():
    """Khởi động HTTP gateway"""
    print("🌐 Khởi động HTTP gateway...")
    return subprocess.Popen([
        sys.executable, "tools/http_gateway.py"
    ], cwd=os.path.dirname(os.path.dirname(__file__)))

def main():
    print("🚀 Khởi động Chat App Multi-Client Launcher")
    print("=" * 50)
    
    # Khởi động backend
    server_process = start_server()
    time.sleep(2)  # Đợi server khởi động
    
    # Khởi động gateway
    gateway_process = start_gateway()
    time.sleep(1)  # Đợi gateway khởi động
    
    print("✅ Backend và Gateway đã sẵn sàng!")
    print("🌐 Web UI: http://127.0.0.1:8080/")
    print("🔌 Backend: 127.0.0.1:5555")
    print("=" * 50)
    
    try:
        print("📱 Mở Client 1...")
        # Tạo cửa sổ đầu tiên
        window1 = webview.create_window("Client 1 - User A", "http://127.0.0.1:8080/", width=1000, height=700)
        
        print("📱 Mở Client 2...")
        # Tạo cửa sổ thứ hai
        window2 = webview.create_window("Client 2 - User B", "http://127.0.0.1:8080/", width=1000, height=700)
        
        print("✅ Đã mở 2 client windows")
        print("💡 Hướng dẫn test:")
        print("   1. Đăng ký 2 user khác nhau (ví dụ: user1/user2)")
        print("   2. Gửi lời mời kết bạn từ user1 đến user2")
        print("   3. Chấp nhận lời mời ở user2")
        print("   4. Chat 1-1 giữa 2 user")
        print("   5. Tạo nhóm từ user1, thêm user2")
        print("   6. Chat nhóm")
        print("=" * 50)
        print("⏹️  Đóng cửa sổ để dừng...")
        
        # Khởi động webview (sẽ mở cả 2 cửa sổ)
        webview.start()
        
    except KeyboardInterrupt:
        print("\n🛑 Đang dừng tất cả...")
        
    finally:
        # Dừng các process
        print("🔄 Dừng gateway...")
        gateway_process.terminate()
        gateway_process.wait()
        
        print("🔄 Dừng backend...")
        server_process.terminate()
        server_process.wait()
        
        print("✅ Đã dừng tất cả!")

if __name__ == "__main__":
    main()
