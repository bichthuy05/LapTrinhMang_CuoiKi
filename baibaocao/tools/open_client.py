# tools/open_client.py
import sys
import os

try:
    import webview
except ImportError:
    print("PyWebview chưa được cài đặt. Chạy lệnh sau:")
    print("pip install pywebview")
    sys.exit(1)

def main():
    # Lấy tên client từ command line argument
    client_name = sys.argv[1] if len(sys.argv) > 1 else "Chat Client"
    
    print(f"📱 Mở {client_name}...")
    print("🌐 Kết nối tới: http://127.0.0.1:8080/")
    print("💡 Đảm bảo server và gateway đã chạy!")
    print("=" * 50)
    
    try:
        # Tạo cửa sổ client
        window = webview.create_window(
            client_name, 
            "http://127.0.0.1:8080/", 
            width=1000, 
            height=700
        )
        
        # Khởi động webview
        webview.start()
        
    except Exception as e:
        print(f"❌ Lỗi mở client: {e}")
        print("💡 Kiểm tra server và gateway đã chạy chưa?")

if __name__ == "__main__":
    main()
