# WordOps MMe Plugin (womme)

Plugin mở rộng chuyên nghiệp dành cho [WordOps](https://wordops.net/), được tùy chỉnh và bổ sung thêm các tính năng đặc biệt. Hiện tại plugin hỗ trợ tính năng Clone Site và sẽ được mở rộng thêm trong tương lai.

## Tính năng

### 1. Nhân bản (Clone) Site
Lệnh `wo site clone` cho phép nhân bản toàn bộ dữ liệu, mã nguồn và database của một trang WordPress sang một tên miền mới ngay trên cùng server một cách an toàn.
- Tự động gọi WordOps khởi tạo site mới (Nginx, Database, User)
- Hỗ trợ tham số `--le` để tự cài Let's Encrypt SSL cho tên miền mới
- Tự động rsync mã nguồn và migrate Database, an toàn cho file config.

*(Các tính năng khác sẽ được update trong tương lai...)*

## Cài đặt siêu tốc (Chỉ 1 dòng lệnh)

Bạn chỉ cần đăng nhập vào server WordOps với quyền root và chạy lệnh sau:

```bash
curl -sL https://raw.githubusercontent.com/hoangmme/womme/main/install.sh | sudo bash
```

## Cách sử dụng

**Ví dụ:** Nhân bản site `old.com` sang `new.com` và tự cài đặt luôn SSL:
```bash
wo site clone old.com new.com --le
```
Cú pháp đầy đủ:
```bash
wo site clone <domain_gốc> <domain_mới> [--le] [--force]
```
