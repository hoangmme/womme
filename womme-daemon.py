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

def process_deploy(domain, config, trigger_type="Thủ công (mme deploy pull)"):
    log_message(domain, f"=== BẮT ĐẦU DEPLOY [{trigger_type}] ===")
    
    lock_file = f"/tmp/womme_deploy_{domain}.lock"
    import fcntl
    lock_fd = None
    try:
        lock_fd = open(lock_file, 'w')
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (BlockingIOError, OSError, IOError):
            log_message(domain, "LỖI: Tiến trình deploy khác đang chạy (Lock file is locked).")
            return False
    except Exception as e:
        log_message(domain, f"Không thể tạo deploy lock: {e}")
        return False

    try:
        repo = config.get("repo")
        branch = config.get("branch", "")
        target_path = config.get("path", "").strip("/")
        build_cmd = config.get("build", "")
        shared_files = config.get("shared_files", [])
        shared_dirs = config.get("shared_dirs", [])
        health_check = config.get("health_check", "")
        keep_releases = int(config.get("keep_releases", 5))

        if target_path in ["", ".", "htdocs"]:
            releases_dir = f"/var/www/{domain}/mme-releases/htdocs"
            symlink_target = f"/var/www/{domain}/htdocs"
            shared_base = f"/var/www/{domain}/mme-shared/htdocs"
        else:
            target_name = os.path.basename(target_path)
            if not target_name:
                log_message(domain, "LỖI: Đường dẫn path không hợp lệ.")
                return False
            releases_dir = f"/var/www/{domain}/mme-releases/{target_name}"
            symlink_target = f"/var/www/{domain}/htdocs/{target_path}"
            shared_base = f"/var/www/{domain}/mme-shared/{target_name}"

        current_release = None
        if os.path.islink(symlink_target):
            current_release = os.path.realpath(symlink_target)
        elif os.path.exists(symlink_target):
            current_release = symlink_target

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
            
        # Lưu thông tin commit hiện tại để hiển thị cho lệnh mme deploy list
        run_cmd("git log -1 --format='%cd (%cr) - %s' --date=format:'%Y-%m-%d %H:%M:%S' > .mme_commit", cwd=new_release_dir)
        run_cmd("git rev-parse HEAD > .mme_hash", cwd=new_release_dir)
        with open(f"{new_release_dir}/.mme_trigger", "w") as tf:
            tf.write(trigger_type)
        
        run_cmd(f"rm -rf {new_release_dir}/.git")

        # 2. Build
        if build_cmd:
            log_message(domain, f"Đang chạy lệnh Build: {build_cmd}")
            success, out = run_cmd(build_cmd, cwd=new_release_dir)
            if not success:
                log_message(domain, f"LỖI Build: {out}")
                return False
            log_message(domain, f"Build output: {out}")

        # 3. Setup Shared Storage
        owner = get_site_owner(domain)
        if shared_files or shared_dirs:
            log_message(domain, "Đang thiết lập Shared Storage...")
            os.makedirs(shared_base, exist_ok=True)
            
            for item in shared_dirs + shared_files:
                shared_target = os.path.join(shared_base, item)
                release_path = os.path.join(new_release_dir, item)
                
                if current_release and not os.path.exists(shared_target):
                    old_path = os.path.join(current_release, item)
                    if os.path.exists(old_path):
                        log_message(domain, f"Copy dữ liệu lần đầu: {item} -> mme-shared")
                        os.makedirs(os.path.dirname(shared_target), exist_ok=True)
                        if os.path.isdir(old_path):
                            shutil.copytree(old_path, shared_target)
                        else:
                            shutil.copy2(old_path, shared_target)
                            
                if os.path.exists(release_path) or os.path.islink(release_path):
                    if os.path.isdir(release_path) and not os.path.islink(release_path):
                        shutil.rmtree(release_path)
                    else:
                        os.remove(release_path)
                        
                os.makedirs(os.path.dirname(release_path), exist_ok=True)
                os.makedirs(os.path.dirname(shared_target), exist_ok=True)
                
                if not os.path.exists(shared_target):
                    if item in shared_dirs:
                        os.makedirs(shared_target, exist_ok=True)
                    else:
                        open(shared_target, 'a').close()
                        
                os.symlink(shared_target, release_path)
                log_message(domain, f"Đã symlink: {item} -> mme-shared")
                
        # 4. Phân quyền
        log_message(domain, f"Đang phân quyền cho user {owner}:www-data...")
        run_cmd(f"chown -R {owner}:www-data {new_release_dir}")
        if shared_files or shared_dirs:
            run_cmd(f"chown -R {owner}:www-data {shared_base}")
            for d in shared_dirs:
                run_cmd(f"chmod -R 775 {os.path.join(shared_base, d)}")
            for f in shared_files:
                run_cmd(f"chmod 664 {os.path.join(shared_base, f)}")
                
        # 5. Preflight check
        if not os.path.exists(new_release_dir):
            log_message(domain, "LỖI PREFLIGHT: Thư mục release không tồn tại.")
            return False
            
        # 6. Atomic Switch htdocs
        log_message(domain, "Đang chuyển đổi Symlink (Atomic Switch)...")
        if os.path.exists(symlink_target) and not os.path.islink(symlink_target):
            backup_name = f"{releases_dir}/original_backup_{timestamp}"
            shutil.move(symlink_target, backup_name)
            log_message(domain, f"Đã backup thư mục thật sang {backup_name}")
            
        tmp_symlink = f"{symlink_target}_tmp"
        run_cmd(f"ln -sfn {new_release_dir} {tmp_symlink}")
        run_cmd(f"chown -h {owner}:www-data {tmp_symlink}")
        success, out = run_cmd(f"mv -Tf {tmp_symlink} {symlink_target}")
        if not success:
            log_message(domain, f"LỖI ATOMIC SWITCH: {out}")
            return False
        
        # 7. Post-switch Health Check
        if health_check:
            log_message(domain, f"Đang kiểm tra Health Check: {health_check}")
            curl_cmd = f"curl -s -o /dev/null -w '%{{http_code}}' https://{domain}{health_check} --insecure -m 10"
            success, out = run_cmd(curl_cmd)
            http_code = out.strip()
            if not success or http_code not in ['200', '201', '301', '302']:
                log_message(domain, f"LỖI HEALTH CHECK (Mã: {http_code}). Đang Rollback...")
                if current_release:
                    run_cmd(f"ln -sfn {current_release} {tmp_symlink}")
                    run_cmd(f"chown -h {owner}:www-data {tmp_symlink}")
                    run_cmd(f"mv -Tf {tmp_symlink} {symlink_target}")
                    log_message(domain, f"Đã Rollback về bản {current_release}")
                return False
            else:
                log_message(domain, f"Health Check OK (Mã: {http_code})")
                
        # 8. Xóa Cache WordOps
        run_cmd("wo clean --all")
        
        # 9. Cleanup Releases
        log_message(domain, f"Đang dọn dẹp các release cũ (Giữ lại {keep_releases} bản)...")
        success, releases_out = run_cmd(f"ls -1dt {releases_dir}/*")
        if success:
            releases = [r for r in releases_out.strip().split('\n') if r and 'original_backup' not in r]
            if len(releases) > keep_releases:
                for old_release in releases[keep_releases:]:
                    if old_release and os.path.exists(old_release):
                        run_cmd(f"rm -rf {old_release}")
                        log_message(domain, f"Đã xóa release cũ: {old_release}")

        log_message(domain, "=== DEPLOY THÀNH CÔNG ===")
        return True

    except Exception as e:
        log_message(domain, f"LỖI HỆ THỐNG TRONG QUÁ TRÌNH DEPLOY: {str(e)}")
        import traceback
        log_message(domain, traceback.format_exc())
        return False
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()
            if os.path.exists(lock_file):
                os.remove(lock_file)
        except:
            pass

# ---------------------------------------------------------
# HTTP SERVER CHO WEBHOOK
# ---------------------------------------------------------
class WebhookHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"MMe Webhook is running. Please send POST requests from Github/Gitlab.")
        
    def do_POST(self):
        if not (self.path.startswith("/mme-webhook") or self.path.startswith("/hooks/")):
            self.send_response(404)
            self.end_headers()
            return

        domain = self.headers.get("X-MMe-Domain")
        if self.path.startswith("/hooks/"):
            domain = self.path.split("/hooks/")[-1].strip("/")
            
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            payload_str = post_data.decode('utf-8')
            try:
                payload = json.loads(payload_str)
            except json.JSONDecodeError:
                from urllib.parse import parse_qs
                parsed = parse_qs(payload_str)
                if 'payload' in parsed:
                    payload = json.loads(parsed['payload'][0])
                else:
                    payload = {}
        except:
            payload = {}

        repo_ssh_url = payload.get('repository', {}).get('ssh_url', '')
        repo_html_url = payload.get('repository', {}).get('html_url', '')
        repo_clone_url = payload.get('repository', {}).get('clone_url', '')
        
        def get_repo_key(url):
            if not url: return ""
            url = url.strip().lower()
            url = url.replace("https://github.com/", "").replace("https://gitlab.com/", "")
            url = url.replace("git@github.com:", "").replace("git@gitlab.com:", "")
            url = url.rstrip("/")
            if url.endswith(".git"):
                url = url[:-4]
            return url.strip()

        webhook_repo_keys = [get_repo_key(u) for u in [repo_ssh_url, repo_html_url, repo_clone_url] if u]
        
        all_configs = load_config()
        matched_targets = []
        
        # Quét chéo toàn bộ các domain trên VPS để tìm TẤT CẢ các site đăng ký repo này
        for dom, conf_data in all_configs.items():
            conf_list = [conf_data] if isinstance(conf_data, dict) else conf_data
            for conf in conf_list:
                conf_repo_key = get_repo_key(conf.get("repo", ""))
                if conf_repo_key and conf_repo_key in webhook_repo_keys:
                    matched_targets.append((dom, conf))
                    
        if not matched_targets:
            if post_data:
                log_message("system", f"⚠️ Đã nhận Webhook nhưng KHÔNG KHỚP repo nào! (Webhook repo: {webhook_repo_keys})")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Webhook received but no matching repository config found.")
            return

        # Báo OK ngay lập tức để Github không bị timeout
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Webhook received. Deploying in background...")

        import threading
        for target_dom, target_conf in matched_targets:
            # 1. Xác thực Signature nếu có
            secret = target_conf.get("secret")
            if secret:
                github_signature = self.headers.get('X-Hub-Signature-256')
                gitlab_token = self.headers.get('X-Gitlab-Token')
                if github_signature:
                    expected_mac = hmac.new(secret.encode(), msg=post_data, digestmod=hashlib.sha256).hexdigest()
                    if not hmac.compare_digest("sha256=" + expected_mac, github_signature):
                        log_message(target_dom, "LỖI: Invalid Github Signature")
                        continue
                elif gitlab_token and gitlab_token != secret:
                    log_message(target_dom, "LỖI: Invalid Gitlab Token")
                    continue

            # 2. Branch check
            push_branch = ''
            try:
                ref = payload.get('ref', '')
                push_branch = ref.split('/')[-1] if ref else ''
                target_branch = target_conf.get("branch", "")
                if target_branch and push_branch and push_branch != target_branch:
                    log_message(target_dom, f"Bỏ qua deploy branch {push_branch} (Yêu cầu: {target_branch})")
                    continue
            except:
                pass

            log_message(target_dom, f"⚡ Đã nhận Webhook thành công từ Github/Gitlab (Branch: {push_branch})")
            t = threading.Thread(target=process_deploy, args=(target_dom, target_conf, "Tự động (Webhook)"))
            t.daemon = True
            t.start()

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
        config_data = load_config().get(domain)
        if config_data:
            conf_list = [config_data] if isinstance(config_data, dict) else config_data
            for conf in conf_list:
                process_deploy(domain, conf)
        else:
            print(f"Không tìm thấy cấu hình cho domain {domain}")
    elif len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        domain = sys.argv[2]
        config_data = load_config().get(domain)
        if config_data:
            conf_list = [config_data] if isinstance(config_data, dict) else config_data
            for conf in conf_list:
                process_rollback(domain, conf)
        else:
            print(f"Không tìm thấy cấu hình cho domain {domain}")
    else:
        run_server()
