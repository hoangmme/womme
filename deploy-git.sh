#!/usr/bin/env bash
# Script hỗ trợ đẩy nhanh code thay đổi lên Git

if [ -z "$1" ]; then
  echo "❌ Lỗi: Bạn chưa nhập nội dung commit!"
  echo "👉 Cách dùng: ./deploy-git.sh \"nội dung commit thay đổi\""
  exit 1
fi

COMMIT_MSG="$*"

echo "🚀 [1/3] Thêm toàn bộ các file thay đổi vào staging (git add .)..."
git add .

echo "💬 [2/3] Tạo commit với thông điệp: \"$COMMIT_MSG\"..."
git commit -m "$COMMIT_MSG"

echo "⬆️ [3/3] Đẩy code lên Remote Repository (git push)..."
git push

if [ $? -eq 0 ]; then
  echo "✅ Đã đẩy code lên Git thành công!"
else
  echo "⚠️ Lưu ý: Nếu lệnh git push thất bại, hãy kiểm tra kết nối mạng hoặc quyền repository."
  exit 1
fi
