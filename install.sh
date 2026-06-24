#!/bin/bash
# Trình cài đặt WordOps MMe Plugin
# Tự động tải từ Github Repo và cài đặt vào hệ thống

REPO_RAW_URL="https://raw.githubusercontent.com/hoangmme/womme/main"

echo "=================================================="
echo " Đang cài đặt MMe Plugin cho WordOps..."
echo "=================================================="

# Kiểm tra quyền root
if [ "$EUID" -ne 0 ]; then
  echo "Lỗi: Vui lòng chạy lệnh bằng quyền root (sudo)"
  exit 1
fi

PLUGIN_DIR="/var/lib/wo/plugins"
CONF_DIR="/etc/wo/plugins.d"

mkdir -p "$PLUGIN_DIR"
mkdir -p "$CONF_DIR"

echo "Đang tải source code plugin từ Github (bypass cache)..."
CACHE_BUSTER=$(date +%s)
curl -sL "$REPO_RAW_URL/womme.py?t=$CACHE_BUSTER" -o "$PLUGIN_DIR/womme.py"
curl -sL "$REPO_RAW_URL/womme-daemon.py?t=$CACHE_BUSTER" -o "$PLUGIN_DIR/womme-daemon.py"

chmod +x "$PLUGIN_DIR/womme-daemon.py"

if [ ! -f "$PLUGIN_DIR/womme.py" ] || [ ! -f "$PLUGIN_DIR/womme-daemon.py" ]; then
    echo "Lỗi: Không thể tải source code từ Repo."
    exit 1
fi

echo "Đang kích hoạt plugin womme trong hệ thống WordOps..."
cat <<EOF > "$CONF_DIR/womme.conf"
[womme]
enable = true
EOF

echo "Đang thiết lập Systemd Daemon cho Webhook Listener..."
cat <<EOF > /etc/systemd/system/womme-daemon.service
[Unit]
Description=WordOps MMe Auto Deploy Webhook Daemon
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 $PLUGIN_DIR/womme-daemon.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable womme-daemon.service
systemctl restart womme-daemon.service

echo "=================================================="
echo " Cài đặt THÀNH CÔNG!"
echo " "
echo " Các lệnh có thể dùng:"
echo " wo mme deploy add <domain>   (Thêm cấu hình Auto Deploy)"
echo " wo mme deploy list           (Xem danh sách Auto Deploy)"
echo " wo mme deploy run <domain>   (Chạy Deploy thủ công)"
echo " wo mme deploy rollback <domain> (Khôi phục bản cũ)"
echo " wo mme deploy logs <domain>  (Xem nhật ký Deploy)"
echo " wo site pause <domain>       (Bật chế độ bảo trì)"
echo " wo site start <domain>       (Tắt chế độ bảo trì)"
echo " wo mme role                  (Fix quyền 644/755/www-data)"
echo " wo site clone <old> <new>    (Nhân bản website)"
echo " "
echo " BƯỚC TIẾP THEO (Thiết lập Nginx Proxy cho Webhook):"
echo " Để cấu hình một URL nhận Webhook bảo mật HTTPS, hãy tạo một trang proxy bằng lệnh WordOps:"
echo " wo site create deploy.tenmiencuaban.com --proxy=127.0.0.1:8989 --le"
echo " (Sau đó dùng link https://deploy.tenmiencuaban.com/hooks/domain.com để gắn vào Github)"
echo "=================================================="
