#!/usr/bin/env bash
# ============================================================
# deploy.sh - Script deploy thủ công lên server production
# ============================================================
# Dùng khi không có CI/CD hoặc muốn deploy nhanh từ máy local
#
# Cách dùng:
#   chmod +x deploy.sh
#   ./deploy.sh                    # deploy lên server mặc định
#   ./deploy.sh --host 1.2.3.4     # chỉ định IP server
#   ./deploy.sh --restart-rasa     # restart cả Rasa (reload model)
# ============================================================

set -euo pipefail

# ── Cấu hình mặc định (override bằng args hoặc env) ──────
PROD_HOST="${PROD_HOST:-YOUR_SERVER_IP}"
PROD_USER="${PROD_USER:-ubuntu}"
DEPLOY_DIR="${DEPLOY_DIR:-/opt/rasa-chatbot}"
SSH_KEY="${SSH_KEY:-~/.ssh/id_rsa}"
RESTART_RASA=false
SKIP_BUILD=false

# ── Parse arguments ───────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --host)       PROD_HOST="$2";  shift 2 ;;
        --user)       PROD_USER="$2";  shift 2 ;;
        --key)        SSH_KEY="$2";    shift 2 ;;
        --restart-rasa) RESTART_RASA=true; shift ;;
        --skip-build) SKIP_BUILD=true; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

SSH_CMD="ssh -i $SSH_KEY -o StrictHostKeyChecking=no $PROD_USER@$PROD_HOST"
RSYNC_CMD="rsync -avz --progress -e 'ssh -i $SSH_KEY -o StrictHostKeyChecking=no'"

echo "======================================================"
echo " Deploy Rasa Chatbot → $PROD_USER@$PROD_HOST"
echo "======================================================"

# ── Bước 1: Kiểm tra kết nối server ──────────────────────
echo "[1/6] Kiểm tra kết nối SSH..."
$SSH_CMD "echo 'SSH OK'" || { echo "Lỗi: Không kết nối được server!"; exit 1; }

# ── Bước 2: Tạo thư mục trên server ──────────────────────
echo "[2/6] Chuẩn bị thư mục trên server..."
$SSH_CMD "mkdir -p $DEPLOY_DIR/nginx/logs $DEPLOY_DIR/nginx/ssl $DEPLOY_DIR/models"

# ── Bước 3: Sync code lên server ─────────────────────────
echo "[3/6] Sync code lên server..."
rsync -avz --progress \
    -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no" \
    --exclude='.git' \
    --exclude='models/*.tar.gz' \
    --exclude='.env*' \
    --exclude='nginx/logs' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.rasa' \
    ./ "$PROD_USER@$PROD_HOST:$DEPLOY_DIR/"

# ── Bước 4: Sync models (chỉ khi cần) ────────────────────
echo "[4/6] Sync models..."
rsync -avz --progress \
    -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no" \
    --ignore-existing \
    ./models/ "$PROD_USER@$PROD_HOST:$DEPLOY_DIR/models/"

# ── Bước 5: Kiểm tra .env.production trên server ─────────
echo "[5/6] Kiểm tra .env.production..."
$SSH_CMD "test -f $DEPLOY_DIR/.env.production" || {
    echo ""
    echo "CẢNH BÁO: Chưa có file .env.production trên server!"
    echo "Chạy lệnh sau để tạo:"
    echo "  scp -i $SSH_KEY .env.production $PROD_USER@$PROD_HOST:$DEPLOY_DIR/.env.production"
    echo ""
    read -p "Tiếp tục không? (y/N): " confirm
    [[ "$confirm" == "y" || "$confirm" == "Y" ]] || exit 1
}

# ── Bước 6: Deploy với Docker Compose ────────────────────
echo "[6/6] Deploy Docker Compose..."
$SSH_CMD << ENDSSH
    set -e
    cd $DEPLOY_DIR

    # Cài Docker nếu chưa có
    if ! command -v docker &> /dev/null; then
        echo "Cài đặt Docker..."
        curl -fsSL https://get.docker.com | sh
        sudo usermod -aG docker \$USER
    fi

    # Cài docker-compose nếu chưa có
    if ! command -v docker-compose &> /dev/null; then
        echo "Cài đặt docker-compose..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)" \
            -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi

    echo "--- Docker version ---"
    docker --version
    docker-compose --version

    # Build action server image
    if [ "$SKIP_BUILD" = "false" ]; then
        echo "--- Build action server ---"
        docker-compose -f docker-compose.prod.yml --env-file .env.production build action_server
    fi

    # Start/update services
    echo "--- Start services ---"
    if [ "$RESTART_RASA" = "true" ]; then
        docker-compose -f docker-compose.prod.yml --env-file .env.production up -d --remove-orphans
    else
        # Chỉ restart action_server và nginx, giữ nguyên rasa (tránh reload model lâu)
        docker-compose -f docker-compose.prod.yml --env-file .env.production up -d \
            --remove-orphans \
            mysql duckling action_server nginx
    fi

    # Dọn dẹp
    docker image prune -f

    echo ""
    echo "======================================================"
    echo " Deploy hoàn tất!"
    echo " API:    http://$PROD_HOST/webhooks/rest/webhook"
    echo " Widget: http://$PROD_HOST/widget/widget.html"
    echo " Health: http://$PROD_HOST/health"
    echo "======================================================"
ENDSSH

# ── Health check ──────────────────────────────────────────
echo ""
echo "Chờ service khởi động..."
sleep 20

echo "Health check..."
for i in {1..5}; do
    if curl -sf "http://$PROD_HOST/health" > /dev/null 2>&1; then
        echo "Health check OK!"
        break
    fi
    echo "Thử lại ($i/5)..."
    sleep 10
done

echo ""
echo "======================================================"
echo " DONE! Chatbot đang chạy tại:"
echo " API:    http://$PROD_HOST/webhooks/rest/webhook"
echo " Widget: http://$PROD_HOST/widget/widget.html"
echo "======================================================"
