#!/bin/bash
# Trình cài đặt WordOps MMe Plugin
# Tự động tải từ Github Repo và cài đặt vào hệ thống

REPO_URL="https://raw.githubusercontent.com/hoangmme/womme/main/womme.py"

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

# Tạo thư mục nếu chưa có
mkdir -p "$PLUGIN_DIR"
mkdir -p "$CONF_DIR"

# Tải file Python Plugin trực tiếp từ Github Repo
echo "Đang tải source code plugin từ Github..."
curl -sL "$REPO_URL" -o "$PLUGIN_DIR/womme.py"

# Kiểm tra xem tải thành công không
if [ ! -f "$PLUGIN_DIR/womme.py" ] || ! grep -q "WOSiteCloneController" "$PLUGIN_DIR/womme.py"; then
    echo "Lỗi: Không thể tải source code từ Repo. Vui lòng kiểm tra lại nhánh main hoặc tính khả dụng của Repo."
    exit 1
fi

# Tạo file cấu hình kích hoạt
echo "Đang kích hoạt plugin womme trong hệ thống WordOps..."
cat <<EOF > "$CONF_DIR/womme.conf"
[womme]
enable = true
EOF

echo "=================================================="
echo " Cài đặt THÀNH CÔNG!"
echo " Bạn đã có thể sử dụng các lệnh mở rộng, ví dụ:"
echo " wo site clone <domain_cũ> <domain_mới> --le --force"
echo "=================================================="
