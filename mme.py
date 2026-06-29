#!/usr/bin/env python3
import os
import json
import subprocess
import argparse
import sys
import pwd
from datetime import datetime

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
    print(f"\033[92m[INFO] {msg}\033[0m")

def log_error(msg):
    print(f"\033[91m[ERROR] {msg}\033[0m", file=sys.stderr)

def load_config():
    if not os.path.exists(DEPLOY_CONFIG_FILE):
        return {}
    try:
        with open(DEPLOY_CONFIG_FILE, 'r') as f:
            config = json.load(f)
            
        migrated = False
        for domain, val in config.items():
            if isinstance(val, dict):
                config[domain] = [val]
                migrated = True
                
        if migrated:
            save_config(config)
            
        return config
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

def setup_nginx_webhook(domain):
    nginx_conf_dir = f"/var/www/{domain}/conf/nginx"
    if os.path.exists(nginx_conf_dir):
        webhook_conf = f"{nginx_conf_dir}/mme-webhook.conf"
        with open(webhook_conf, "w") as f:
            f.write(f"""location ^~ /mme-webhook {{
    proxy_pass http://127.0.0.1:8989;
    proxy_set_header X-MMe-Domain $host;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Hub-Signature-256 $http_x_hub_signature_256;
    proxy_set_header X-GitHub-Event $http_x_github_event;
    proxy_set_header X-GitHub-Delivery $http_x_github_delivery;
    proxy_set_header Content-Type $http_content_type;
}}
""")
        subprocess.run(["nginx", "-t"], capture_output=True)
        subprocess.run(["systemctl", "reload", "nginx"], capture_output=True)

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


def validate_paths(path_str):
    if not path_str: return []
    paths = [p.strip() for p in path_str.split(',')]
    valid_paths = []
    for p in paths:
        if not p: continue
        if p.startswith("/") or ".." in p:
            log_error(f"Đường dẫn không hợp lệ (không được dùng tuyệt đối hoặc chứa '../'): {p}")
            continue
        valid_paths.append(p)
    return valid_paths

def cmd_deploy_push(args):
    repo = args.repo
    branch = args.branch
    path = args.path
    build = args.build

    if not repo:
        print(f"\\n--- Cấu hình Git Auto Deploy cho domain: {args.domain} ---")
        repo = input("1. Nhập Git Repo URL (vd: git@github.com:user/repo.git): ").strip()
        while not repo:
            repo = input("   -> Git Repo URL bắt buộc phải nhập: ").strip()
            
        branch_input = input(f"2. Nhập Branch (Nhấn Enter để tự động lấy branch mặc định của repo): ").strip()
        if branch_input:
            branch = branch_input
            
        print("3. Bạn muốn deploy loại dự án nào?")
        print("   [1] Toàn bộ website (Thả code thẳng vào htdocs gốc)")
        print("   [2] Theme WordPress")
        print("   [3] Plugin WordPress")
        print("   [4] Tùy chỉnh đường dẫn riêng (Custom path)")
        type_choice = input("   -> Chọn (1/2/3/4) [Nhấn Enter mặc định là 1]: ").strip()
        
        repo_clean = repo.rstrip("/")
        repo_name = repo_clean.split("/")[-1].replace(".git", "") if repo_clean else ""
        if type_choice == "2":
            while True:
                theme_name = input("   -> Nhập chính xác tên thư mục Theme: ").strip()
                if theme_name:
                    path = f"wp-content/themes/{theme_name}"
                    print(f"   => Đã cấu hình đường dẫn Theme: \033[96m{path}\033[0m")
                    break
        elif type_choice == "3":
            while True:
                plugin_name = input("   -> Nhập chính xác tên thư mục Plugin: ").strip()
                if plugin_name:
                    path = f"wp-content/plugins/{plugin_name}"
                    print(f"   => Đã cấu hình đường dẫn Plugin: \033[96m{path}\033[0m")
                    break
        elif type_choice == "4":
            path_input = input(f"   -> Nhập đường dẫn con lưu code (Ví dụ: app/frontend): ").strip()
            path = path_input
        else:
            path = ""
            
        build_input = input(f"4. Nhập lệnh build - ví dụ: npm install (Nhấn Enter nếu không cần): ").strip()
        if build_input:
            build = build_input
            
        shared_files_input = input("5. Shared Files (Các file giữ lại vĩnh viễn, cách nhau dấu phẩy): ").strip()
        shared_files = validate_paths(shared_files_input)
        
        shared_dirs_input = input("6. Shared Dirs (Các thư mục giữ lại vĩnh viễn, cách nhau dấu phẩy): ").strip()
        shared_dirs = validate_paths(shared_dirs_input)
        
        health_check = input("7. Health Check Path (Nhấn Enter bỏ qua, hoặc nhập ví dụ: /api/health): ").strip()
        if health_check and not health_check.startswith("/"): health_check = "/" + health_check
        
        keep_releases = input("8. Số lượng release giữ lại (Keep Releases) [Mặc định 5]: ").strip()
        try:
            keep_releases = int(keep_releases) if keep_releases else 5
        except:
            keep_releases = 5
            
        print("-" * 50)

    import re
    # Chuẩn hóa Repo URL: Chuyển https:// thành git@ để dùng được với Deploy Key
    if repo.startswith("https://github.com/"):
        repo = repo.replace("https://github.com/", "git@github.com:")
    elif repo.startswith("https://gitlab.com/"):
        repo = repo.replace("https://gitlab.com/", "git@gitlab.com:")
        
    if repo.startswith("git@") and not repo.endswith(".git"):
        repo += ".git"
        
    # Chuẩn hóa Path: Bỏ qua thư mục htdocs nếu user lỡ nhập
    if path:
        path = path.strip("/")
        if path.startswith("htdocs/"):
            path = path[7:]
        path = path.strip("/")
        
        # Tự động thêm tên folder cho theme/plugin nếu user chỉ gõ tới wp-content/themes
        if path.endswith("themes") or path.endswith("plugins"):
            repo_name = repo.split("/")[-1].replace(".git", "")
            path = f"{path}/{repo_name}"
            print(f"[INFO] Tự động bổ sung tên thư mục vào Path: {path}")

    config = load_config()
    
    new_entry = {
        "repo": repo,
        "branch": branch,
        "path": path,
        "build": build,
        "shared_files": shared_files,
        "shared_dirs": shared_dirs,
        "health_check": health_check,
        "keep_releases": keep_releases
    }
    
    if args.domain in config:
        print(f"\nDomain \033[96m{args.domain}\033[0m đã có sẵn cấu hình deploy.")
        ans = input("Bạn muốn (1) Thêm cấu hình mới này bên cạnh cấu hình cũ, hay (2) Ghi đè toàn bộ cấu hình cũ? [1/2, Mặc định: 1]: ").strip()
        if ans == "2":
            config[args.domain] = [new_entry]
            log_info(f"Đã ghi đè cấu hình Deploy cho domain: {args.domain}")
        else:
            config[args.domain].append(new_entry)
            log_info(f"Đã thêm cấu hình Deploy mới cho domain: {args.domain}")
    else:
        config[args.domain] = [new_entry]
        log_info(f"Đã tạo cấu hình Deploy đầu tiên cho domain: {args.domain}")
    save_config(config)

    log_info(f"Đã lưu cấu hình Deploy cho domain: {args.domain}")
    ensure_ssh_key()
    
    print("\\n" + "="*64)
    print(" HƯỚNG DẪN CÀI ĐẶT GITHUB WEBHOOK & DEPLOY KEY")
    print("="*64)
    print("1. Copy toàn bộ Public Key (ở trên) và thêm vào phần:")
    print("   [Tên Repo của bạn] > Settings > Deploy Keys > Add deploy key")
    print("2. Thêm Webhook URL sau vào phần:")
    print("   [Tên Repo của bạn] > Settings > Webhooks > Add webhook")
    print(f"   - Payload URL: https://{args.domain}/wp-json/wpmme/v1/deploy")
    print("   - Content type: application/json")
    print("="*64 + "\n")
    
    log_info(f"Để chạy thử deploy lần đầu thủ công, hãy gõ lệnh: mme deploy pull {args.domain}")

def cmd_deploy_edit(args):
    config = load_config()
    if args.domain not in config:
        log_error(f"Domain {args.domain} chưa có cấu hình deploy. Vui lòng dùng lệnh 'mme deploy push' trước.")
        return
        
    conf_list = config[args.domain]
    if isinstance(conf_list, dict):
        conf_list = [conf_list]
        
    idx = 0
    if len(conf_list) > 1:
        print(f"\nDomain \033[96m{args.domain}\033[0m đang có {len(conf_list)} cấu hình:")
        for i, conf in enumerate(conf_list):
            print(f"  [{i+1}] Repo: {conf.get('repo', '')} -> Path: {conf.get('path', 'htdocs')}")
        while True:
            try:
                choice = int(input(f"Nhập số thứ tự cấu hình muốn sửa (1-{len(conf_list)}): ").strip())
                if 1 <= choice <= len(conf_list):
                    idx = choice - 1
                    break
            except:
                pass
                
    old_conf = conf_list[idx]
    
    print(f"\n--- Sửa cấu hình Git Auto Deploy cho domain: {args.domain} ---")
    print("Nhấn Enter nếu bạn muốn giữ nguyên giá trị cũ.")
    
    repo = input(f"1. Git Repo URL [{old_conf.get('repo')}]: ").strip()
    if not repo: repo = old_conf.get('repo', '')
    
    branch = input(f"2. Branch [{old_conf.get('branch')}]: ").strip()
    if not branch: branch = old_conf.get('branch', '')
    
    old_path = old_conf.get('path', '')
    
    print(f"3. Chọn Loại Code Mới (Nhấn Enter để giữ nguyên: \033[36m{old_path if old_path else 'Toàn bộ mã nguồn'}\033[0m):")
    print("   [1] Toàn bộ mã nguồn (Full Source)")
    print("   [2] Theme WordPress")
    print("   [3] Plugin WordPress")
    print("   [4] Tùy chỉnh đường dẫn riêng (Custom path)")
    type_choice = input("   -> Chọn (1/2/3/4) [Nhấn Enter bỏ qua]: ").strip()
    
    if type_choice == "1":
        path = ""
    elif type_choice == "2":
        while True:
            theme_name = input("   -> Nhập chính xác tên thư mục Theme: ").strip()
            if theme_name:
                path = f"wp-content/themes/{theme_name}"
                print(f"   => Đã cấu hình đường dẫn Theme: \033[96m{path}\033[0m")
                break
    elif type_choice == "3":
        while True:
            plugin_name = input("   -> Nhập chính xác tên thư mục Plugin: ").strip()
            if plugin_name:
                path = f"wp-content/plugins/{plugin_name}"
                print(f"   => Đã cấu hình đường dẫn Plugin: \033[96m{path}\033[0m")
                break
    elif type_choice == "4":
        path_input = input(f"   -> Nhập đường dẫn con lưu code (Ví dụ: app/frontend): ").strip()
        path = path_input
    else:
        path = old_path
        
    build = input(f"4. Build Command [{old_conf.get('build')}]: ").strip()
    if not build and old_conf.get('build'):
        build = old_conf.get('build', '')
        
    sf_default = ",".join(old_conf.get("shared_files", []))
    sf_input = input(f"5. Shared Files (Các file giữ lại vĩnh viễn) [{sf_default}]: ").strip()
    if not sf_input and "shared_files" in old_conf:
        shared_files = old_conf["shared_files"]
    else:
        shared_files = validate_paths(sf_input)
        
    sd_default = ",".join(old_conf.get("shared_dirs", []))
    sd_input = input(f"6. Shared Dirs (Các thư mục giữ lại vĩnh viễn) [{sd_default}]: ").strip()
    if not sd_input and "shared_dirs" in old_conf:
        shared_dirs = old_conf["shared_dirs"]
    else:
        shared_dirs = validate_paths(sd_input)
        
    hc_default = old_conf.get("health_check", "")
    health_check = input(f"7. Health Check Path [{hc_default}]: ").strip()
    if not health_check: health_check = hc_default
    if health_check and not health_check.startswith("/"): health_check = "/" + health_check
    
    kr_default = old_conf.get("keep_releases", 5)
    keep_releases = input(f"8. Số lượng release giữ lại [{kr_default}]: ").strip()
    if not keep_releases: keep_releases = kr_default
    try:
        keep_releases = int(keep_releases)
    except:
        keep_releases = 5
        
    import re
    if repo.startswith("https://github.com/"): repo = repo.replace("https://github.com/", "git@github.com:")
    elif repo.startswith("https://gitlab.com/"): repo = repo.replace("https://gitlab.com/", "git@gitlab.com:")
    if repo.startswith("git@") and not repo.endswith(".git"): repo += ".git"
    
    if path:
        path = path.strip("/")
        if path.startswith("htdocs/"): path = path[7:]
        path = path.strip("/")
        
    conf_list[idx] = {
        "repo": repo,
        "branch": branch,
        "path": path,
        "build": build,
        "shared_files": shared_files,
        "shared_dirs": shared_dirs,
        "health_check": health_check,
        "keep_releases": keep_releases
    }
    
    config[args.domain] = conf_list
    save_config(config)
    log_info(f"Đã cập nhật cấu hình Deploy cho domain: {args.domain}")
    
    # Thiết lập Nginx Webhook tự động
    setup_nginx_webhook(args.domain)
    
    ensure_ssh_key()
    
    print("\\n" + "="*64)
    print(" HƯỚNG DẪN CÀI ĐẶT GITHUB WEBHOOK & DEPLOY KEY")
    print("="*64)
    print("1. Copy toàn bộ Public Key (ở trên) và thêm vào phần:")
    print("   [Tên Repo của bạn] > Settings > Deploy Keys > Add deploy key")
    print("2. Thêm Webhook URL sau vào phần:")
    print("   [Tên Repo của bạn] > Settings > Webhooks > Add webhook")
    print(f"   - Payload URL: https://{args.domain}/mme-webhook")
    print("   - Content type: application/json")
    print("="*64 + "\\n")

def cmd_deploy_delete(args):
    config = load_config()
    if args.domain not in config:
        log_error(f"Domain {args.domain} chưa có cấu hình deploy nào.")
        return
        
    conf_list = config[args.domain]
    if isinstance(conf_list, dict):
        conf_list = [conf_list]
        
    if len(conf_list) == 1:
        ans = input(f"Bạn có chắc muốn xóa cấu hình deploy của {args.domain}? [y/N]: ").strip().lower()
        if ans == 'y':
            del config[args.domain]
            save_config(config)
            log_info(f"Đã xóa toàn bộ cấu hình deploy của {args.domain}.")
    else:
        print(f"\nDomain \033[96m{args.domain}\033[0m đang có {len(conf_list)} cấu hình:")
        for i, conf in enumerate(conf_list):
            print(f"  [{i+1}] Repo: {conf.get('repo', '')} -> Path: {conf.get('path', 'htdocs')}")
        print(f"  [{len(conf_list)+1}] \033[91mXóa toàn bộ cấu hình của domain này\033[0m")
        print("  [0] Hủy bỏ")
        
        while True:
            try:
                choice = int(input(f"Nhập số thứ tự cấu hình muốn xóa (0-{len(conf_list)+1}): ").strip())
                if choice == 0:
                    print("Đã hủy bỏ.")
                    return
                elif choice == len(conf_list) + 1:
                    ans = input(f"Bạn có chắc muốn xóa TOÀN BỘ cấu hình của {args.domain}? [y/N]: ").strip().lower()
                    if ans == 'y':
                        del config[args.domain]
                        save_config(config)
                        log_info(f"Đã xóa toàn bộ cấu hình deploy của {args.domain}.")
                    return
                elif 1 <= choice <= len(conf_list):
                    idx = choice - 1
                    deleted_repo = conf_list[idx].get('repo', '')
                    ans = input(f"Xác nhận xóa cấu hình [{choice}] ({deleted_repo})? [y/N]: ").strip().lower()
                    if ans == 'y':
                        conf_list.pop(idx)
                        if len(conf_list) == 0:
                            del config[args.domain]
                        else:
                            config[args.domain] = conf_list
                        save_config(config)
                        log_info(f"Đã xóa cấu hình [{choice}] của {args.domain}.")
                    return
            except:
                pass

def cmd_deploy_list(args):
    config = load_config()
    if not config:
        log_info("Chưa có cấu hình deploy nào.")
        return
        
    log_info("Đang kiểm tra kết nối Webhook & SSH (Vui lòng đợi vài giây)...")
    
    # 1. Kiểm tra kết nối SSH chung (1 lần duy nhất)
    ssh_status = "\033[91m❌ LỖI (Chưa thêm Public Key vào Github/Gitlab)\033[0m"
    os.environ["GIT_SSH_COMMAND"] = "ssh -o StrictHostKeyChecking=no -i /root/.ssh/id_ed25519 -o ConnectTimeout=5 -o BatchMode=yes"
    
    # Check nhanh với github
    res = subprocess.run(["ssh", "-T", "-o", "StrictHostKeyChecking=no", "-i", "/root/.ssh/id_ed25519", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes", "git@github.com"], capture_output=True, text=True)
    if "successfully authenticated" in res.stdout or "successfully authenticated" in res.stderr:
        ssh_status = "\033[92m✅ OK\033[0m"
    else:
        # Dự phòng check repo đầu tiên nếu xài gitlab
        for domain, conf in config.items():
            repo = conf.get('repo', '')
            if repo:
                res2 = subprocess.run(["git", "ls-remote", repo], capture_output=True)
                if res2.returncode == 0:
                    ssh_status = "\033[92m✅ OK\033[0m"
                break
                
        # 2. Kiểm tra trạng thái Webhook
        webhook_status = "\033[91m❌ LỖI (Webhook Endpoint không hoạt động)\033[0m"
        # Test new Nginx endpoint first
        curl_cmd_new = ["curl", "-L", "-X", "POST", "-s", "-o", "/dev/null", "-w", "%{http_code}", f"https://{domain}/mme-webhook"]
        res_new = subprocess.run(curl_cmd_new, capture_output=True, text=True)
        if res_new.stdout.strip() in ['200', '201']:
            webhook_status = "\033[92m✅ OK\033[0m (Nginx Endpoint)"
        else:
            # Fallback test old WPMMe endpoint
            curl_cmd_old = ["curl", "-L", "-X", "POST", "-s", "-o", "/dev/null", "-w", "%{http_code}", f"https://{domain}/wp-json/wpmme/v1/deploy"]
            res_old = subprocess.run(curl_cmd_old, capture_output=True, text=True)
            if res_old.stdout.strip() in ['200', '201']:
                webhook_status = "\033[92m✅ OK\033[0m (WPMMe Endpoint)"
                
        # 3. Lấy thời gian nhận webhook gần nhất
    if "❌ LỖI" in ssh_status:
        try:
            with open("/root/.ssh/id_ed25519.pub", "r") as f:
                pub_key = f.read().strip()
            ssh_status += f"\n                              \033[93m👉 Hãy copy đoạn Public Key dưới đây và thêm vào Github:\033[0m\n                              \033[36m{pub_key}\033[0m"
        except:
            pass
                
    print("\n\033[96m" + "="*60 + "\033[0m")
    print("\033[1;92m TRẠNG THÁI HỆ THỐNG\033[0m")
    print("\033[96m" + "="*60 + "\033[0m")
    print(f" Kết nối Github/Gitlab (SSH): {ssh_status}")
    print("\033[96m" + "="*60 + "\033[0m")
    
    print("\n\033[1;93m DANH SÁCH CẤU HÌNH GIT AUTO DEPLOY\033[0m")
    print("\033[96m" + "="*60 + "\033[0m")
    
    for domain, conf_list in config.items():
        if isinstance(conf_list, dict):
            conf_list = [conf_list]
            
        # 2. Kiểm tra trạng thái Webhook
        webhook_status = "\033[91m❌ LỖI (Webhook Endpoint không hoạt động)\033[0m"
        # Test new Nginx endpoint first
        curl_cmd = ["curl", "-L", "-X", "POST", "-s", "-o", "/dev/null", "-w", "%{http_code}", f"https://{domain}/mme-webhook"]
        res = subprocess.run(curl_cmd, capture_output=True, text=True)
        is_webhook_ok = res.stdout.strip() in ['200', '201']
        endpoint_type = "Nginx"
        
        if not is_webhook_ok:
            # Fallback test old WPMMe endpoint
            curl_cmd = ["curl", "-L", "-X", "POST", "-s", "-o", "/dev/null", "-w", "%{http_code}", f"https://{domain}/wp-json/wpmme/v1/deploy"]
            res = subprocess.run(curl_cmd, capture_output=True, text=True)
            is_webhook_ok = res.stdout.strip() in ['200', '201']
            endpoint_type = "WPMMe"
        # 3. Kiểm tra log để xem Github đã thực sự gọi Webhook bao giờ chưa & trạng thái Deploy
        last_webhook = ""
        deploy_status_msg = ""
        log_file = f"/var/log/womme/{domain}.log"
        if os.path.exists(log_file):
            try:
                with open(log_file, "r") as f:
                    lines = f.readlines()
                    for line in reversed(lines):
                        if not last_webhook and "⚡ Đã nhận Webhook thành công" in line:
                            parts = line.split("]", 1)
                            if len(parts) > 1:
                                time_str = parts[0].strip("[")
                                last_webhook = f" \033[90m(Nhận webhook: {time_str})\033[0m"
                                
                        if not deploy_status_msg:
                            if "=== DEPLOY THÀNH CÔNG ===" in line:
                                deploy_status_msg = "\n           \033[92m✅ Trạng thái Pull Code: Thành công\033[0m"
                            elif "LỖI Clone:" in line:
                                err = line.split("LỖI Clone:", 1)[1].strip()
                                if len(err) > 80: err = err[:77] + "..."
                                deploy_status_msg = f"\n           \033[91m❌ LỖI GIT PULL:\033[0m {err}\n           \033[93m👉 Sửa: Kiểm tra lại SSH Key Github/Gitlab hoặc chạy 'mme deploy logs {domain}'\033[0m"
                            elif "LỖI Build:" in line:
                                err = line.split("LỖI Build:", 1)[1].strip()
                                if len(err) > 80: err = err[:77] + "..."
                                deploy_status_msg = f"\n           \033[91m❌ LỖI BUILD:\033[0m {err}\n           \033[93m👉 Sửa: Xem lại cấu hình build hoặc chạy 'mme deploy logs {domain}'\033[0m"
                            elif "LỖI HỆ THỐNG TRONG QUÁ TRÌNH DEPLOY:" in line:
                                err = line.split("DEPLOY:", 1)[1].strip()
                                if len(err) > 80: err = err[:77] + "..."
                                deploy_status_msg = f"\n           \033[91m❌ LỖI HỆ THỐNG:\033[0m {err}"
                            elif "KHÔNG KHỚP repo nào" in line:
                                deploy_status_msg = f"\n           \033[91m❌ LỖI WEBHOOK:\033[0m Nhận được tín hiệu từ Github nhưng URL Repo không khớp cấu hình!\n           \033[93m👉 Sửa: Kiểm tra định dạng Payload (chọn application/json) hoặc check lại URL repo trong 'mme deploy edit {domain}'\033[0m"
                                
                        if last_webhook and deploy_status_msg:
                            break
            except:
                pass
                
        if is_webhook_ok:
            if last_webhook or deploy_status_msg:
                webhook_status = f"\033[92m✅ OK\033[0m ({endpoint_type}){last_webhook}{deploy_status_msg}"
                if "❌ LỖI WEBHOOK" in deploy_status_msg:
                    webhook_status = f"\033[91m❌ LỖI ĐỒNG BỘ\033[0m ({endpoint_type}){last_webhook}{deploy_status_msg}"
            else:
                webhook_status = f"\033[93m⚠️ Cổng đã mở ({endpoint_type}) (Chưa nhận được tín hiệu thực tế từ Github)\033[0m"
                webhook_status += f"\n           \033[93m👉 Payload URL cần cấu hình: \033[1;36mhttps://{domain}/mme-webhook\033[0m"
        else:
            webhook_status += f"\n           \033[93m👉 Payload URL: \033[1;36mhttps://{domain}/mme-webhook\033[0m"
            
        print(f"- Domain:  \033[1;96m{domain}\033[0m")
        print(f"  Webhook: {webhook_status}")
        
        for idx, conf in enumerate(conf_list):
            prefix = "  "
            if len(conf_list) > 1:
                print(f"  [{idx+1}] Repo: {conf.get('repo', '')}")
                prefix = "      "
            else:
                print(f"  Repo:    {conf.get('repo', '')}")
                
            if conf.get('branch'):
                print(f"{prefix}Branch:  {conf.get('branch')}")
                
            path_val = conf.get('path', '')
            if path_val:
                path_status = path_val
                full_path = f"/var/www/{domain}/htdocs/{path_val}"
                
                if path_val.startswith("wp-content/themes/"):
                    try:
                        active_theme_res = subprocess.run(
                            ["wp", "theme", "list", "--status=active", "--field=name", f"--path=/var/www/{domain}/htdocs", "--allow-root"],
                            capture_output=True, text=True, timeout=5
                        )
                        active_theme = active_theme_res.stdout.strip()
                        theme_folder = path_val.replace("wp-content/themes/", "").strip("/")
                        if active_theme and active_theme != theme_folder:
                            path_status += f"\n{prefix}     \033[93m⚠️ CẢNH BÁO: Đây KHÔNG PHẢI là theme đang kích hoạt ({active_theme}). Nếu cấu hình sai, gõ 'mme deploy edit {domain}' để sửa.\033[0m"
                    except:
                        pass
                elif path_val.startswith("wp-content/plugins/"):
                    if not os.path.exists(full_path):
                        path_status += f"\n{prefix}     \033[93m⚠️ CẢNH BÁO: Thư mục plugin này chưa tồn tại. Code đẩy về sẽ tạo thư mục mới nhưng plugin có thể chưa được kích hoạt.\033[0m"
                else:
                    if not os.path.exists(full_path):
                        path_status += f"\n{prefix}     \033[93m⚠️ CẢNH BÁO: Đường dẫn này không tồn tại trên máy chủ.\033[0m"
                        
                print(f"{prefix}Path:    {path_status}")
            if conf.get('build'):
                print(f"{prefix}Build:   {conf.get('build')}")
        print("\033[90m" + "-" * 60 + "\033[0m")

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

def cmd_deploy_pull(args):
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

    if os.path.exists(f"/var/www/{dest}"):
        if force:
            log_info(f"Site {dest} đã tồn tại, tiếp tục do có cờ --force...")
        else:
            log_error(f"Site mới {dest} đã tồn tại. Thêm --force để ghi đè.")
            return
    else:
        create_cmd = ["wo", "site", "create", dest, "--wp"]
        if le: create_cmd.append("--le")
        if force: create_cmd.append("--force")
    
        log_info(f"Đang tạo site mới {dest} bằng WordOps...")
        subprocess.run(create_cmd)
        
        if not os.path.exists(f"/var/www/{dest}/htdocs"):
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

import re

def cmd_site_rename(args):
    old_domain = args.old
    new_domain = args.new
    
    if old_domain == new_domain:
        log_error("Tên miền mới phải khác tên miền cũ!")
        return

    site_dir = f"/var/www/{old_domain}"
    if not os.path.exists(site_dir):
        log_error(f"Site gốc {old_domain} không tồn tại trong /var/www/")
        return

    # 1. Đọc DB cũ
    old_wp_config = f"{site_dir}/wp-config.php"
    if not os.path.exists(old_wp_config):
        log_error(f"Không tìm thấy {old_wp_config}")
        return
        
    with open(old_wp_config, "r") as f:
        content = f.read()
    match = re.search(r"define\(\s*'DB_NAME',\s*'([^']+)'\s*\);", content)
    if not match:
        log_error("Không tìm thấy DB_NAME trong wp-config.php cũ.")
        return
    old_db = match.group(1)

    # 2. Tạo site mới
    log_info(f"Đang tạo site mới {new_domain} (0 bytes dung lượng data)...")
    if os.path.exists(f"/var/www/{new_domain}"):
        if args.force:
            log_info(f"Site {new_domain} đã tồn tại, tiếp tục do có cờ --force...")
        else:
            log_error(f"Site mới {new_domain} đã tồn tại. Thêm --force để ghi đè.")
            return
    else:
        create_cmd = ["wo", "site", "create", new_domain, "--wp"]
        if args.le: create_cmd.append("--le")
        if args.force: create_cmd.append("--force")
        
        subprocess.run(create_cmd)
        if not os.path.exists(f"/var/www/{new_domain}/htdocs"):
            log_error(f"Quá trình tạo site mới {new_domain} thất bại.")
            return

    # 3. Đọc DB mới
    new_wp_config = f"/var/www/{new_domain}/wp-config.php"
    with open(new_wp_config, "r") as f:
        content = f.read()
    new_db = re.search(r"define\(\s*'DB_NAME',\s*'([^']+)'\s*\);", content).group(1)

    # 4. Di chuyển dữ liệu DB cực nhanh (0 bytes)
    log_info("Đang chuyển đổi cơ sở dữ liệu siêu tốc...")
    mysql_cmd = ["mysql", "-e", f"SHOW TABLES IN `{old_db}`;", "-s", "--skip-column-names"]
    res = subprocess.run(mysql_cmd, capture_output=True, text=True)
    tables = [t.strip() for t in res.stdout.strip().split("\\n") if t.strip()]
    
    if tables:
        subprocess.run(["wp", "db", "reset", "--yes", "--allow-root", f"--path=/var/www/{new_domain}/htdocs"])
        rename_queries = [f"`{old_db}`.`{t}` TO `{new_db}`.`{t}`" for t in tables]
        rename_sql = "RENAME TABLE " + ", ".join(rename_queries) + ";"
        subprocess.run(["mysql", "-e", rename_sql])

    # 5. Di chuyển Files (0 bytes disk)
    log_info("Đang di chuyển tệp tin (Instant, 0 bytes disk)...")
    subprocess.run(["rm", "-rf", f"/var/www/{new_domain}/htdocs"])
    subprocess.run(["mv", f"/var/www/{old_domain}/htdocs", f"/var/www/{new_domain}/htdocs"])
    
    # Kéo theo releases nếu có
    if os.path.exists(f"/var/www/{old_domain}/mme-releases"):
        subprocess.run(["mv", f"/var/www/{old_domain}/mme-releases", f"/var/www/{new_domain}/mme-releases"])

    # 6. Search Replace DB
    log_info("Đang cập nhật tên miền mới trong Database...")
    subprocess.run(f"wp search-replace '//{old_domain}' '//{new_domain}' --all-tables --path=/var/www/{new_domain}/htdocs --allow-root", shell=True)
    subprocess.run(f"wp search-replace '{old_domain}' '{new_domain}' --all-tables --path=/var/www/{new_domain}/htdocs --allow-root", shell=True)

    # 7. Xóa site cũ khỏi WordOps (File và DB đã rỗng nên an toàn)
    log_info("Đang dọn dẹp site cũ...")
    subprocess.run(["wo", "site", "delete", old_domain, "--no-prompt"])

    # Cập nhật config deploy mme nếu có
    config = load_config()
    if old_domain in config:
        config[new_domain] = config[old_domain]
        del config[old_domain]
        save_config(config)

    log_info(f"✅ Đã đổi tên miền từ {old_domain} sang {new_domain} thành công (Dung lượng không đổi)!")


def toggle_wp_config_constant(domain, constant_name, value):
    config_path = f"/var/www/{domain}/wp-config.php"
    if not os.path.exists(config_path):
        config_path = f"/var/www/{domain}/htdocs/wp-config.php"
        if not os.path.exists(config_path):
            log_error(f"Không tìm thấy wp-config.php cho {domain}")
            return False

    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Xóa định nghĩa cũ nếu có
    pattern = rf"(?i)\s*define\s*\(\s*['\"]{constant_name}['\"]\s*,[^;]+;\s*"
    content = re.sub(pattern, "\n", content)

    # Chèn định nghĩa mới vào trước dòng /* That's all, stop editing! */
    insert_str = f"\ndefine('{constant_name}', {value});\n"
    if "/* That's all, stop editing!" in content:
        content = content.replace("/* That's all, stop editing!", insert_str + "/* That's all, stop editing!")
    else:
        # Fallback chèn vào cuối
        content += insert_str

    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return True

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
    toggle_wp_config_constant(domain, "DISALLOW_FILE_EDIT", "true")
    toggle_wp_config_constant(domain, "DISALLOW_FILE_MODS", "true")

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
    toggle_wp_config_constant(domain, "DISALLOW_FILE_EDIT", "false")
    toggle_wp_config_constant(domain, "DISALLOW_FILE_MODS", "false")

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
\033[96m==================================================\033[0m
\033[1;92m WordOps MMe CLI Tool - Trợ lý vận hành siêu tốc\033[0m
\033[96m==================================================\033[0m

 \033[93mCác lệnh có thể dùng:\033[0m
 \033[96mmme deploy push <domain>\033[0m     (Thêm cấu hình Auto Deploy)
 \033[96mmme deploy edit <domain>\033[0m     (Sửa cấu hình Auto Deploy)
 \033[96mmme deploy list\033[0m              (Xem danh sách Auto Deploy)
 \033[96mmme deploy pull <domain>\033[0m     (Chạy Deploy thủ công)
 \033[96mmme deploy rollback <domain>\033[0m (Khôi phục bản cũ)
 \033[96mmme deploy logs <domain>\033[0m     (Xem nhật ký Deploy)
 \033[96mmme site pause <domain>\033[0m      (Bật chế độ bảo trì)
 \033[96mmme site start <domain>\033[0m      (Tắt chế độ bảo trì)
 \033[96mmme site lockon <domain>\033[0m     (Bật khóa bảo mật site)
 \033[96mmme site lockoff <domain>\033[0m    (Tắt khóa bảo mật site)
 \033[96mmme role\033[0m                     (Fix quyền 644/755/www-data)
 \033[96mmme copy <nguồn> <đích>\033[0m      (Sao chép thư mục sang VPS khác)
 \033[96mmme site clone <old> <new>\033[0m   (Nhân bản website)
 \033[96mmme site rename <old> <new>\033[0m  (Đổi tên miền website)
 \033[96mmme db\033[0m                       (Sửa cấu hình MySQL/MariaDB)
 \033[96mmme site wpmme <domain>\033[0m      (Cài & kích hoạt plugin WPMMe)
 \033[96mmme site thememme <domain>\033[0m   (Cài & kích hoạt theme WPMMe)
 \033[96mmme site mmeform <domain>\033[0m    (Cài & kích hoạt plugin MMeForm)
 \033[96mmme update\033[0m                   (Cập nhật MMe CLI lên bản mới nhất)
 
 \033[90mGõ `mme <lệnh> --help` để xem chi tiết cách dùng của một nhóm lệnh.\033[0m
\033[96m==================================================\033[0m
"""

def cmd_site_migrate(args):
    old_domain = args.old
    new_domain = args.new
    
    # Kiểm tra tránh truyền nhầm đường dẫn (vd: /var/www/...) thay vì domain
    if "/" in old_domain or "/" in new_domain:
        log_error("Tên miền không hợp lệ! Vui lòng chỉ nhập tên miền (VD: old.com new.com). Không nhập đường dẫn thư mục.")
        return
        
    print(f"\n--- MIGRATE WEBSITE: {old_domain} -> {new_domain} ---")
    
    # 1. Source Detection
    print("\n[1] Bắt đầu kiểm tra VPS Nguồn...")
    wp_root = f"/var/www/{old_domain}/htdocs"
    wp_config = f"/var/www/{old_domain}/wp-config.php"
    
    if os.path.exists(wp_root) and os.path.exists(wp_config):
        print(f"✅ Đã nhận diện chuẩn WordOps trên VPS nguồn:")
        print(f"   - WP root: {wp_root}")
        print(f"   - WP config: {wp_config}")
    else:
        print(f"⚠️ Không nhận diện được chuẩn WordOps cho domain: {old_domain}")
        wp_root = input("   -> Nhập đường dẫn WP Root (VD: /var/www/html): ").strip()
        while not os.path.exists(wp_root):
            wp_root = input("   -> Thư mục không tồn tại. Nhập lại WP Root: ").strip()
            
        wp_config = input("   -> Nhập đường dẫn wp-config.php: ").strip()
        while not os.path.exists(wp_config):
            wp_config = input("   -> File không tồn tại. Nhập lại wp-config.php: ").strip()
            
    # 2. Target SSH Prompt
    print("\n[2] Thông tin VPS Đích (Target VPS)")
    ssh_input = input("   -> Nhập kết nối SSH (VD: root@157.10.201.240:22 hoặc ssh://root@157.10.201.240:22): ").strip()
    
    ssh_user = "root"
    ssh_host = ""
    ssh_port = "22"
    
    # Parse logic
    if ssh_input.startswith("ssh://"):
        ssh_input = ssh_input[6:]
        
    if "@" in ssh_input:
        ssh_user, rest = ssh_input.split("@", 1)
    else:
        rest = ssh_input
        
    if ":" in rest:
        ssh_host, ssh_port = rest.split(":", 1)
    else:
        ssh_host = rest
        
    if not ssh_host:
        log_error("Không thể phân tích địa chỉ VPS đích.")
        return
        
    # 3. SSH Key Management
    ensure_ssh_key()
    ssh_key = "/root/.ssh/id_ed25519"
    pub_key_path = f"{ssh_key}.pub"
    if not os.path.exists(pub_key_path):
        ssh_key = "/root/.ssh/id_rsa"
        pub_key_path = f"{ssh_key}.pub"
        
    with open(pub_key_path, "r") as f:
        pub_key = f.read().strip()
        
    # 4. SSH Preflight Check
    ssh_cmd_base = ["ssh", "-i", ssh_key, "-p", ssh_port, "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5", f"{ssh_user}@{ssh_host}"]
    
    print(f"\n[3] Đang kiểm tra kết nối SSH tới {ssh_host}...")
    while True:
        res = subprocess.run(ssh_cmd_base + ["echo", "SSH_OK"], capture_output=True, text=True)
        if "SSH_OK" in res.stdout:
            print(f"✅ SSH kết nối thành công tới {ssh_host}")
            break
        else:
            print("\n❌ KHÔNG THỂ KẾT NỐI BẰNG KHÓA SSH HIỆN TẠI")
            print("Vui lòng truy cập vào VPS đích và dán khóa Public Key sau vào file: \033[96m/root/.ssh/authorized_keys\033[0m")
            print("-" * 60)
            print(f"\033[93m{pub_key}\033[0m")
            print("-" * 60)
            print("Gợi ý các lệnh cần chạy trên VPS đích (nếu chưa có sẵn thư mục .ssh):")
            print("  mkdir -p ~/.ssh && chmod 700 ~/.ssh && nano ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys")
            input("\n👉 Nhấn \033[92mENTER\033[0m sau khi bạn đã dán khóa thành công để thử lại... (hoặc Ctrl+C để thoát)")

    # 5. Target Preflight check (WordOps, htdocs, wp-cli)
    print("\n[4] Kiểm tra nền tảng trên VPS đích...")
    
    # Check WordOps
    res = subprocess.run(ssh_cmd_base + ["command -v wo"], capture_output=True, text=True)
    if not res.stdout.strip():
        log_error("VPS đích chưa cài đặt WordOps. Vui lòng cài WordOps trước khi migrate.")
        return
    print("   ✅ WordOps: Đã cài đặt")
    
    # Check Domain
    target_wp_root = f"/var/www/{new_domain}/htdocs"
    res = subprocess.run(ssh_cmd_base + [f"[ -d {target_wp_root} ] && echo YES"], capture_output=True, text=True)
    if "YES" not in res.stdout:
        log_error(f"Website đích chưa được tạo trên VPS. Vui lòng chạy lệnh sau trên VPS đích trước:")
        print(f"   wo site create {new_domain} --wp --php82 --le")
        return
    print(f"   ✅ Website: Đã tồn tại thư mục {target_wp_root}")
    
    # Check WP-CLI
    res = subprocess.run(ssh_cmd_base + ["command -v wp"], capture_output=True, text=True)
    if not res.stdout.strip():
        log_error("VPS đích chưa cài đặt WP-CLI.")
        return
        
    print("\n   🚀 MỌI THỨ ĐÃ SẴN SÀNG ĐỂ BẮT ĐẦU MIGRATE!")
    ans = input("   Bạn có muốn tiến hành ngay bây giờ? [Y/n]: ").strip().lower()
    if ans == 'n':
        return
        
    # 6. Backup target site
    print("\n[5] Đang thực hiện backup thư mục đích...")
    backup_folder = f"/var/www/{new_domain}/htdocs_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    subprocess.run(ssh_cmd_base + [f"mv {target_wp_root} {backup_folder} && mkdir -p {target_wp_root}"])
    
    # 7. Rsync Source Code
    print("\n[6] Đang đồng bộ Source Code (Rsync)...")
    rsync_cmd = [
        "rsync", "-avz",
        "--exclude=wp-content/cache/",
        "--exclude=*.log",
        "--exclude=wp-config.php",
        "--exclude=.user.ini",
        "-e", f"ssh -i {ssh_key} -p {ssh_port} -o StrictHostKeyChecking=no",
        f"{wp_root}/",
        f"{ssh_user}@{ssh_host}:{target_wp_root}/"
    ]
    # We use subprocess.call to show the output in real-time
    subprocess.call(rsync_cmd)
    
    # 8. Read source table_prefix and update target wp-config.php if needed
    print("\n[7] Kiểm tra và đồng bộ Table Prefix...")
    source_prefix = "wp_"
    try:
        with open(wp_config, "r") as f:
            for line in f:
                if "$table_prefix" in line and "=" in line:
                    # Parse: $table_prefix = 'wp_';
                    parts = line.split("=")
                    if len(parts) > 1:
                        val = parts[1].split(";")[0].strip().strip("'").strip('"')
                        if val:
                            source_prefix = val
                            break
    except:
        pass
    
    print(f"   -> Table prefix ở nguồn: {source_prefix}")
    # Update target table_prefix using wp-cli
    set_prefix_cmd = f"cd {target_wp_root} && wp config set table_prefix {source_prefix} --type=variable --allow-root"
    subprocess.run(ssh_cmd_base + [set_prefix_cmd])
    
    # 9. Database stream gzip
    print("\n[8] Đang chuyển Database bằng luồng nén GZIP...")
    export_cmd = f"wp db export - --allow-root --path={wp_root} | gzip"
    import_cmd = f"cd {target_wp_root} && gunzip | wp db import - --allow-root"
    ssh_full_cmd = f"ssh -i {ssh_key} -p {ssh_port} -o StrictHostKeyChecking=no {ssh_user}@{ssh_host} '{import_cmd}'"
    
    full_db_cmd = f"{export_cmd} | {ssh_full_cmd}"
    subprocess.call(full_db_cmd, shell=True)
    
    # 10. Search and replace
    print("\n[9] Đang thực hiện Search & Replace Database...")
    replacements = [
        (f"https://{old_domain}", f"https://{new_domain}"),
        (f"http://{old_domain}", f"https://{new_domain}"),
        (f"www.{old_domain}", f"{new_domain}"),
        (old_domain, new_domain)
    ]
    
    for old_str, new_str in replacements:
        sr_cmd = f"cd {target_wp_root} && wp search-replace '{old_str}' '{new_str}' --all-tables --allow-root"
        subprocess.run(ssh_cmd_base + [sr_cmd])
        
    # 11. Flush cache & fix permissions
    print("\n[10] Dọn dẹp Cache và phân quyền...")
    subprocess.run(ssh_cmd_base + [f"cd {target_wp_root} && wp cache flush --allow-root"])
    
    fix_perm = f"chown -R www-data:www-data /var/www/{new_domain} && " \
               f"find /var/www/{new_domain} -type d -exec chmod 755 {{}} \\; && " \
               f"find /var/www/{new_domain} -type f -exec chmod 644 {{}} \\; && " \
               f"chmod 640 /var/www/{new_domain}/wp-config.php"
    subprocess.run(ssh_cmd_base + [fix_perm])
    
    # 12. Health check
    print("\n[11] Health Check sau Migrate...")
    # Check Nginx
    res = subprocess.run(ssh_cmd_base + ["nginx -t"], capture_output=True, text=True)
    if "successful" in res.stderr or "successful" in res.stdout:
        print("   ✅ Nginx syntax: OK")
    else:
        print("   ⚠️ Lỗi cú pháp Nginx. Hãy kiểm tra lại.")
        
    # Check HTTP status locally
    res = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", f"https://{new_domain}"], capture_output=True, text=True)
    print(f"   ✅ HTTP Status Code ({new_domain}): {res.stdout.strip()}")
    
    print(f"\n🎉 HOÀN TẤT MIGRATE: {old_domain} -> {new_domain}")
    print("Vui lòng trỏ lại Domain DNS hoặc cấu hình hosts file trên máy cá nhân để kiểm tra website mới.")


def cmd_wpmme(args):
    domain = args.domain
    site_dir = f"/var/www/{domain}"
    if not os.path.exists(site_dir):
        log_error(f"Site {domain} không tồn tại trong /var/www/")
        return
        
    htdocs_dir = f"{site_dir}/htdocs"
    if not os.path.exists(f"{htdocs_dir}/wp-config.php") and not os.path.exists(f"{site_dir}/wp-config.php"):
        log_error(f"Site {domain} không phải là WordPress (không tìm thấy wp-config.php).")
        return

    log_info(f"Đang cài đặt và kích hoạt plugin WPMMe cho {domain}...")
    
    plugin_url = "https://github.com/hoangmme/wpmme/archive/refs/heads/main.zip"
    cmd = [
        "wp", "plugin", "install", plugin_url,
        "--activate", "--force",
        f"--path={htdocs_dir}",
        "--allow-root"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        log_info(f"Đã cài đặt và kích hoạt thành công plugin wpmme cho {domain}.")
        
        # Tự động phân quyền
        plugin_dir = f"{htdocs_dir}/wp-content/plugins/wpmme"
        if os.path.exists(plugin_dir):
            log_info("Đang tự động phân quyền (mme role) cho thư mục plugin...")
            subprocess.run(["chown", "-R", "www-data:www-data", plugin_dir])
            subprocess.run(["find", plugin_dir, "-type", "d", "-exec", "chmod", "755", "{}", "+"])
            subprocess.run(["find", plugin_dir, "-type", "f", "-exec", "chmod", "644", "{}", "+"])
            
        log_info("Đang xóa cache để áp dụng thay đổi...")
        subprocess.run(["wo", "clean", "--all"], capture_output=True)
    else:
        log_error(f"Lỗi khi cài đặt plugin:\\n{result.stderr}")

def cmd_thememme(args):
    domain = args.domain
    site_dir = f"/var/www/{domain}"
    if not os.path.exists(site_dir):
        log_error(f"Site {domain} không tồn tại trong /var/www/")
        return
        
    htdocs_dir = f"{site_dir}/htdocs"
    if not os.path.exists(f"{htdocs_dir}/wp-config.php") and not os.path.exists(f"{site_dir}/wp-config.php"):
        log_error(f"Site {domain} không phải là WordPress (không tìm thấy wp-config.php).")
        return

    log_info(f"Đang cài đặt và kích hoạt theme WPMMe cho {domain}...")
    
    theme_url = "https://github.com/hoangmme/thememme/archive/refs/heads/main.zip"
    cmd = [
        "wp", "theme", "install", theme_url,
        "--activate", "--force",
        f"--path={htdocs_dir}",
        "--allow-root"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        log_info(f"Đã cài đặt và kích hoạt thành công theme thememme cho {domain}.")
        
        # Tự động phân quyền toàn bộ thư mục themes
        theme_dir = f"{htdocs_dir}/wp-content/themes"
        if os.path.exists(theme_dir):
            log_info("Đang tự động phân quyền (mme role) cho thư mục themes...")
            subprocess.run(["chown", "-R", "www-data:www-data", theme_dir])
            subprocess.run(["find", theme_dir, "-type", "d", "-exec", "chmod", "755", "{}", "+"])
            subprocess.run(["find", theme_dir, "-type", "f", "-exec", "chmod", "644", "{}", "+"])
            
        log_info("Đang xóa cache để áp dụng thay đổi...")
        subprocess.run(["wo", "clean", "--all"], capture_output=True)
    else:
        log_error(f"Lỗi khi cài đặt theme:\\n{result.stderr}")

def cmd_mmeform(args):
    domain = args.domain
    site_dir = f"/var/www/{domain}"
    if not os.path.exists(site_dir):
        log_error(f"Site {domain} không tồn tại trong /var/www/")
        return
        
    htdocs_dir = f"{site_dir}/htdocs"
    if not os.path.exists(f"{htdocs_dir}/wp-config.php") and not os.path.exists(f"{site_dir}/wp-config.php"):
        log_error(f"Site {domain} không phải là WordPress (không tìm thấy wp-config.php).")
        return

    log_info(f"Đang cài đặt và kích hoạt plugin MMeForm cho {domain}...")
    
    plugin_url = "https://github.com/hoangmme/mmeform/archive/refs/heads/main.zip"
    cmd = [
        "wp", "plugin", "install", plugin_url,
        "--activate", "--force",
        f"--path={htdocs_dir}",
        "--allow-root"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        log_info(f"Đã cài đặt và kích hoạt thành công plugin mmeform cho {domain}.")
        
        # Tự động phân quyền
        plugin_dir = f"{htdocs_dir}/wp-content/plugins/mmeform"
        if os.path.exists(plugin_dir):
            log_info("Đang tự động phân quyền (mme role) cho thư mục plugin...")
            subprocess.run(["chown", "-R", "www-data:www-data", plugin_dir])
            subprocess.run(["find", plugin_dir, "-type", "d", "-exec", "chmod", "755", "{}", "+"])
            subprocess.run(["find", plugin_dir, "-type", "f", "-exec", "chmod", "644", "{}", "+"])
            
        log_info("Đang xóa cache để áp dụng thay đổi...")
        subprocess.run(["wo", "clean", "--all"], capture_output=True)
    else:
        log_error(f"Lỗi khi cài đặt plugin:\\n{result.stderr}")

def cmd_update(args):
    log_info("Đang cập nhật MMe CLI Tool lên phiên bản mới nhất từ GitHub...")
    cmd = "curl -sL https://raw.githubusercontent.com/hoangmme/womme/main/install.sh | bash"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        log_info("Đã cập nhật thành công!")
        print(result.stdout)
    else:
        log_error(f"Lỗi khi cập nhật:\\n{result.stderr}")

def cmd_db(args):
    log_info("Đang mở file cấu hình MySQL (/etc/mysql/conf.d/my.cnf)...")
    subprocess.run(["nano", "/etc/mysql/conf.d/my.cnf"])
    log_info("Ghi nhớ chạy lệnh `wo stack reload --mysql` hoặc `systemctl restart mariadb` để áp dụng cấu hình mới.")


def cmd_port(args):
    port = args.port
    if not port.isdigit() or not (1 <= int(port) <= 65535):
        log_error("Port không hợp lệ. Vui lòng nhập số từ 1 - 65535.")
        return
        
    print(f"\n--- THAY ĐỔI PORT SSH SANG {port} ---")
    
    sshd_config = "/etc/ssh/sshd_config"
    if not os.path.exists(sshd_config):
        log_error(f"Không tìm thấy file cấu hình {sshd_config}")
        return
        
    # Sửa cấu hình
    log_info("Đang cập nhật /etc/ssh/sshd_config...")
    with open(sshd_config, "r") as f:
        lines = f.readlines()
        
    port_updated = False
    for i, line in enumerate(lines):
        if line.strip().startswith("Port ") or line.strip().startswith("#Port "):
            lines[i] = f"Port {port}\n"
            port_updated = True
            
    if not port_updated:
        lines.append(f"\nPort {port}\n")
        
    with open(sshd_config, "w") as f:
        f.writelines(lines)
        
    import subprocess
    # Mở port UFW
    log_info(f"Đang mở port {port}/tcp trên UFW firewall...")
    subprocess.run(["ufw", "allow", f"{port}/tcp"], capture_output=True)
    subprocess.run(["ufw", "reload"], capture_output=True)
    
    # Restart SSH
    log_info("Đang khởi động lại dịch vụ SSH...")
    subprocess.run(["systemctl", "restart", "ssh"], capture_output=True)
    subprocess.run(["systemctl", "restart", "sshd"], capture_output=True)
    
    print("\n✅ Đã thay đổi port SSH thành công!")
    print("\033[93m⚠️ QUAN TRỌNG: KHÔNG ĐƯỢC ĐÓNG TERMINAL NÀY!\033[0m")
    print(f"1. Hãy mở một tab terminal MỚI và thử kết nối lại với port mới:")
    print(f"   \033[96mssh -p {port} root@<IP_VPS_CỦA_BẠN>\033[0m")
    print(f"2. NẾU BẠN VÀO ĐƯỢC THÀNH CÔNG ở tab mới, bạn có thể xóa port 22 cũ bằng lệnh:")
    print(f"   \033[96mufw delete allow 22/tcp\033[0m")

def cmd_copy(args):
    source_dir = args.source.rstrip("/")
    dest_dir = args.dest
    
    if not os.path.exists(source_dir):
        log_error(f"Đường dẫn nguồn {source_dir} không tồn tại!")
        return
        
    print("\n" + "="*64)
    print(f" BẠN ĐANG CHUẨN BỊ COPY THƯ MỤC SANG VPS MỚI")
    print(f" Nguồn: {source_dir}")
    print(f" Đích:  {dest_dir}")
    print("="*64)
    
    conn_str = input("Nhập thông tin VPS đích (VD: root@103.110.87.69:22 hoặc chỉ nhập IP): ").strip()
    if not conn_str:
        log_error("Thông tin VPS đích không được để trống!")
        return
        
    user = "root"
    port = "22"
    ip = conn_str
    
    if "@" in ip:
        user, ip = ip.split("@", 1)
    if ":" in ip:
        ip, port = ip.split(":", 1)

    # Đảm bảo có SSH key
    ensure_ssh_key()
    
    pub_key_path = "/root/.ssh/id_ed25519.pub"
    if not os.path.exists(pub_key_path):
        pub_key_path = "/root/.ssh/id_rsa.pub"
        
    with open(pub_key_path, "r") as f:
        pub_key = f.read().strip()
        
    print("\n" + "="*64)
    print(" BƯỚC 1: CẤP QUYỀN Ở VPS ĐÍCH")
    print("="*64)
    print(f"Bạn hãy mở một phần mềm SSH mới, đăng nhập vào VPS đích ({ip})")
    print("sau đó copy và dán đoạn lệnh dưới đây vào rồi nhấn Enter:")
    print(f"\nmkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '{pub_key}' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys\n")
    print("="*64)
    
    input("BƯỚC 2: Sau khi đã chạy lệnh trên ở VPS đích, hãy nhấn Enter tại đây để bắt đầu copy...")
    
    log_info(f"Đang tạo trước thư mục đích tại {user}@{ip}...")
    mkdir_cmd = ["ssh", "-p", port, "-o", "StrictHostKeyChecking=no", "-i", "/root/.ssh/id_ed25519", f"{user}@{ip}", f"mkdir -p {dest_dir}"]
    res = subprocess.run(mkdir_cmd)
    if res.returncode != 0:
        log_error("Lỗi kết nối SSH đến VPS đích. Bạn đã chạy lệnh cấp quyền ở VPS đích chưa?")
        return

    log_info(f"Đang bắt đầu chuyển dữ liệu (Tốc độ phụ thuộc vào mạng)...")
    
    # Xử lý phân biệt file và thư mục
    rsync_source = source_dir
    if os.path.isdir(source_dir):
        rsync_source += "/" # Chỉ copy nội dung, không tạo thêm thư mục cha lồng nhau
        
    rsync_cmd = [
        "rsync", "-avz", "--progress",
        "-e", f"ssh -p {port} -o StrictHostKeyChecking=no -i /root/.ssh/id_ed25519",
        rsync_source,
        f"{user}@{ip}:{dest_dir}"
    ]
    
    try:
        res = subprocess.run(rsync_cmd)
        if res.returncode == 0:
            log_info("✅ Quá trình copy đã hoàn tất xuất sắc!")
        else:
            log_error(f"Quá trình copy bị lỗi (Mã lỗi rsync: {res.returncode}). Vui lòng kiểm tra lại log bên trên.")
    except Exception as e:
        log_error(f"Lỗi hệ thống khi chạy rsync: {str(e)}")

def main():
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"]):
        print(CUSTOM_HELP.strip())
        sys.exit(0)

    parser = argparse.ArgumentParser(prog="mme", description="WordOps MMe CLI Tool - Trợ lý vận hành siêu tốc")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # --- db ---
    db_parser = subparsers.add_parser("db", help="Mở trình soạn thảo sửa cấu hình MySQL")
    db_parser.set_defaults(func=cmd_db)
    
    # --- update ---
    update_parser = subparsers.add_parser("update", help="Cập nhật MMe CLI Tool lên phiên bản mới nhất")
    update_parser.set_defaults(func=cmd_update)
    
    # --- role ---
    role_parser = subparsers.add_parser("role", help="Tự động cấp quyền 644/755/www-data cho thư mục hiện tại")
    role_parser.set_defaults(func=cmd_role)
    
    # --- port ---
    port_parser = subparsers.add_parser("port", help="Thay đổi port SSH của VPS")
    port_parser.add_argument("port", help="Số port mới (VD: 2222)")
    port_parser.set_defaults(func=cmd_port)

    # --- copy ---
    copy_parser = subparsers.add_parser("copy", help="Sao chép thư mục sang VPS khác qua rsync")
    copy_parser.add_argument("source", help="Đường dẫn thư mục gốc (VD: /var/www/abc)")
    copy_parser.add_argument("dest", help="Đường dẫn thư mục đích trên VPS mới (VD: /var/www/xyz)")
    copy_parser.set_defaults(func=cmd_copy)
    
    # --- deploy ---
    deploy_parser = subparsers.add_parser("deploy", help="Quản lý Git Auto Deploy")
    deploy_sub = deploy_parser.add_subparsers(dest="deploy_cmd", required=True)
    
    # deploy push
    deploy_push = deploy_sub.add_parser("push", help="Thêm cấu hình deploy cho domain")
    deploy_push.add_argument("domain", help="Tên miền (VD: mme.vn)")
    deploy_push.add_argument("--repo", required=False, default=None, help="Git repo URL")
    deploy_push.add_argument("--branch", default="", help="Branch (Mặc định: Tự động lấy branch chính của repo)")
    deploy_push.add_argument("--path", default="", help="Đường dẫn lưu code (mặc định: root htdocs)")
    deploy_push.add_argument("--build", default="", help="Lệnh build (VD: npm run build)")
    deploy_push.set_defaults(func=cmd_deploy_push)
    
    # deploy edit
    deploy_edit = deploy_sub.add_parser("edit", help="Sửa cấu hình deploy hiện tại")
    deploy_edit.add_argument("domain", help="Tên miền (VD: mme.vn)")
    deploy_edit.set_defaults(func=cmd_deploy_edit)
    
    # deploy list
    deploy_list = deploy_sub.add_parser("list", help="Danh sách cấu hình deploy")
    deploy_list.set_defaults(func=cmd_deploy_list)
    
    # deploy pull
    deploy_pull = deploy_sub.add_parser("pull", help="Chạy deploy thủ công")
    deploy_pull.add_argument("domain", help="Tên miền")
    deploy_pull.set_defaults(func=cmd_deploy_pull)
    
    # deploy rollback
    deploy_rollback = deploy_sub.add_parser("rollback", help="Khôi phục code bản trước đó")
    deploy_rollback.add_argument("domain", help="Tên miền")
    deploy_rollback.set_defaults(func=cmd_deploy_rollback)
    
    # deploy logs
    deploy_logs = deploy_sub.add_parser("logs", help="Xem nhật ký deploy")
    deploy_logs.add_argument("domain", help="Tên miền")
    deploy_logs.set_defaults(func=cmd_deploy_logs)
    
    # deploy delete
    deploy_delete = deploy_sub.add_parser("delete", help="Xóa cấu hình deploy")
    deploy_delete.add_argument("domain", help="Tên miền")
    deploy_delete.set_defaults(func=cmd_deploy_delete)
    
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
    site_clone.add_argument("--le", action="store_true", help="Cài đặt luôn SSL cho site mới")
    site_clone.add_argument("--force", action="store_true", help="Ép buộc chạy lệnh bỏ qua cảnh báo")
    site_clone.set_defaults(func=cmd_site_clone)
    
    # site rename
    site_rename = site_sub.add_parser("rename", help="Đổi tên miền website (0 bytes disk)")
    site_rename.add_argument("old", help="Tên miền cũ (VD: old.com)")
    site_rename.add_argument("new", help="Tên miền mới (VD: new.com)")
    site_rename.add_argument("--le", action="store_true", help="Cài đặt luôn SSL cho site mới")
    site_rename.add_argument("--force", action="store_true", help="Ép buộc chạy lệnh bỏ qua cảnh báo")
    site_rename.set_defaults(func=cmd_site_rename)
    
    # site migrate
    site_migrate = site_sub.add_parser("migrate", help="Di chuyển toàn bộ website sang VPS mới")
    site_migrate.add_argument("old", help="Tên miền cũ (VD: old.com)")
    site_migrate.add_argument("new", help="Tên miền mới (VD: new.com)")
    site_migrate.set_defaults(func=cmd_site_migrate)

    # site wpmme
    site_wpmme = site_sub.add_parser("wpmme", help="Cài và kích hoạt plugin WPMMe")
    site_wpmme.add_argument("domain", help="Tên miền (VD: mme.vn)")
    site_wpmme.set_defaults(func=cmd_wpmme)

    # site thememme
    site_thememme = site_sub.add_parser("thememme", help="Cài và kích hoạt theme WPMMe")
    site_thememme.add_argument("domain", help="Tên miền (VD: mme.vn)")
    site_thememme.set_defaults(func=cmd_thememme)
    
    # site mmeform
    site_mmeform = site_sub.add_parser("mmeform", help="Cài và kích hoạt plugin MMeForm")
    site_mmeform.add_argument("domain", help="Tên miền (VD: mme.vn)")
    site_mmeform.set_defaults(func=cmd_mmeform)
    
    # Phân tích lệnh
    try:
        args = parser.parse_args()
        args.func(args)
    except SystemExit:
        sys.exit(1)
    except Exception as e:
        import traceback
        log_error(f"Lỗi thực thi lệnh: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
