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

echo "Đang thiết lập tính năng Auto-complete (Bấm Tab gợi ý lệnh)..."
mkdir -p /etc/bash_completion.d
cat <<'EOF' > /etc/bash_completion.d/mme
_mme_completion() {
    local cur prev words cword
    _init_completion 2>/dev/null || {
        COMPREPLY=()
        local w c
        cword=$COMP_CWORD
        words=("${COMP_WORDS[@]}")
        cur="${words[cword]}"
        prev="${words[cword-1]}"
    }

    local commands="deploy site role db"
    local deploy_commands="add list run rollback logs"
    local site_commands="pause start lockon lockoff clone"
    
    # Lấy danh sách tên miền từ /var/www (bỏ qua các thư mục hệ thống của WordOps)
    local domains=$(ls /var/www 2>/dev/null | grep -vE '^(html|22222|default)$')

    if [[ $cword -eq 1 ]]; then
        COMPREPLY=( $(compgen -W "$commands" -- "$cur") )
        return 0
    fi
    
    local cmd=${words[1]}
    
    if [[ $cword -eq 2 ]]; then
        case "$cmd" in
            deploy)
                COMPREPLY=( $(compgen -W "$deploy_commands" -- "$cur") )
                ;;
            site)
                COMPREPLY=( $(compgen -W "$site_commands" -- "$cur") )
                ;;
        esac
        return 0
    fi
    
    local subcmd=${words[2]}
    
    if [[ $cword -eq 3 ]]; then
        case "$cmd" in
            deploy)
                case "$subcmd" in
                    add|run|rollback|logs)
                        COMPREPLY=( $(compgen -W "$domains" -- "$cur") )
                        ;;
                esac
                ;;
            site)
                case "$subcmd" in
                    pause|start|lockon|lockoff|clone)
                        COMPREPLY=( $(compgen -W "$domains" -- "$cur") )
                        ;;
                esac
                ;;
        esac
        return 0
    fi
    
    if [[ $cword -eq 4 && "$cmd" == "site" && "$subcmd" == "clone" ]]; then
        COMPREPLY=( $(compgen -W "$domains" -- "$cur") )
        return 0
    fi
}
complete -F _mme_completion mme
EOF

# Nạp lại ngay lập tức cho session hiện tại nếu người dùng chạy thủ công,
# nhưng nếu chạy qua curl | bash thì cần lưu ý.
source /etc/bash_completion.d/mme 2>/dev/null || true

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
