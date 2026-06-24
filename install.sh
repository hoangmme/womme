#!/bin/bash
# Trình cài đặt MMe CLI Tool
# Tự động tải từ Github Repo và cài đặt vào hệ thống

REPO_RAW_URL="https://raw.githubusercontent.com/hoangmme/womme/main"

echo "=================================================="
echo " Đang cài đặt MMe CLI Tool..."
echo "=================================================="

# Kiểm tra quyền root
if [ "$EUID" -ne 0 ]; then
  echo "Lỗi: Vui lòng chạy lệnh bằng quyền root (sudo)"
  exit 1
fi

DAEMON_DIR="/usr/local/bin"

echo "Đang tải source code tool từ Github..."
CACHE_BUSTER=$(date +%s)
curl -sL "$REPO_RAW_URL/mme.py?t=$CACHE_BUSTER" -o "/usr/local/bin/mme"
curl -sL "$REPO_RAW_URL/womme-daemon.py?t=$CACHE_BUSTER" -o "$DAEMON_DIR/womme-daemon.py"

chmod +x "/usr/local/bin/mme"
chmod +x "$DAEMON_DIR/womme-daemon.py"

# Xóa các file cũ của plugin WordOps nếu có
if [ -f "/etc/wo/plugins.d/womme.conf" ]; then
    rm -f "/etc/wo/plugins.d/womme.conf"
fi
if [ -f "/var/lib/wo/plugins/womme.py" ]; then
    rm -f "/var/lib/wo/plugins/womme.py"
fi

echo "Đang thiết lập Systemd Daemon cho Webhook Listener..."
cat <<EOF > /etc/systemd/system/womme-daemon.service
[Unit]
Description=MMe Auto Deploy Webhook Daemon
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 $DAEMON_DIR/womme-daemon.py
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
echo " Bây giờ MMe đã trở thành một công cụ dòng lệnh độc lập, không còn phụ thuộc vào wo plugin."
echo " Bạn có thể gõ chữ mme ở bất cứ đâu để gọi."
echo " "
echo " Các lệnh có thể dùng:"
echo " mme deploy add <domain>   (Thêm cấu hình Auto Deploy)"
echo " mme deploy list           (Xem danh sách Auto Deploy)"
echo " mme deploy run <domain>   (Chạy Deploy thủ công)"
echo " mme deploy rollback <domain> (Khôi phục bản cũ)"
echo " mme deploy logs <domain>  (Xem nhật ký Deploy)"
echo " mme site pause <domain>   (Bật chế độ bảo trì)"
echo " mme site start <domain>   (Tắt chế độ bảo trì)"
echo " mme site lockon <domain>  (Bật khóa bảo mật site)"
echo " mme site lockoff <domain> (Tắt khóa bảo mật site)"
echo " mme role                  (Fix quyền 644/755/www-data)"
echo " mme site clone <old> <new> (Nhân bản website)"
echo " mme db                    (Sửa cấu hình MySQL/MariaDB)"
echo " "
echo " BƯỚC TIẾP THEO (Thiết lập Nginx Proxy cho Webhook):"
echo " Để cấu hình một URL nhận Webhook bảo mật HTTPS, hãy tạo một trang proxy bằng lệnh WordOps:"
echo " wo site create deploy.tenmiencuaban.com --proxy=127.0.0.1:8989 --le"
echo " (Sau đó dùng link https://deploy.tenmiencuaban.com/hooks/domain.com để gắn vào Github)"
echo "=================================================="
