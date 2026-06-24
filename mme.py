#!/usr/bin/env python3
import os
import json
import subprocess
import argparse
import sys
import pwd

DEPLOY_CONFIG_FILE = "/etc/wo/mme-deploy.json"

MAINTENANCE_HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Website Đang Bảo Trì</title>
    <!-- Thư viện Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Google Fonts: Inter -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <!-- FontAwesome cho các biểu tượng -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        body {
            font-family: 'Inter', sans-serif;
        }
        
        /* Hiệu ứng trôi nổi cho các khối màu nền */
        @keyframes float {
            0% { transform: translateY(0px) scale(1); }
            33% { transform: translateY(-30px) scale(1.1); }
            66% { transform: translateY(15px) scale(0.9); }
            100% { transform: translateY(0px) scale(1); }
        }
        
        .blob {
            animation: float 8s ease-in-out infinite;
        }
        
        .blob-delayed {
            animation: float 10s ease-in-out infinite;
            animation-delay: 2s;
        }

        /* Hiệu ứng xoay cho icon bánh răng */
        @keyframes spin-slow {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        .animate-spin-slow {
            animation: spin-slow 8s linear infinite;
        }

        @keyframes progress-stripes {
            from { background-position: 1rem 0; }
            to { background-position: 0 0; }
        }
        .animate-progress {
            background-image: linear-gradient(45deg, rgba(255, 255, 255, 0.15) 25%, transparent 25%, transparent 50%, rgba(255, 255, 255, 0.15) 50%, rgba(255, 255, 255, 0.15) 75%, transparent 75%, transparent);
            background-size: 1rem 1rem;
            animation: progress-stripes 1s linear infinite;
        }
    </style>
</head>

<body class="bg-gray-50 min-h-screen flex items-center justify-center p-4 relative overflow-hidden selection:bg-indigo-500 selection:text-white">

    <!-- Background Decoration (Các đốm màu mờ phía sau) -->
    <div class="absolute top-[-10%] left-[-10%] w-96 h-96 bg-indigo-300 rounded-full mix-blend-multiply filter blur-3xl opacity-50 blob"></div>
    <div class="absolute top-[20%] right-[-10%] w-96 h-96 bg-purple-300 rounded-full mix-blend-multiply filter blur-3xl opacity-50 blob-delayed"></div>
    <div class="absolute bottom-[-10%] left-[20%] w-96 h-96 bg-pink-300 rounded-full mix-blend-multiply filter blur-3xl opacity-50 blob"></div>

    <div class="relative z-10 w-full max-w-3xl bg-white/70 backdrop-blur-xl border border-white/40 shadow-2xl rounded-3xl p-8 md:p-12 text-center">
        
        <!-- Logo -->
        <div class="mb-8">
            <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-indigo-600 text-white shadow-lg mb-4">
                <i class="fa-solid fa-layer-group text-2xl"></i>
            </div>
        </div>

        <!-- Biểu tượng Bảo trì -->
        <div class="relative flex justify-center items-center mb-6 text-indigo-500">
            <i class="fa-solid fa-gear text-5xl animate-spin-slow absolute opacity-20"></i>
            <i class="fa-solid fa-wrench text-3xl z-10 drop-shadow-md"></i>
        </div>

        <!-- Tiêu đề chính -->
        <h1 class="text-3xl md:text-5xl font-bold text-gray-800 mb-4 tracking-tight">
            Chúng tôi đang nâng cấp!
        </h1>
        
        <!-- Mô tả -->
        <p class="text-base md:text-lg text-gray-600 mb-8 max-w-xl mx-auto leading-relaxed">
            Hệ thống đang được bảo trì để cập nhật các tính năng mới và cải thiện trải nghiệm của bạn. Chúng tôi sẽ quay lại trong thời gian sớm nhất. Xin lỗi vì sự bất tiện này!
        </p>

        <!-- Hiệu ứng trạng thái & Thanh tiến trình giả lập -->
        <div class="mt-6 pt-8 border-t border-gray-200/50 w-full max-w-md mx-auto">
            <div class="flex items-center justify-center space-x-2 mb-4">
                <span class="relative flex h-3 w-3">
                  <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                  <span class="relative inline-flex rounded-full h-3 w-3 bg-amber-500"></span>
                </span>
                <span class="text-sm font-semibold text-amber-600 uppercase tracking-widest">Đang xử lý nâng cấp...</span>
            </div>
            
            <!-- Thanh Loading sọc chạy -->
            <div class="h-2 w-full bg-gray-200/80 rounded-full overflow-hidden shadow-inner">
                <div class="h-full bg-indigo-500 rounded-full animate-progress" style="width: 100%;"></div>
            </div>
        </div>

    </div>

</body>
</html>"""

def log_info(msg):
    print(f"[INFO] {msg}")

def log_error(msg):
    print(f"[ERROR] {msg}", file=sys.stderr)

def load_config():
    if not os.path.exists(DEPLOY_CONFIG_FILE):
        return {}
    try:
        with open(DEPLOY_CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_config(config):
    os.makedirs(os.path.dirname(DEPLOY_CONFIG_FILE), exist_ok=True)
    with open(DEPLOY_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def ensure_ssh_key():
    key_path = "/root/.ssh/id_ed25519"
    pub_key_path = f"{key_path}.pub"
    if not os.path.exists(key_path):
        log_info("Chưa có SSH Key. Đang tạo tự động SSH Deploy Key mới (Ed25519)...")
        subprocess.run(f'ssh-keygen -t ed25519 -f {key_path} -N "" -q', shell=True)
    
    if os.path.exists(pub_key_path):
        with open(pub_key_path, 'r') as f:
            pub_key = f.read().strip()
            log_info("================================================================")
            log_info("Public Key của Server (Hãy copy và thêm vào GitHub Deploy Keys):")
            log_info(pub_key)
            log_info("================================================================")

# ==================== COMMAND HANDLERS ====================

def cmd_role(args):
    cwd = os.getcwd()
    log_info(f"Đang cấp lại quyền cho toàn bộ file và thư mục tại: {cwd}")
    
    log_info("Đang đổi chủ sở hữu (chown -R www-data:www-data)...")
    subprocess.run(["chown", "-R", "www-data:www-data", cwd])
    
    log_info("Đang phân quyền thư mục (chmod 755)...")
    subprocess.run(["find", cwd, "-type", "d", "-exec", "chmod", "755", "{}", "+"])
    
    log_info("Đang phân quyền file (chmod 644)...")
    subprocess.run(["find", cwd, "-type", "f", "-exec", "chmod", "644", "{}", "+"])
    
    log_info("Hoàn tất cấp quyền!")

def cmd_deploy_add(args):
    config = load_config()
    config[args.domain] = {
        "repo": args.repo,
        "branch": args.branch,
        "path": args.path,
        "build": args.build
    }
    save_config(config)

    log_info(f"Đã lưu cấu hình Deploy cho domain: {args.domain}")
    ensure_ssh_key()
    log_info("Vui lòng lên GitHub/GitLab thêm Public Key ở trên vào phần Deploy Keys của kho mã nguồn (Nhớ cấp quyền read-only).")
    log_info(f"Để chạy thử deploy lần đầu thủ công, hãy gõ lệnh: mme deploy run {args.domain}")

def cmd_deploy_list(args):
    config = load_config()
    if not config:
        log_info("Chưa có cấu hình deploy nào.")
        return
    log_info("Danh sách cấu hình Git Auto Deploy:")
    for domain, conf in config.items():
        print(f"- Domain: {domain}")
        print(f"  Repo:   {conf.get('repo')}")
        print(f"  Branch: {conf.get('branch')}")
        print(f"  Path:   {conf.get('path')}")
        print(f"  Build:  {conf.get('build')}")
        print("")

def run_daemon(action, domain):
    daemon_path = "/usr/local/bin/womme-daemon.py"
    if not os.path.exists(daemon_path):
        daemon_path = "/var/lib/wo/plugins/womme-daemon.py"
        if not os.path.exists(daemon_path):
            daemon_path = os.path.join(os.path.dirname(__file__), "womme-daemon.py")
    
    if os.path.exists(daemon_path):
        subprocess.run([sys.executable, daemon_path, action, domain])
    else:
        log_error(f"Không tìm thấy womme-daemon.py tại {daemon_path}")

def cmd_deploy_run(args):
    log_info(f"Đang kích hoạt deploy thủ công cho {args.domain}...")
    run_daemon("--run", args.domain)

def cmd_deploy_rollback(args):
    log_info(f"Đang kích hoạt Rollback cho {args.domain}...")
    run_daemon("--rollback", args.domain)

def cmd_deploy_logs(args):
    log_file = f"/var/log/womme/{args.domain}.log"
    if os.path.exists(log_file):
        subprocess.run(["tail", "-n", "50", log_file])
    else:
        log_info(f"Chưa có nhật ký deploy nào cho {args.domain}.")

def cmd_site_pause(args):
    domain = args.domain
    site_dir = f"/var/www/{domain}"
    if not os.path.exists(site_dir):
        log_error(f"Site {domain} không tồn tại trong /var/www/")
        return

    log_info(f"Đang bật chế độ bảo trì cho {domain}...")

    html_path = f"{site_dir}/htdocs/mme-maintenance.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(MAINTENANCE_HTML)

    nginx_conf_dir = f"{site_dir}/conf/nginx"
    os.makedirs(nginx_conf_dir, exist_ok=True)
    conf_path = f"{nginx_conf_dir}/mme-maintenance.conf"
    
    nginx_rules = """set $maintenance 0;
if (-f $document_root/mme-maintenance.html) {
    set $maintenance 1;
}
if ($request_uri ~* "^/(wp-admin|wp-login\\.php|zogin)") {
    set $maintenance 0;
}
if ($maintenance = 1) {
    return 503;
}
error_page 503 @mme_maintenance;
location @mme_maintenance {
    rewrite ^(.*)$ /mme-maintenance.html break;
}"""
    with open(conf_path, 'w', encoding='utf-8') as f:
        f.write(nginx_rules)

    check = subprocess.run(["nginx", "-t"], capture_output=True, text=True)
    if check.returncode == 0:
        subprocess.run(["wo", "stack", "reload", "--nginx"], check=False)
        log_info(f"Đã BẬT bảo trì thành công cho {domain}. Trạng thái HTTP 503 sẽ được trả về.")
    else:
        log_error(f"Lỗi cấu hình Nginx. Đang tự động rollback...\n{check.stderr}")
        if os.path.exists(conf_path):
            os.remove(conf_path)

def cmd_site_start(args):
    domain = args.domain
    site_dir = f"/var/www/{domain}"
    if not os.path.exists(site_dir):
        log_error(f"Site {domain} không tồn tại.")
        return

    log_info(f"Đang tắt chế độ bảo trì cho {domain}...")

    html_path = f"{site_dir}/htdocs/mme-maintenance.html"
    conf_path = f"{site_dir}/conf/nginx/mme-maintenance.conf"

    if os.path.exists(html_path):
        os.remove(html_path)
    
    if os.path.exists(conf_path):
        os.remove(conf_path)

    subprocess.run(["wo", "stack", "reload", "--nginx"], check=False)
    log_info(f"Đã TẮT bảo trì thành công cho {domain}. Website hoạt động bình thường.")

def cmd_site_clone(args):
    source = args.old_domain
    dest = args.new_domain
    le = args.le
    force = args.force

    log_info(f"Bắt đầu quá trình clone từ {source} sang {dest}...")

    if not os.path.exists(f"/var/www/{source}/htdocs"):
        log_error(f"Site gốc {source} không tồn tại trong /var/www/")
        return

    create_cmd = ["wo", "site", "create", dest, "--wp"]
    if le:
        create_cmd.append("--le")
    if force:
        create_cmd.append("--force")

    log_info(f"Đang tạo site mới {dest} bằng WordOps...")
    result = subprocess.run(create_cmd)
    
    if result.returncode != 0 or not os.path.exists(f"/var/www/{dest}/htdocs"):
        log_error(f"Quá trình tạo site mới {dest} thất bại.")
        return

    log_info("Đang sao chép tệp tin từ site gốc sang site mới...")
    
    has_config = os.path.exists(f"/var/www/{dest}/htdocs/wp-config.php")
    if has_config:
        subprocess.run(f"cp /var/www/{dest}/htdocs/wp-config.php /tmp/wp-config-{dest}.php", shell=True)
    has_root_config = os.path.exists(f"/var/www/{dest}/wp-config.php")
    if has_root_config:
        subprocess.run(f"cp /var/www/{dest}/wp-config.php /tmp/wp-config-root-{dest}.php", shell=True)
        
    subprocess.run(f"rm -rf /var/www/{dest}/htdocs/*", shell=True)
    subprocess.run(f"rsync -a --exclude='wp-config.php' /var/www/{source}/htdocs/ /var/www/{dest}/htdocs/", shell=True)
    
    if has_config:
        subprocess.run(f"mv /tmp/wp-config-{dest}.php /var/www/{dest}/htdocs/wp-config.php", shell=True)
    if has_root_config:
        subprocess.run(f"mv /tmp/wp-config-root-{dest}.php /var/www/{dest}/wp-config.php", shell=True)

    log_info("Đang chuyển đổi cơ sở dữ liệu (Database)...")
    subprocess.run(f"wp db export /tmp/{source}.sql --path=/var/www/{source}/htdocs --allow-root", shell=True)
    subprocess.run(f"wp db import /tmp/{source}.sql --path=/var/www/{dest}/htdocs --allow-root", shell=True)
    if os.path.exists(f"/tmp/{source}.sql"):
        os.remove(f"/tmp/{source}.sql")

    log_info("Đang cập nhật URL tên miền trong Database...")
    subprocess.run(f"wp search-replace '//{source}' '//{dest}' --all-tables --path=/var/www/{dest}/htdocs --allow-root", shell=True)
    subprocess.run(f"wp search-replace '{source}' '{dest}' --all-tables --path=/var/www/{dest}/htdocs --allow-root", shell=True)

    log_info("Đang phân quyền thư mục và dọn dẹp cache...")
    subprocess.run(f"chown -R www-data:www-data /var/www/{dest}/htdocs", shell=True)
    subprocess.run("wo clean --all", shell=True)

    log_info(f"Thành công! Site {source} đã được nhân bản hoàn chỉnh sang {dest}.")

def cmd_site_lockon(args):
    domain = args.domain
    site_dir = f"/var/www/{domain}"
    htdocs = f"{site_dir}/htdocs"
    
    if not os.path.exists(htdocs):
        log_error(f"Site {domain} không tồn tại.")
        return

    log_info(f"Đang BẬT khóa bảo mật (Lock ON) cho {domain}...")

    # 1. Tắt sửa theme/plugin & Cài đặt theme/plugin
    log_info("Đang cập nhật wp-config.php (DISALLOW_FILE_EDIT, DISALLOW_FILE_MODS)...")
    subprocess.run(f"wp config set DISALLOW_FILE_EDIT true --raw --path={htdocs} --allow-root", shell=True)
    subprocess.run(f"wp config set DISALLOW_FILE_MODS true --raw --path={htdocs} --allow-root", shell=True)

    # 2. Chặn PHP execution trong uploads và cache
    log_info("Đang tạo rule Nginx chặn thực thi PHP trong uploads/cache...")
    nginx_conf_dir = f"{site_dir}/conf/nginx"
    os.makedirs(nginx_conf_dir, exist_ok=True)
    conf_path = f"{nginx_conf_dir}/mme-lock.conf"
    
    nginx_rules = """# MMe Lock: Chặn thực thi PHP trong thư mục nguy hiểm
location ~* /wp-content/(?:uploads|cache)/.*\\.php$ {
    deny all;
    access_log off;
    log_not_found off;
}"""
    with open(conf_path, 'w', encoding='utf-8') as f:
        f.write(nginx_rules)
    
    # Reload Nginx
    subprocess.run(["wo", "stack", "reload", "--nginx"], check=False)

    # 3. Chạy role cho domain
    log_info("Đang chuẩn hóa quyền thư mục (mme role)...")
    log_info("Đổi chủ sở hữu sang www-data:www-data...")
    subprocess.run(["chown", "-R", "www-data:www-data", site_dir])
    log_info("Phân quyền 755 cho thư mục và 644 cho file...")
    subprocess.run(["find", site_dir, "-type", "d", "-exec", "chmod", "755", "{}", "+"])
    subprocess.run(["find", site_dir, "-type", "f", "-exec", "chmod", "644", "{}", "+"])

    log_info(f"✅ Đã BẬT khóa bảo mật thành công cho {domain}!")

def cmd_site_lockoff(args):
    domain = args.domain
    site_dir = f"/var/www/{domain}"
    htdocs = f"{site_dir}/htdocs"
    
    if not os.path.exists(htdocs):
        log_error(f"Site {domain} không tồn tại.")
        return

    log_info(f"Đang TẮT khóa bảo mật (Lock OFF) cho {domain}...")

    # 1. Bật lại sửa theme/plugin
    log_info("Đang cập nhật wp-config.php (Cho phép sửa file)...")
    subprocess.run(f"wp config set DISALLOW_FILE_EDIT false --raw --path={htdocs} --allow-root", shell=True)
    subprocess.run(f"wp config set DISALLOW_FILE_MODS false --raw --path={htdocs} --allow-root", shell=True)

    # 2. Xóa rule Nginx
    conf_path = f"{site_dir}/conf/nginx/mme-lock.conf"
    if os.path.exists(conf_path):
        log_info("Đang gỡ bỏ rule chặn PHP Nginx...")
        os.remove(conf_path)
        subprocess.run(["wo", "stack", "reload", "--nginx"], check=False)

    log_info("Đang chuẩn hóa quyền thư mục (mme role)...")
    subprocess.run(["chown", "-R", "www-data:www-data", site_dir])

    log_info(f"✅ Đã TẮT khóa bảo mật thành công cho {domain}! Có thể cài đặt/sửa file bình thường.")

# ==================== MAIN PARSER ====================

CUSTOM_HELP = """
==================================================
 WordOps MMe CLI Tool - Trợ lý vận hành siêu tốc
==================================================

 Các lệnh có thể dùng:
 mme deploy add <domain>      (Thêm cấu hình Auto Deploy)
 mme deploy list              (Xem danh sách Auto Deploy)
 mme deploy run <domain>      (Chạy Deploy thủ công)
 mme deploy rollback <domain> (Khôi phục bản cũ)
 mme deploy logs <domain>     (Xem nhật ký Deploy)
 mme site pause <domain>      (Bật chế độ bảo trì)
 mme site start <domain>      (Tắt chế độ bảo trì)
 mme site lockon <domain>     (Bật khóa bảo mật site)
 mme site lockoff <domain>    (Tắt khóa bảo mật site)
 mme role                     (Fix quyền 644/755/www-data)
 mme site clone <old> <new>   (Nhân bản website)
 mme db                       (Sửa cấu hình MySQL/MariaDB)
 
 Gõ `mme <lệnh> --help` để xem chi tiết cách dùng của một nhóm lệnh.
==================================================
"""

def cmd_db(args):
    log_info("Đang mở file cấu hình MySQL (/etc/mysql/conf.d/my.cnf)...")
    subprocess.run(["nano", "/etc/mysql/conf.d/my.cnf"])
    log_info("Ghi nhớ chạy lệnh `wo stack reload --mysql` hoặc `systemctl restart mariadb` để áp dụng cấu hình mới.")

def main():
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"]):
        print(CUSTOM_HELP.strip())
        sys.exit(0)

    parser = argparse.ArgumentParser(prog="mme", description="WordOps MMe CLI Tool - Trợ lý vận hành siêu tốc")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # --- db ---
    db_parser = subparsers.add_parser("db", help="Mở trình soạn thảo sửa cấu hình MySQL")
    db_parser.set_defaults(func=cmd_db)
    
    # --- role ---
    role_parser = subparsers.add_parser("role", help="Tự động cấp quyền 644/755/www-data cho thư mục hiện tại")
    role_parser.set_defaults(func=cmd_role)
    
    # --- deploy ---
    deploy_parser = subparsers.add_parser("deploy", help="Quản lý Git Auto Deploy")
    deploy_sub = deploy_parser.add_subparsers(dest="deploy_cmd", required=True)
    
    # deploy add
    deploy_add = deploy_sub.add_parser("add", help="Thêm cấu hình deploy cho domain")
    deploy_add.add_argument("domain", help="Tên miền (VD: mme.vn)")
    deploy_add.add_argument("--repo", required=True, help="Git repo URL")
    deploy_add.add_argument("--branch", default="main", help="Branch (mặc định: main)")
    deploy_add.add_argument("--path", default="", help="Đường dẫn lưu code (mặc định: root htdocs)")
    deploy_add.add_argument("--build", default="", help="Lệnh build (VD: npm run build)")
    deploy_add.set_defaults(func=cmd_deploy_add)
    
    # deploy list
    deploy_list = deploy_sub.add_parser("list", help="Danh sách cấu hình deploy")
    deploy_list.set_defaults(func=cmd_deploy_list)
    
    # deploy run
    deploy_run = deploy_sub.add_parser("run", help="Chạy deploy thủ công")
    deploy_run.add_argument("domain", help="Tên miền")
    deploy_run.set_defaults(func=cmd_deploy_run)
    
    # deploy rollback
    deploy_rollback = deploy_sub.add_parser("rollback", help="Khôi phục code bản trước đó")
    deploy_rollback.add_argument("domain", help="Tên miền")
    deploy_rollback.set_defaults(func=cmd_deploy_rollback)
    
    # deploy logs
    deploy_logs = deploy_sub.add_parser("logs", help="Xem nhật ký deploy")
    deploy_logs.add_argument("domain", help="Tên miền")
    deploy_logs.set_defaults(func=cmd_deploy_logs)
    
    # --- site ---
    site_parser = subparsers.add_parser("site", help="Quản lý website (bảo trì, nhân bản)")
    site_sub = site_parser.add_subparsers(dest="site_cmd", required=True)
    
    # site pause
    site_pause = site_sub.add_parser("pause", help="Bật chế độ bảo trì")
    site_pause.add_argument("domain", help="Tên miền")
    site_pause.set_defaults(func=cmd_site_pause)
    
    # site start
    site_start = site_sub.add_parser("start", help="Tắt chế độ bảo trì")
    site_start.add_argument("domain", help="Tên miền")
    site_start.set_defaults(func=cmd_site_start)
    
    # site lockon
    site_lockon = site_sub.add_parser("lockon", help="Bật khóa bảo mật site")
    site_lockon.add_argument("domain", help="Tên miền")
    site_lockon.set_defaults(func=cmd_site_lockon)
    
    # site lockoff
    site_lockoff = site_sub.add_parser("lockoff", help="Tắt khóa bảo mật site")
    site_lockoff.add_argument("domain", help="Tên miền")
    site_lockoff.set_defaults(func=cmd_site_lockoff)
    
    # site clone
    site_clone = site_sub.add_parser("clone", help="Nhân bản website")
    site_clone.add_argument("old_domain", help="Tên miền gốc")
    site_clone.add_argument("new_domain", help="Tên miền mới")
    site_clone.add_argument("--le", action="store_true", help="Cài SSL Let's Encrypt")
    site_clone.add_argument("--force", action="store_true", help="Ghi đè nếu site đã tồn tại")
    site_clone.set_defaults(func=cmd_site_clone)
    
    # Phân tích lệnh
    try:
        args = parser.parse_args()
        args.func(args)
    except Exception as e:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
