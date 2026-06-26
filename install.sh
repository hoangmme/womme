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

    local commands="deploy site role copy db update"
    local deploy_commands="push pull edit list rollback logs"
    local site_commands="pause start lockon lockoff clone rename wpmme thememme"
    
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
                    add|edit|run|rollback|logs)
                        COMPREPLY=( $(compgen -W "$domains" -- "$cur") )
                        ;;
                esac
                ;;
            site)
                case "$subcmd" in
                    pause|start|lockon|lockoff|clone|rename|wpmme|thememme)
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

echo -e "\e[96m==================================================\e[0m"
echo -e "\e[1;92m WordOps MMe CLI Tool - Trợ lý vận hành siêu tốc\e[0m"
echo -e "\e[96m==================================================\e[0m"
echo ""
echo -e " \e[93mCác lệnh có thể dùng:\e[0m"
echo -e " \e[96mmme deploy push <domain>\e[0m     (Thêm cấu hình Auto Deploy)"
echo -e " \e[96mmme deploy edit <domain>\e[0m     (Sửa cấu hình Auto Deploy)"
echo -e " \e[96mmme deploy list\e[0m              (Xem danh sách Auto Deploy)"
echo -e " \e[96mmme deploy pull <domain>\e[0m     (Chạy Deploy thủ công)"
echo -e " \e[96mmme deploy rollback <domain>\e[0m (Khôi phục bản cũ)"
echo -e " \e[96mmme deploy logs <domain>\e[0m     (Xem nhật ký Deploy)"
echo -e " \e[96mmme site pause <domain>\e[0m      (Bật chế độ bảo trì)"
echo -e " \e[96mmme site start <domain>\e[0m      (Tắt chế độ bảo trì)"
echo -e " \e[96mmme site lockon <domain>\e[0m     (Bật khóa bảo mật site)"
echo -e " \e[96mmme site lockoff <domain>\e[0m    (Tắt khóa bảo mật site)"
echo -e " \e[96mmme role\e[0m                     (Fix quyền 644/755/www-data)"
echo -e " \e[96mmme copy <nguồn> <đích>\e[0m      (Sao chép thư mục sang VPS khác)"
echo -e " \e[96mmme site clone <old> <new>\e[0m   (Nhân bản website)"
echo -e " \e[96mmme site rename <old> <new>\e[0m  (Đổi tên miền website)"
echo -e " \e[96mmme db\e[0m                       (Sửa cấu hình MySQL/MariaDB)"
echo -e " \e[96mmme site wpmme <domain>\e[0m      (Cài & kích hoạt plugin WPMMe)"
echo -e " \e[96mmme site thememme <domain>\e[0m   (Cài & kích hoạt theme WPMMe)"
echo -e " \e[96mmme update\e[0m                   (Cập nhật MMe CLI lên bản mới nhất)"
echo ""
echo -e " \e[90mGõ \`mme <lệnh> --help\` để xem chi tiết cách dùng của một nhóm lệnh.\e[0m"
echo -e "\e[96m==================================================\e[0m"
echo -e "\e[1;33m MẸO NHỎ QUAN TRỌNG:\e[0m"
echo -e "\e[33m Hãy gõ lệnh \e[1;37mexec bash\e[0m\e[33m và nhấn Enter để có thể gõ mme và dùng phím Tab ngay bây giờ!\e[0m"
echo ""
echo "=================================================="
