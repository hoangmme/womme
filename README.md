# WordOps MMe Plugin (womme)

Plugin mở rộng chuyên nghiệp dành cho [WordOps](https://wordops.net/), hỗ trợ tự động hóa hệ thống CI/CD (Git Auto Deploy) theo chuẩn Zero-Downtime, cùng với các tính năng hữu ích khác.

## Bảng tính năng chính

- **Zero-Downtime Deploy**: Kiến trúc Symlink chuyên nghiệp (`releases`, `shared`, `current`).
- **Webhook Daemon**: Chạy ngầm bằng Python Systemd, bảo mật bằng GitHub/GitLab Signature.
- **Rollback siêu tốc**: Khôi phục lại bản release trước đó chỉ trong 1 giây.
- **Auto Release Retention**: Tự động dọn dẹp, chỉ giữ lại 5 bản release gần nhất.
- **Auto SSH Deploy Key**: Tự sinh Public Key dán thẳng vào Github.
- **Build Command**: Tự động chạy lệnh (npm, composer) sau khi kéo code.
- **Smart Permission**: Tự nhận diện đúng User sở hữu WordOps Site để chown.
- **Manual Deploy**: Hỗ trợ chạy lệnh thủ công nếu không muốn xài Webhook.
- **Nginx Proxy**: Tạo Webhook endpoint HTTPS xịn xò qua proxy nội bộ.

---

## 🚀 Cài đặt (Chỉ 1 dòng lệnh)

Yêu cầu chạy dưới quyền **root** trên máy chủ đã cài đặt WordOps:

```bash
curl -sL https://raw.githubusercontent.com/hoangmme/womme/main/install.sh | sudo bash
```
*(Script sẽ tự kéo source code, cài plugin, dựng Systemd Daemon và báo hoàn tất)*

## 💡 Thiết lập Nginx Webhook Proxy

Để nhận Webhook từ Github an toàn qua HTTPS, WordOps hỗ trợ tạo reverse proxy trỏ thẳng vào port 8989 của Daemon:

```bash
wo site create deploy.tenmiencuaban.com --proxy=127.0.0.1:8989 --le
```
Khi khai báo trên Github, bạn sử dụng Payload URL dạng: `https://deploy.tenmiencuaban.com/hooks/domain.com`

---

## 🛠 Cách sử dụng CLI

### 1. Thêm cấu hình Auto Deploy (`add`)
Cấu hình một domain để tự động nhận code mỗi khi push lên Git. Có thể chọn đường dẫn là toàn bộ site (`/`) hoặc chỉ 1 thư mục theme/plugin.

```bash
mme deploy add mme.vn \
  --repo=git@github.com:hoangmme/mme-theme.git \
  --branch=main \
  --path=wp-content/themes/mme \
  --build="npm ci && npm run build"
```
*Lưu ý: Lệnh này sẽ tự động sinh và in ra SSH Public Key để bạn dán vào Github Deploy Keys.*

### 2. Chạy Deploy thủ công (`run`)
Bấm nút kéo code, build và deploy thủ công không cần đợi Webhook (thường dùng để test lần đầu):
```bash
mme deploy run mme.vn
```

### 3. Xem danh sách (`list`)
```bash
mme deploy list
```

### 4. Xem nhật ký Deploy (`logs`)
```bash
mme deploy logs mme.vn
```

### 5. Rollback khẩn cấp (`rollback`)
Trong trường hợp bản code mới bị lỗi sập site, gõ lệnh này để trỏ symlink lùi về bản release liền kề trước đó:
```bash
mme deploy rollback mme.vn
```

---

## 🛠 Tính năng bổ trợ

### 1. Fix quyền file/folder cấp tốc (`role`)
Phân quyền tự động 644 cho file, 755 cho thư mục và đổi chủ sở hữu toàn bộ thành `www-data:www-data` cho thư mục hiện tại (bao gồm cả thư mục con). Rất tiện khi bạn lỡ tay up file qua root SFTP.
```bash
cd /var/www/domain.com/htdocs
mme role
```

### 2. Bật/Tắt chế độ bảo trì (`pause` / `start`)
Chỉ với một dòng lệnh, toàn bộ traffic truy cập vào website sẽ ngay lập tức được chuyển hướng sang giao diện bảo trì cực kỳ chuyên nghiệp (kèm mã HTTP 503 chuẩn SEO) mà không làm ảnh hưởng đến mã nguồn gốc.
```bash
mme site pause domain.com
```
Khi nâng cấp hoặc sửa lỗi xong, để mở lại website bình thường:
```bash
mme site start domain.com
```

### 3. Nhân bản Site (`clone`)
Lệnh này cho phép nhân bản nguyên vẹn một site sang domain mới ngay trên cùng server:
```bash
mme site clone old-domain.com new-domain.com --le --force
```
