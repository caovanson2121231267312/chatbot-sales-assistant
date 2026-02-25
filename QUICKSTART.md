# 🚀 Hướng dẫn chạy nhanh - Quick Start Guide

## Bước 1: Cài đặt Python packages

```bash
pip install -r requirements.txt
```

## Bước 2: Cấu hình Database

### 2.1. Tạo file .env

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

### 2.2. Chỉnh sửa file .env

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=ecommerce_chatbot
DB_USER=root
DB_PASSWORD=your_password_here
```

### 2.3. Khởi tạo database

```bash
python database/db_config.py
```

✅ Script sẽ tự động:
- Tạo database
- Tạo tất cả bảng
- Load dữ liệu mẫu (sản phẩm, mã giảm giá, FAQ...)

## Bước 3: Train Model

```bash
rasa train
```

⏱️ Quá trình train mất khoảng 5-10 phút.

## Bước 4: Chạy Chatbot

### Option A: Test nhanh trong terminal

```bash
rasa shell
```

### Option B: Chạy đầy đủ với web interface

**Mở Terminal 1 - Action Server:**
```bash
rasa run actions
```

**Mở Terminal 2 - Rasa Server:**
```bash
rasa run --enable-api --cors "*"
```

**Mở trình duyệt:**
- Mở file: `rasa-webchat/index.html`

## 🎉 Xong! Bây giờ bạn có thể chat

### Thử các câu hỏi sau:

```
👋 Chào hỏi:
- Xin chào
- Hi

🔍 Tìm sản phẩm:
- Tìm iPhone
- Có laptop không?
- Cho xem điện thoại Samsung

💰 Hỏi giá:
- iPhone 15 giá bao nhiêu?
- Giá MacBook

📦 Kiểm tra hàng:
- iPhone 15 còn hàng không?
- Còn màu đen không?

🎁 Khuyến mãi:
- Có mã giảm giá không?
- Khuyến mãi gì?

📋 Đơn hàng:
- Kiểm tra đơn hàng
- Theo dõi vận chuyển
```

## ⚠️ Lưu ý quan trọng

1. **Cần chạy cả 2 terminal** (action server + rasa server) để chatbot hoạt động đầy đủ
2. **Port mặc định:**
   - Rasa server: 5005
   - Action server: 5055
3. **Nếu gặp lỗi:** Kiểm tra MySQL đã chạy và thông tin trong `.env` đúng

## 🐛 Troubleshooting nhanh

### Lỗi: "Connection refused"
```bash
# Kiểm tra MySQL đã chạy
# Windows: Mở Services, tìm MySQL
# Linux: sudo systemctl status mysql
```

### Lỗi: "Module not found"
```bash
pip install -r requirements.txt --force-reinstall
```

### Lỗi: "Port already in use"
```bash
# Đổi port trong file endpoints.yml hoặc config.yml
# Hoặc kill process đang dùng port đó
```

## 📚 Tài liệu đầy đủ

Xem file `README.md` để biết thêm chi tiết về:
- Cấu trúc project
- Tùy chỉnh chatbot
- Thêm sản phẩm mới
- Deploy production
- Và nhiều hơn nữa...

---

**Chúc bạn thành công! 🎊**
