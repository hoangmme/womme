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

## 💡 Thiết lập Github Webhook

Thay vì phải tạo riêng một Subdomain Proxy phức tạp, bạn chỉ cần cài plugin WPMMe của chúng tôi lên website, nó sẽ đóng vai trò như một điểm cầu nối (Bridge) an toàn:

1. Cài đặt plugin WPMMe vào trang web:
```bash
mme site wpmme domain.com
```

2. Vào Github > Settings > Webhooks > Add webhook, nhập:
- **Payload URL**: `https://domain.com/wp-json/wpmme/v1/deploy`
- **Content type**: `application/json`

*(Plugin sẽ nhận tín hiệu mã hóa từ Github và âm thầm kích hoạt tiến trình Deploy của Server mà không gây nặng web).*

---

## 🛠 Cách sử dụng CLI

### 1. Thêm cấu hình Auto Deploy (`add`)
Cấu hình một domain để tự động nhận code mỗi khi push lên Git. Có thể chọn đường dẫn là toàn bộ site (`/`) hoặc chỉ 1 thư mục theme/plugin.

```bash
Cấu hình một domain để tự động nhận code mỗi khi push lên Git.
```bash
mme deploy push domain.com
```
Lệnh này sẽ hỏi bạn URL của Git Repository, nhánh (branch), và đường dẫn cần triển khai.

### 2. Kích hoạt triển khai (Deploy) thủ công
Bạn có thể tự tay tải code mới nhất về server mà không cần đợi webhook bằng lệnh:
```bash
mme deploy pull domain.com
```

### 3. Sửa cấu hình Deploy (`edit`)
Nếu bạn nhập sai hoặc muốn đổi repo/branch, sử dụng lệnh:
```bash
mme deploy edit mme.vn
```

### 4. Xem danh sách (`list`)
```bash
mme deploy list
```

### 5. Xem nhật ký Deploy (`logs`)
```bash
mme deploy logs mme.vn
```

### 6. Rollback khẩn cấp (`rollback`)
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

### 4. Cài đặt plugin WPMMe (`site wpmme`)
```bash
mme site wpmme mme.vn
```
Lệnh này sẽ tự động tải file zip mới nhất từ Github WPMMe và cài đè vào site, đồng thời tự sửa lỗi phân quyền `mme role`.

### 5. Cài nhanh Theme WPMMe (`thememme`)
```bash
mme site thememme mme.vn
```
Tương tự như plugin, lệnh này sẽ cài tự động Theme từ Github (hoangmme/thememme) vào site và phân quyền.

### 6. Đổi tên miền không tốn dung lượng (`rename`)
Chuyển website từ domain cũ sang domain mới với công nghệ "Instant Move" (0 bytes dung lượng data, không cần copy file hay export DB):
```bash
mme site rename old.com new.com
```

### 7. Copy file sang máy chủ (VPS) khác cực nhanh (`copy`)
Lệnh này giúp bạn chuyển một thư mục bất kỳ từ VPS hiện tại sang VPS mới thông qua đường truyền nội bộ SSH (rsync) một cách bảo mật tuyệt đối (Tự động thiết lập SSH Key):
```bash
mme copy /var/www/domain.com/htdocs /var/www/newdomain.com/htdocs
```
Hệ thống sẽ hướng dẫn bạn từng bước cách cấp quyền ở VPS mới và tự động chạy tiến trình copy siêu mượt mà.

### 8. Đổi port SSH an toàn (`port`)
Đổi port SSH từ 22 sang một port khác (vd: 2222) cực kỳ an toàn vì tool sẽ tự động cấu hình lại firewall UFW và SSH Service:
```bash
mme port 2222
```

### 9. Di chuyển website sang máy chủ khác (`migrate`)
Lệnh này là một "CI/CD thu nhỏ" giúp bạn di chuyển toàn bộ website từ VPS cũ sang VPS mới cực kỳ an toàn (sử dụng gzip stream database để tiết kiệm dung lượng, tự động fix table_prefix):
```bash
mme site migrate old-domain.com new-domain.com
```
Làm theo các bước hiện ra trên màn hình để chuyển dữ liệu mà không lo bị ngắt kết nối hay lỗi phân quyền.

### 10. Cập nhật MMe CLI Tool (`update`)
Cập nhật công cụ `mme` trên server của bạn lên phiên bản mới nhất từ Github:
```bash
mme update
```
