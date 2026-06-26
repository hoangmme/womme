#!/usr/bin/env python3
import os
import json
import sys
import subprocess
import hmac
import hashlib
import time
import shutil
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import pwd

DEPLOY_CONFIG_FILE = "/etc/wo/mme-deploy.json"
LOG_DIR = "/var/log/womme"
os.makedirs(LOG_DIR, exist_ok=True)

def log_message(domain, message):
    log_file = os.path.join(LOG_DIR, f"{domain}.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}\n"
    print(line.strip())
    with open(log_file, "a") as f:
        f.write(line)

def run_cmd(cmd, cwd=None):
    if cwd is None:
        cwd = '/'
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return result.returncode == 0, result.stdout
    except Exception as e:
        return False, str(e)

def load_config():
    if not os.path.exists(DEPLOY_CONFIG_FILE):
        return {}
    with open(DEPLOY_CONFIG_FILE, 'r') as f:
        return json.load(f)

def get_site_owner(domain):
    try:
        # Lấy user của thư mục /var/www/domain
        stat_info = os.stat(f"/var/www/{domain}")
        uid = stat_info.st_uid
        user = pwd.getpwuid(uid)[0]
        return user
    except:
        return "www-data"

def process_deploy(domain, config):
    log_message(domain, "=== BẮT ĐẦU DEPLOY ===")
    
    # Tạo lock để chống chạy trùng
    lock_file = f"/tmp/womme_deploy_{domain}.lock"
    if os.path.exists(lock_file):
        log_message(domain, "LỖI: Tiến trình deploy khác đang chạy (Lock file exists).")
        return False
    
    open(lock_file, 'w').close()

    try:
        repo = config.get("repo")
        branch = config.get("branch", "main")
        target_path = config.get("path", "").strip("/")
        build_cmd = config.get("build", "")

        # Xác định cấu trúc thư mục
        if target_path in ["", ".", "/htdocs"]:
            # Full site deploy
            base_dir = f"/var/www/{domain}"
            releases_dir = f"{base_dir}/releases"
            symlink_target = f"{base_dir}/htdocs"
        else:
            # Theme / Plugin deploy
            target_name = os.path.basename(target_path)
            if not target_name:
                log_message(domain, "LỖI: Đường dẫn path không hợp lệ.")
                return False
            releases_dir = f"/var/www/{domain}/mme-releases/{target_name}"
            symlink_target = f"/var/www/{domain}/htdocs/{target_path}"

        os.makedirs(releases_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        new_release_dir = f"{releases_dir}/{timestamp}"

        # 1. Clone Code
        os.environ["GIT_SSH_COMMAND"] = "ssh -o StrictHostKeyChecking=no -i /root/.ssh/id_ed25519"
        if branch:
            log_message(domain, f"Đang clone từ {repo} (branch: {branch}) vào {new_release_dir}...")
            clone_cmd = f"git clone --depth 1 --branch {branch} {repo} {new_release_dir}"
        else:
            log_message(domain, f"Đang clone từ {repo} (default branch) vào {new_release_dir}...")
            clone_cmd = f"git clone --depth 1 {repo} {new_release_dir}"
            
        success, out = run_cmd(clone_cmd)
        if not success:
            log_message(domain, f"LỖI Clone: {out}")
            return False
        
        # Xóa thư mục .git cho nhẹ
        run_cmd(f"rm -rf {new_release_dir}/.git")

        # 2. Build
        if build_cmd:
            log_message(domain, f"Đang chạy lệnh Build: {build_cmd}")
            success, out = run_cmd(build_cmd, cwd=new_release_dir)
            if not success:
                log_message(domain, f"LỖI Build: {out}")
                return False
            log_message(domain, f"Build output: {out}")

        # 3. Setup Symlink
        log_message(domain, "Đang chuyển đổi Symlink (Zero-downtime)...")
        # Nếu thư mục gốc đang là thư mục thật (không phải symlink), di chuyển nó sang thư mục backup an toàn
        if os.path.exists(symlink_target) and not os.path.islink(symlink_target):
            backup_name = f"{releases_dir}/original_backup_{timestamp}"
            shutil.move(symlink_target, backup_name)
            log_message(domain, f"Đã chuyển thư mục cũ sang {backup_name}")

        # Tạo symlink mới
        run_cmd(f"ln -sfn {new_release_dir} {symlink_target}")

        # 4. Phân quyền
        owner = get_site_owner(domain)
        log_message(domain, f"Đang phân quyền thư mục cho user {owner}:www-data...")
        run_cmd(f"chown -h {owner}:www-data {symlink_target}")
        run_cmd(f"chown -R {owner}:www-data {new_release_dir}")

        # 5. Xóa Cache WordOps
        log_message(domain, "Đang xóa cache WordOps...")
        run_cmd("wo clean --all")

        # 6. Retention (Giữ 5 bản release)
        log_message(domain, "Đang dọn dẹp các release cũ (Giữ lại 5 bản)...")
        success, releases_out = run_cmd(f"ls -1dt {releases_dir}/*")
        if success:
            releases = releases_out.strip().split('\n')
            if len(releases) > 5:
                for old_release in releases[5:]:
                    if old_release and os.path.exists(old_release):
                        run_cmd(f"rm -rf {old_release}")
                        log_message(domain, f"Đã xóa release cũ: {old_release}")

        log_message(domain, "=== DEPLOY THÀNH CÔNG ===")
        return True

    except Exception as e:
        log_message(domain, f"LỖI HỆ THỐNG TRONG QUÁ TRÌNH DEPLOY: {str(e)}")
        return False
    finally:
        if os.path.exists(lock_file):
            os.remove(lock_file)

# ---------------------------------------------------------
# HTTP SERVER CHO WEBHOOK
# ---------------------------------------------------------
class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # /hooks/<domain>
        if not self.path.startswith("/hooks/"):
            self.send_response(404)
            self.end_headers()
            return
            
        domain = self.path.split("/hooks/")[-1].strip("/")
        config = load_config().get(domain)
        
        if not config:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Domain config not found")
            return

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        # 1. Xác thực Signature (Nếu có cấu hình Secret)
        secret = config.get("secret")
        if secret:
            github_signature = self.headers.get('X-Hub-Signature-256')
            gitlab_token = self.headers.get('X-Gitlab-Token')
            
            if github_signature:
                expected_mac = hmac.new(secret.encode(), msg=post_data, digestmod=hashlib.sha256).hexdigest()
                expected_sig = "sha256=" + expected_mac
                if not hmac.compare_digest(expected_sig, github_signature):
                    self.send_response(403)
                    self.end_headers()
                    self.wfile.write(b"Invalid Github Signature")
                    return
            elif gitlab_token:
                if gitlab_token != secret:
                    self.send_response(403)
                    self.end_headers()
                    self.wfile.write(b"Invalid Gitlab Token")
                    return
            else:
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"Missing Signature/Token Header")
                return

        # 2. Lấy thông tin Branch
        try:
            payload = json.loads(post_data.decode('utf-8'))
            ref = payload.get('ref', '')
            push_branch = ref.split('/')[-1] if ref else ''
            
            target_branch = config.get("branch", "main")
            if push_branch and push_branch != target_branch:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(f"Push to branch {push_branch} ignored. Target is {target_branch}.".encode())
                return
        except:
            pass # Bỏ qua nếu parse JSON lỗi (thường là ping event)

        # Báo OK ngay lập tức để Github không bị timeout
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Webhook received. Deploying in background...")

        # Chạy deploy ngầm (fork)
        pid = os.fork()
        if pid == 0:
            process_deploy(domain, config)
            os._exit(0)

def run_server(port=8989):
    server_address = ('', port)
    httpd = HTTPServer(server_address, WebhookHandler)
    print(f"Bắt đầu WOMME Webhook Daemon tại port {port}...")
    httpd.serve_forever()

def process_rollback(domain, config):
    log_message(domain, "=== BẮT ĐẦU ROLLBACK ===")
    target_path = config.get("path", "").strip("/")
    if target_path in ["", ".", "/htdocs"]:
        base_dir = f"/var/www/{domain}"
        releases_dir = f"{base_dir}/releases"
        symlink_target = f"{base_dir}/htdocs"
    else:
        target_name = os.path.basename(target_path)
        releases_dir = f"/var/www/{domain}/mme-releases/{target_name}"
        symlink_target = f"/var/www/{domain}/htdocs/{target_path}"

    if not os.path.exists(releases_dir):
        log_message(domain, "Không tìm thấy thư mục releases.")
        return False
        
    success, releases_out = run_cmd(f"ls -1dt {releases_dir}/*")
    releases = [r for r in releases_out.strip().split('\n') if r and os.path.isdir(r)]
    
    if len(releases) < 2:
        log_message(domain, "Không đủ release để rollback (Cần ít nhất 2 bản ghi).")
        return False
        
    previous_release = releases[1]
    log_message(domain, f"Đang Rollback về bản: {previous_release}")
    
    run_cmd(f"ln -sfn {previous_release} {symlink_target}")
    
    owner = get_site_owner(domain)
    run_cmd(f"chown -h {owner}:www-data {symlink_target}")
    run_cmd("wo clean --all")
    
    broken_release = releases[0]
    run_cmd(f"rm -rf {broken_release}")
    log_message(domain, f"Đã xóa bản release lỗi: {broken_release}")
    
    log_message(domain, "=== ROLLBACK THÀNH CÔNG ===")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--run":
        domain = sys.argv[2]
        config = load_config().get(domain)
        if config:
            process_deploy(domain, config)
        else:
            print(f"Không tìm thấy cấu hình cho domain {domain}")
    elif len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        domain = sys.argv[2]
        config = load_config().get(domain)
        if config:
            process_rollback(domain, config)
        else:
            print(f"Không tìm thấy cấu hình cho domain {domain}")
    else:
        run_server()
