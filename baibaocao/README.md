# Chat App - Web UI + Python Backend

Ứng dụng chat với giao diện web và backend Python bất đồng bộ.

## 🚀 Tính năng

- **Authentication**: Đăng ký/Đăng nhập user
- **Friends**: Gửi lời mời kết bạn, chấp nhận, danh sách bạn bè
- **Chat 1-1**: Gửi/nhận tin nhắn, lịch sử chat
- **Groups**: Tạo nhóm, thêm thành viên, chat nhóm
- **Real-time**: Nhận tin nhắn real-time qua HTTP polling
- **Dark Mode**: Chuyển đổi giao diện sáng/tối
- **Multi-client**: Mở nhiều cửa sổ để test

## 🛠️ Cài đặt

### 1. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 2. Cấu trúc dự án
```
baibaocao/
├── tools/
│   ├── server_async.py      # Backend Python (asyncio)
│   ├── http_gateway.py      # HTTP gateway + static server
│   ├── launcher.py          # Multi-client launcher (cũ)
│   └── open_client.py       # Mở từng client riêng lẻ
├── web/
│   ├── index.html           # Giao diện chính
│   ├── app.css              # Styles (light/dark theme)
│   └── app.js               # Logic frontend
└── requirements.txt
```

## 🎯 Cách sử dụng

### Phương án 1: Chạy từng bước (Khuyến nghị)

#### Bước 1: Khởi động backend (Terminal 1)
```bash
python tools/server_async.py
```
- Backend chạy trên `127.0.0.1:5555`
- Giao thức: JSON-lines (mỗi dòng một JSON)
- **Giữ terminal này mở**

#### Bước 2: Khởi động HTTP gateway (Terminal 2)
```bash
python tools/http_gateway.py
```
- Gateway chạy trên `127.0.0.1:8080`
- Phục vụ web UI và proxy API tới backend
- **Giữ terminal này mở**

#### Bước 3: Mở từng client (Terminal 3, 4, 5...)
```bash
# Mở Client 1
python tools/open_client.py "User A"

# Mở Client 2 (terminal mới)
python tools/open_client.py "User B"

# Mở Client 3 (terminal mới)
python tools/open_client.py "User C"
```

**Ưu điểm:**
- Server chạy ổn định, không bị restart
- Mở client khi cần, đóng khi không cần
- Mỗi client có terminal riêng, dễ debug
- Có thể mở 3, 4, 5... client tùy ý

### Phương án 2: Chạy một lệnh (Launcher cũ)

```bash
python tools/launcher.py
```
- Tự động khởi động backend + gateway
- Mở 2 cửa sổ app cùng lúc
- Nhấn `Ctrl+C` để dừng tất cả

### Phương án 3: Trình duyệt web

Sau khi chạy backend + gateway:
```
http://127.0.0.1:8080/
```
- Mở nhiều tab để test multi-client
- Không cần cài pywebview

## 🧪 Test tính năng

### Test cơ bản
1. **Đăng ký 2 user**:
   - Client 1: `user1` / `pass1`
   - Client 2: `user2` / `pass2`

2. **Kết bạn**:
   - Client 1: Nhập `2` vào "Add by user_id" → "Kết bạn"
   - Client 2: Chấp nhận lời mời

3. **Chat 1-1**:
   - Click vào tên bạn trong danh sách
   - Gửi tin nhắn

4. **Tạo nhóm**:
   - Client 1: Nhập tên nhóm → "Tạo"
   - Thêm thành viên: Nhập `gid` và `uid` → "Thêm"

5. **Chat nhóm**:
   - Click vào tên nhóm
   - Gửi tin nhắn

## 🔧 Giao thức Backend

### Format tin nhắn
```json
{"type": "MSG_SEND", "data": {"to_user_id": 2, "content": "Hello!"}}
```

### Các loại tin nhắn chính
- `AUTH_LOGIN` / `AUTH_REGISTER`
- `FRIEND_REQUEST` / `FRIEND_ACCEPT` / `FRIEND_LIST`
- `MSG_SEND` / `MSG_HISTORY`
- `GROUP_CREATE` / `GROUP_ADD` / `GROUP_MSG_SEND`
- `MSG_SEEN` / `MSG_RECALL` / `MSG_REACT`

## 🌐 Web UI

### Cấu trúc
- **Header**: Logo + Dark Mode toggle
- **Sidebar**: 
  - Auth form
  - Friends management
  - Groups management
- **Chat area**: Tiêu đề + tin nhắn + composer

### Theme
- Light/Dark mode với CSS variables
- Responsive design
- Bootstrap-like styling

## 📱 Multi-Client Testing

### Cách 1: PyWebview (Desktop app)
```bash
# Terminal 1: Backend
python tools/server_async.py

# Terminal 2: Gateway
python tools/http_gateway.py

# Terminal 3: Client 1
python tools/open_client.py "User A"

# Terminal 4: Client 2  
python tools/open_client.py "User B"
```

### Cách 2: Trình duyệt
- Mở nhiều tab: `http://127.0.0.1:8080/`
- Mỗi tab là một client độc lập

## 🚨 Troubleshooting

### Lỗi thường gặp
1. **Port đã được sử dụng**:
   - Dừng process cũ: `netstat -ano | findstr :5555`
   - Hoặc đổi port trong code

2. **PyWebview không cài được**:
   - Windows: `pip install pywebview`
   - Linux: `sudo apt-get install python3-webview`

3. **Backend không khởi động**:
   - Kiểm tra Python version (>= 3.7)
   - Kiểm tra dependencies

4. **Client không mở được**:
   - Đảm bảo backend và gateway đã chạy
   - Kiểm tra port 8080 có mở không

### Logs
- Backend: Console output với asyncio
- Gateway: HTTP request logs
- Client: Status messages

## 🔮 Mở rộng

### Tính năng có thể thêm
- Database persistence (SQLite/PostgreSQL)
- File upload/avatar
- WebSocket thay cho HTTP polling
- Push notifications
- End-to-end encryption
- Voice/video call

### Cải tiến UI
- Reactions trên tin nhắn
- Typing indicators
- Unread badges
- Message search
- User profiles

## 📄 License

Dự án học tập - Mạng máy tính
