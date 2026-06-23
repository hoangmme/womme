import os
import json
import subprocess
from cement.core.controller import CementBaseController, expose
from wo.core.logging import Log

DEPLOY_CONFIG_FILE = "/etc/wo/mme-deploy.json"

def load_config():
    if not os.path.exists(DEPLOY_CONFIG_FILE):
        return {}
    try:
        with open(DEPLOY_CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_config(config):
    with open(DEPLOY_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def ensure_ssh_key():
    key_path = "/root/.ssh/id_ed25519"
    pub_key_path = f"{key_path}.pub"
    if not os.path.exists(key_path):
        Log.info(None, "Chưa có SSH Key. Đang tạo tự động SSH Deploy Key mới (Ed25519)...")
        subprocess.run(f'ssh-keygen -t ed25519 -f {key_path} -N "" -q', shell=True)
    
    if os.path.exists(pub_key_path):
        with open(pub_key_path, 'r') as f:
            pub_key = f.read().strip()
            Log.info(None, "================================================================")
            Log.info(None, "Public Key của Server (Hãy copy và thêm vào GitHub Deploy Keys):")
            Log.info(None, pub_key)
            Log.info(None, "================================================================")

class WOSiteCloneController(CementBaseController):
    class Meta:
        label = 'clone'
        stacked_on = 'site'
        stacked_type = 'nested'
        description = 'Nhân bản (Clone) một WordOps site hiện tại sang tên miền mới'
        arguments = [
            (['source_domain'], dict(help='Tên miền của site gốc cần clone')),
            (['dest_domain'], dict(help='Tên miền của site mới cần tạo')),
            (['--le'], dict(action='store_true', help='Tự động cài đặt SSL Let\'s Encrypt cho site mới')),
            (['--force'], dict(action='store_true', help='Bắt buộc tạo mới (nếu thư mục site đã tồn tại)')),
        ]

    @expose(hide=True)
    def default(self):
        source = self.app.pargs.source_domain
        dest = self.app.pargs.dest_domain
        le = self.app.pargs.le
        force = self.app.pargs.force

        Log.info(self, f"Bắt đầu quá trình clone từ {source} sang {dest}...")

        if not os.path.exists(f"/var/www/{source}/htdocs"):
            Log.error(self, f"Lỗi: Site gốc {source} không tồn tại trong /var/www/")
            return

        create_cmd = ["wo", "site", "create", dest, "--wp"]
        if le:
            create_cmd.append("--le")
        if force:
            create_cmd.append("--force")

        Log.info(self, f"Đang tạo site mới {dest} bằng WordOps...")
        result = subprocess.run(create_cmd)
        
        if result.returncode != 0 or not os.path.exists(f"/var/www/{dest}/htdocs"):
            Log.error(self, f"Lỗi: Quá trình tạo site mới {dest} thất bại.")
            return

        Log.info(self, "Đang sao chép tệp tin từ site gốc sang site mới...")
        
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

        Log.info(self, "Đang chuyển đổi cơ sở dữ liệu (Database)...")
        subprocess.run(f"wp db export /tmp/{source}.sql --path=/var/www/{source}/htdocs --allow-root", shell=True)
        subprocess.run(f"wp db import /tmp/{source}.sql --path=/var/www/{dest}/htdocs --allow-root", shell=True)
        if os.path.exists(f"/tmp/{source}.sql"):
            os.remove(f"/tmp/{source}.sql")

        Log.info(self, "Đang cập nhật URL tên miền trong Database...")
        subprocess.run(f"wp search-replace '//{source}' '//{dest}' --all-tables --path=/var/www/{dest}/htdocs --allow-root", shell=True)
        subprocess.run(f"wp search-replace '{source}' '{dest}' --all-tables --path=/var/www/{dest}/htdocs --allow-root", shell=True)

        Log.info(self, "Đang phân quyền thư mục và dọn dẹp cache...")
        subprocess.run(f"chown -R www-data:www-data /var/www/{dest}/htdocs", shell=True)
        subprocess.run("wo clean --all", shell=True)

        Log.info(self, f"Thành công! Site {source} đã được nhân bản hoàn chỉnh sang {dest}.")

class WOMMEBaseController(CementBaseController):
    class Meta:
        label = 'mme'
        stacked_on = 'base'
        stacked_type = 'nested'
        description = 'WordOps MMe Plugin Commands'
        arguments = []

    @expose(hide=True)
    def default(self):
        self.app.args.print_help()

class WOMMEDeployController(CementBaseController):
    class Meta:
        label = 'deploy'
        stacked_on = 'mme'
        stacked_type = 'nested'
        description = 'Git Auto Deploy Management'
        arguments = [
            (['--repo'], dict(help='Git Repository URL (VD: git@github.com:user/repo.git)')),
            (['--branch'], dict(help='Branch cần deploy (Mặc định: main)')),
            (['--path'], dict(help='Đường dẫn thư mục đích trong htdocs (VD: wp-content/themes/mme hoặc /)')),
            (['--build'], dict(help='Lệnh build chạy sau khi clone (VD: "npm ci && npm run build")')),
            (['domain_or_action'], dict(help='Tên miền (hoặc action như list)')),
            (['domain'], dict(nargs='?', help='Tên miền (cho lệnh run, rollback, logs)')),
        ]

    @expose(help="Quản lý job auto deploy (wo mme deploy <add|list|run|rollback|logs>)")
    def default(self):
        self.app.args.print_help()

    @expose(help="Thêm cấu hình auto deploy cho tên miền")
    def add(self):
        domain = self.app.pargs.domain_or_action
        if not domain:
            Log.error(self, "Lỗi: Thiếu tên miền.")
            return

        repo = self.app.pargs.repo
        if not repo:
            Log.error(self, "Lỗi: Phải truyền --repo=...")
            return

        branch = self.app.pargs.branch or "main"
        path = self.app.pargs.path or ""
        build = self.app.pargs.build or ""

        config = load_config()
        config[domain] = {
            "repo": repo,
            "branch": branch,
            "path": path,
            "build": build
        }
        save_config(config)

        Log.info(self, f"Đã lưu cấu hình Deploy cho domain: {domain}")
        ensure_ssh_key()
        Log.info(self, "Vui lòng lên GitHub/GitLab thêm Public Key ở trên vào phần Deploy Keys của kho mã nguồn (Nhớ cấp quyền read-only).")
        Log.info(self, f"Để chạy thử deploy lần đầu thủ công, hãy gõ lệnh: wo mme deploy run {domain}")

    @expose(help="Liệt kê các job auto deploy hiện tại")
    def list(self):
        config = load_config()
        if not config:
            Log.info(self, "Chưa có cấu hình deploy nào.")
            return
        Log.info(self, "Danh sách cấu hình Git Auto Deploy:")
        for domain, conf in config.items():
            print(f"- Domain: {domain}")
            print(f"  Repo:   {conf.get('repo')}")
            print(f"  Branch: {conf.get('branch')}")
            print(f"  Path:   {conf.get('path')}")
            print(f"  Build:  {conf.get('build')}")
            print("")

    @expose(help="Chạy thủ công quá trình deploy (không cần chờ Webhook)")
    def run(self):
        domain = self.app.pargs.domain_or_action
        if not domain:
            Log.error(self, "Lỗi: Vui lòng nhập tên miền (vd: wo mme deploy run mme.vn)")
            return
        Log.info(self, f"Đang kích hoạt deploy thủ công cho {domain}...")
        daemon_path = "/var/lib/wo/plugins/womme-daemon.py"
        if os.path.exists(daemon_path):
            subprocess.run(["python3", daemon_path, "--run", domain])
        else:
            # Dành cho lúc đang code/test ở thư mục hiện tại
            subprocess.run(["python3", os.path.join(os.path.dirname(__file__), "womme-daemon.py"), "--run", domain])

    @expose(help="Khôi phục lại phiên bản trước đó (Rollback)")
    def rollback(self):
        domain = self.app.pargs.domain_or_action
        if not domain:
            Log.error(self, "Lỗi: Vui lòng nhập tên miền (vd: wo mme deploy rollback mme.vn)")
            return
        Log.info(self, f"Đang kích hoạt Rollback cho {domain}...")
        daemon_path = "/var/lib/wo/plugins/womme-daemon.py"
        if os.path.exists(daemon_path):
            subprocess.run(["python3", daemon_path, "--rollback", domain])
        else:
            subprocess.run(["python3", os.path.join(os.path.dirname(__file__), "womme-daemon.py"), "--rollback", domain])

    @expose(help="Xem nhật ký deploy của tên miền")
    def logs(self):
        domain = self.app.pargs.domain_or_action
        if not domain:
            Log.error(self, "Lỗi: Vui lòng nhập tên miền (vd: wo mme deploy logs mme.vn)")
            return
        log_file = f"/var/log/womme/{domain}.log"
        if os.path.exists(log_file):
            subprocess.run(["tail", "-n", "50", log_file])
        else:
            Log.info(self, f"Chưa có nhật ký deploy nào cho {domain}.")

def load(app):
    app.handler.register(WOSiteCloneController)
    app.handler.register(WOMMEBaseController)
    app.handler.register(WOMMEDeployController)
