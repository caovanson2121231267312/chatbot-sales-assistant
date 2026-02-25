# Chạy Rasa Bot bằng Docker (MySQL bên ngoài)

Docker Compose chạy 4 service tương đương 3 lệnh local của bạn:

| Local (3 lệnh) | Docker service |
|----------------|----------------|
| `docker run -p 8888:8000 rasa/duckling` | **duckling** (8888:8000) |
| `rasa run --enable-api --cors "*" --debug --connector socketio` | **rasa** (5005:5005) |
| `watchmedo auto-restart ... python -m rasa_sdk --debug --port 5055 --actions actions` | **action_server** (5055:5055) |
| (webchat) | **web** (8080:80) |

MySQL **không** chạy trong Docker; bot kết nối tới MySQL bên ngoài (máy host hoặc server khác) qua biến môi trường.

---

## 1. Chuẩn bị

- Cài [Docker](https://docs.docker.com/get-docker/) và [Docker Compose](https://docs.docker.com/compose/install/).
- MySQL đã chạy sẵn (local hoặc server), đã tạo database và import schema (xem `database/schema.sql`, `database/sample_data.sql`).

---

## 2. Cấu hình MySQL (kết nối từ container)

Tạo file `.env` từ mẫu (trong thư mục gốc project):

```bash
copy .env.example .env
# (Linux/Mac: cp .env.example .env)
```

Sửa `.env`:

- **MySQL trên cùng máy host (Windows/Mac):**  
  `DB_HOST=host.docker.internal`
- **MySQL trên cùng máy host (Linux):**  
  `DB_HOST=172.17.0.1` hoặc IP máy (vd `192.168.1.100`)
- **MySQL trên server khác:**  
  `DB_HOST=<IP hoặc hostname server>`

Ví dụ `.env`:

```env
DB_HOST=host.docker.internal
DB_PORT=3306
DB_NAME=ecommerce_chatbot
DB_USER=root
DB_PASSWORD=mat_khau_mysql
```

---

## 3. Chạy bằng Docker Compose

Trong thư mục gốc project (có `docker-compose.yml`):

```bash
docker compose up -d
```

Hoặc build lại rồi chạy:

```bash
docker compose build
docker compose up -d
```

Xem log:

```bash
docker compose logs -f
# Hoặc từng service:
docker compose logs -f rasa
docker compose logs -f action_server
docker-compose run --rm rasa train
```

---

## 4. Các cổng và truy cập

| Service | Cổng | Mô tả |
|---------|------|--------|
| Rasa + Socket.IO | **5005** | Backend chat (webchat gọi tới đây) |
| Action server | **5055** | Custom actions (Rasa gọi nội bộ) |
| Duckling | **8888** | Entity extraction (nếu dùng) |
| Webchat | **8080** | Mở trình duyệt: http://localhost:8080 |

---

## 5. Dừng / gỡ

```bash
docker compose down
```

Chỉ dừng không xóa volume:

```bash
docker compose stop
```

---

## 6. Chạy từng service (không dùng Compose)

Nếu muốn chạy tách từng phần (giống 3 lệnh local):

**Terminal 1 – Duckling:**

```bash
docker run -p 8888:8000 --name duckling rasa/duckling
```

**Terminal 2 – Action server (cần có `.env` và MySQL đã chạy):**

```bash
docker build -t rasa-action .
docker run -p 5055:5055 --env-file .env -v "%cd%\actions:/app/actions" -v "%cd%\database:/app/database" rasa-action
```

**Terminal 3 – Rasa:**

```bash
docker run -p 5005:5005 -v "%cd%:/app" -v "%cd%\endpoints.docker.yml:/app/endpoints.yml" rasa/rasa:3.1.0 run --enable-api --cors "*" --debug --connector socketio
```

Lưu ý: khi chạy Rasa và action server bằng hai container riêng, Rasa phải gọi được tới action server (vd cùng mạng Docker hoặc dùng IP máy host). Dùng `docker compose` sẽ tự tạo network và tên `action_server` cho đơn giản.

---

## 7. Lưu ý

- **Model:** Rasa dùng model trong thư mục `models/`. Đảm bảo đã train và có ít nhất một file `.tar.gz` trong `models/`.
- **Webchat:** Trong `rasa-webchat` cấu hình đúng URL backend (vd `http://localhost:5005` khi test trên máy).
- **Sửa code actions:** Sau khi sửa file trong `actions/`, cần restart action server:  
  `docker compose restart action_server`
