# Hướng dẫn Deploy Rasa Chatbot lên Server Production

## Yêu cầu server

| Thành phần | Tối thiểu | Khuyến nghị |
|---|---|---|
| CPU | 4 vCPU | 8 vCPU |
| RAM | 8 GB | 16 GB |
| Disk | 40 GB | 80 GB SSD |
| OS | Ubuntu 20.04+ | Ubuntu 22.04 LTS |
| Port mở | 22, 80, 443 | 22, 80, 443 |

---

## Bước 1 — Chuẩn bị máy local

### 1.1 Tạo SSH key (nếu chưa có)

```bash
ssh-keygen -t ed25519 -C "deploy-rasa" -f ~/.ssh/rasa_deploy
# Nhấn Enter 2 lần (không cần passphrase cho CI/CD)
```

Lấy public key để thêm vào server:

```bash
cat ~/.ssh/rasa_deploy.pub
# Copy toàn bộ nội dung dòng này
```

### 1.2 Tạo file .env.production

```bash
cp .env.production.example .env.production
```

Mở file `.env.production` và điền thông tin thật:

```env
# Database
DB_HOST=mysql                        # Giữ nguyên nếu dùng MySQL trong Docker
DB_PORT=3306
DB_NAME=ecommerce_chatbot
DB_USER=rasa
DB_PASSWORD=MatKhauManhCuaBan123!    # ← Đổi thành password mạnh
DB_ROOT_PASSWORD=RootPassword456!    # ← Đổi thành password root mạnh

# CORS: Thay * bằng domain thật khi có domain
RASA_CORS_ORIGINS=*

# Docker Hub (nếu dùng CI/CD)
DOCKER_IMAGE_PREFIX=your-dockerhub-username
APP_VERSION=latest

# Ports
HTTP_PORT=80
HTTPS_PORT=443
```

> **Lưu ý:** File `.env.production` đã được thêm vào `.gitignore`, không bao giờ commit file này lên Git.

---

## Bước 2 — Cài đặt server

SSH vào server:

```bash
ssh root@YOUR_SERVER_IP
# hoặc nếu dùng key:
ssh -i ~/.ssh/rasa_deploy ubuntu@YOUR_SERVER_IP
```

### 2.1 Cập nhật hệ thống

```bash
apt update && apt upgrade -y
apt install -y curl git rsync ufw
```

### 2.2 Cài Docker

```bash
curl -fsSL https://get.docker.com | sh

# Thêm user hiện tại vào group docker (không cần sudo mỗi lần)
usermod -aG docker $USER

# Kiểm tra
docker --version
# Docker version 24.x.x, build ...
```

### 2.3 Cài Docker Compose

```bash
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose

chmod +x /usr/local/bin/docker-compose

# Kiểm tra
docker-compose --version
# Docker Compose version v2.x.x
```

### 2.4 Cấu hình Firewall

```bash
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable

# Kiểm tra
ufw status
```

### 2.5 Thêm SSH public key vào server

Trên server, thêm public key từ bước 1.1:

```bash
mkdir -p ~/.ssh
echo "PASTE_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

### 2.6 Tạo thư mục deploy

```bash
mkdir -p /opt/rasa-chatbot
cd /opt/rasa-chatbot
```

---

## Bước 3 — Deploy lần đầu (thủ công)

Chạy từ **máy local** (không phải server):

### 3.1 Cấp quyền script

```bash
chmod +x deploy.sh
```

### 3.2 Chạy deploy

```bash
PROD_HOST=YOUR_SERVER_IP \
PROD_USER=ubuntu \
SSH_KEY=~/.ssh/rasa_deploy \
./deploy.sh
```

Script sẽ tự động:
1. Sync toàn bộ code lên server
2. Sync models (40MB mỗi file, chỉ copy file chưa có)
3. Build Docker image action server
4. Khởi động tất cả services
5. Chạy health check

### 3.3 Kiểm tra sau deploy

SSH vào server và kiểm tra:

```bash
cd /opt/rasa-chatbot

# Xem trạng thái các container
docker-compose -f docker-compose.prod.yml ps

# Kết quả mong đợi:
# NAME                  STATUS
# rasa_mysql            Up (healthy)
# rasa_duckling         Up (healthy)
# rasa_action_server    Up (healthy)
# rasa_server           Up (healthy)
# rasa_nginx            Up

# Xem log nếu có lỗi
docker-compose -f docker-compose.prod.yml logs --tail=50 rasa
docker-compose -f docker-compose.prod.yml logs --tail=50 action_server
```

### 3.4 Test API

```bash
# Test từ server (thay localhost bằng IP nếu test từ ngoài)
curl -X POST http://localhost/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test", "message": "xin chào"}'

# Kết quả mong đợi (JSON):
# [{"recipient_id":"test","text":"Xin chào! Tôi có thể giúp gì cho bạn?"}]
```

---

## Bước 4 — Cài đặt SSL/HTTPS (khuyến nghị)

Cần có domain trỏ về IP server trước.

### 4.1 Cài Certbot

```bash
apt install -y certbot

# Dừng Nginx tạm để lấy cert
docker-compose -f /opt/rasa-chatbot/docker-compose.prod.yml stop nginx

# Lấy SSL cert (thay YOUR_DOMAIN)
certbot certonly --standalone -d YOUR_DOMAIN -d www.YOUR_DOMAIN \
    --email your@email.com --agree-tos --non-interactive

# Cert được lưu tại:
# /etc/letsencrypt/live/YOUR_DOMAIN/fullchain.pem
# /etc/letsencrypt/live/YOUR_DOMAIN/privkey.pem
```

### 4.2 Copy cert vào thư mục Nginx

```bash
cp /etc/letsencrypt/live/YOUR_DOMAIN/fullchain.pem /opt/rasa-chatbot/nginx/ssl/
cp /etc/letsencrypt/live/YOUR_DOMAIN/privkey.pem /opt/rasa-chatbot/nginx/ssl/
chmod 600 /opt/rasa-chatbot/nginx/ssl/*.pem
```

### 4.3 Bật HTTPS trong Nginx config

Mở file `nginx/conf.d/rasa.conf` và bỏ comment các dòng SSL:

```nginx
# Đổi listen 80 thành:
listen 443 ssl http2;

# Bỏ comment các dòng ssl_certificate:
ssl_certificate     /etc/nginx/ssl/fullchain.pem;
ssl_certificate_key /etc/nginx/ssl/privkey.pem;
ssl_protocols       TLSv1.2 TLSv1.3;
ssl_ciphers         HIGH:!aNULL:!MD5;
ssl_session_cache   shared:SSL:10m;
ssl_session_timeout 10m;
```

Thêm block redirect HTTP → HTTPS (bỏ comment ở đầu file `rasa.conf`):

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN;
    return 301 https://$host$request_uri;
}
```

Khởi động lại Nginx:

```bash
cd /opt/rasa-chatbot
docker-compose -f docker-compose.prod.yml restart nginx
```

### 4.4 Tự động gia hạn cert

```bash
# Thêm cron job gia hạn mỗi 2 tháng
crontab -e

# Thêm dòng này vào cuối:
0 3 1 */2 * certbot renew --quiet && \
    cp /etc/letsencrypt/live/YOUR_DOMAIN/*.pem /opt/rasa-chatbot/nginx/ssl/ && \
    docker-compose -f /opt/rasa-chatbot/docker-compose.prod.yml restart nginx
```

---

## Bước 5 — Cài đặt CI/CD với GitHub Actions

### 5.1 Tạo Docker Hub Access Token

1. Đăng nhập [hub.docker.com](https://hub.docker.com)
2. Vào **Account Settings → Security → New Access Token**
3. Đặt tên: `rasa-cicd`, quyền: **Read, Write, Delete**
4. Copy token (chỉ hiện 1 lần)

### 5.2 Thêm Secrets vào GitHub repo

Vào **GitHub repo → Settings → Secrets and variables → Actions → New repository secret**

Thêm lần lượt 6 secrets sau:

| Secret name | Giá trị |
|---|---|
| `DOCKER_HUB_USERNAME` | Username Docker Hub của bạn |
| `DOCKER_HUB_TOKEN` | Token vừa tạo ở bước 5.1 |
| `PROD_SERVER_HOST` | IP hoặc domain server (vd: `1.2.3.4`) |
| `PROD_SERVER_USER` | User SSH (vd: `ubuntu` hoặc `root`) |
| `PROD_SERVER_SSH_KEY` | Nội dung file `~/.ssh/rasa_deploy` (private key) |
| `PROD_ENV_FILE` | Nội dung toàn bộ file `.env.production` |

Lấy nội dung private key:

```bash
cat ~/.ssh/rasa_deploy
# Copy từ -----BEGIN OPENSSH PRIVATE KEY----- đến -----END OPENSSH PRIVATE KEY-----
```

### 5.3 Kích hoạt CI/CD

```bash
# Khởi tạo git repo (nếu chưa có)
git init
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Push lên main để trigger pipeline
git add .
git commit -m "feat: add CI/CD and production Docker setup"
git push origin main
```

Theo dõi pipeline tại: **GitHub repo → Actions**

---

## Bước 6 — Tích hợp widget vào website khác

Sau khi deploy xong, các website khác tích hợp chatbot bằng cách thêm vào HTML:

### Cách 1 — Iframe (đơn giản nhất)

```html
<!-- Dán vào trước </body> của trang web -->
<iframe
  src="https://YOUR_DOMAIN/widget/widget.html"
  style="position:fixed;bottom:0;right:0;width:400px;height:620px;border:none;z-index:9999;"
  title="Chatbot hỗ trợ"
></iframe>
```

### Cách 2 — Nhúng trực tiếp (cùng domain hoặc CORS đã cấu hình)

```html
<!-- Thêm vào <head> -->
<script>
  window.RASA_URL = 'https://YOUR_DOMAIN/webhooks/rest/webhook';
</script>

<!-- Dán vào trước </body> -->
<script src="https://YOUR_DOMAIN/widget/widget.html"></script>
```

### Cách 3 — Gọi API trực tiếp (tích hợp vào UI riêng)

```javascript
// POST đến endpoint này từ bất kỳ frontend nào
const response = await fetch('https://YOUR_DOMAIN/webhooks/rest/webhook', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    sender: 'user-unique-id',   // ID phiên của user
    message: 'Tìm điện thoại Samsung'
  })
});

const replies = await response.json();
// replies = [{ "recipient_id": "...", "text": "Dạ, tôi tìm thấy..." }]
```

---

## Xử lý sự cố thường gặp

### Container không khởi động được

```bash
# Xem log chi tiết
docker-compose -f docker-compose.prod.yml logs action_server
docker-compose -f docker-compose.prod.yml logs rasa

# Restart service cụ thể
docker-compose -f docker-compose.prod.yml restart action_server
```

### Lỗi kết nối database

```bash
# Kiểm tra MySQL đang chạy
docker-compose -f docker-compose.prod.yml exec mysql mysqladmin ping -u root -p

# Kiểm tra biến môi trường
docker-compose -f docker-compose.prod.yml exec action_server env | grep DB_
```

### Rasa không load được model

```bash
# Kiểm tra models có trong thư mục không
ls -lh /opt/rasa-chatbot/models/

# Nếu thiếu, sync lại từ máy local:
rsync -avz ./models/ ubuntu@YOUR_SERVER_IP:/opt/rasa-chatbot/models/
```

### Nginx lỗi 502 Bad Gateway

```bash
# Rasa chưa sẵn sàng, chờ thêm (Rasa mất 60-90s để load model)
docker-compose -f docker-compose.prod.yml logs -f rasa

# Khi thấy dòng "Rasa server is up and running" thì mới test được
```

### Cập nhật code không cần restart Rasa

```bash
# Chỉ restart action_server (nhanh, không reload model)
docker-compose -f docker-compose.prod.yml restart action_server

# Restart toàn bộ (chậm hơn, reload model ~90s)
docker-compose -f docker-compose.prod.yml up -d --remove-orphans
```

---

## Checklist trước khi go-live

- [ ] Server đã cài Docker và Docker Compose
- [ ] Firewall mở port 80 và 443
- [ ] File `.env.production` đã điền đầy đủ, password mạnh
- [ ] Models đã được sync lên server (`ls models/*.tar.gz`)
- [ ] Tất cả containers đều `Up (healthy)`
- [ ] Test API trả về response đúng
- [ ] SSL cert đã cài (nếu có domain)
- [ ] CORS đã đổi từ `*` sang domain cụ thể
- [ ] Cron job gia hạn SSL đã cài
- [ ] CI/CD pipeline chạy thành công ít nhất 1 lần
