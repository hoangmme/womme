import os
import json
import subprocess
from cement.core.controller import CementBaseController, expose
from wo.core.logging import Log

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
                <!-- Bạn có thể thay thế icon này bằng thẻ <img> chứa logo của bạn -->
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


class WOSitePauseController(CementBaseController):
    class Meta:
        label = 'pause'
        stacked_on = 'site'
        stacked_type = 'nested'
        description = 'Bật chế độ bảo trì (Maintenance) cho trang web'
        arguments = [
            (['domain'], dict(help='Tên miền cần bảo trì')),
        ]

    @expose(hide=True)
    def default(self):
        domain = self.app.pargs.domain
        if not domain:
            Log.error(self, "Lỗi: Vui lòng nhập tên miền.")
            return

        site_dir = f"/var/www/{domain}"
        if not os.path.exists(site_dir):
            Log.error(self, f"Lỗi: Site {domain} không tồn tại.")
            return

        Log.info(self, f"Đang bật chế độ bảo trì cho {domain}...")

        html_path = f"{site_dir}/htdocs/mme-maintenance.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(MAINTENANCE_HTML)

        nginx_conf_dir = f"{site_dir}/conf/nginx"
        os.makedirs(nginx_conf_dir, exist_ok=True)
        conf_path = f"{nginx_conf_dir}/mme-maintenance.conf"
        
        nginx_rules = """error_page 503 @mme_maintenance;
if (-f $document_root/mme-maintenance.html) {
    return 503;
}
location @mme_maintenance {
    rewrite ^(.*)$ /mme-maintenance.html break;
}"""
        with open(conf_path, 'w', encoding='utf-8') as f:
            f.write(nginx_rules)

        # Kiểm tra config nginx trước khi reload
        check = subprocess.run(["nginx", "-t"], capture_output=True, text=True)
        if check.returncode == 0:
            subprocess.run(["wo", "stack", "reload", "--nginx"], check=False)
            Log.info(self, f"Đã BẬT bảo trì thành công cho {domain}. Trạng thái HTTP 503 sẽ được trả về.")
        else:
            Log.error(self, f"Lỗi cấu hình Nginx. Đang tự động rollback...\n{check.stderr}")
            if os.path.exists(conf_path):
                os.remove(conf_path)


class WOSiteStartController(CementBaseController):
    class Meta:
        label = 'start'
        stacked_on = 'site'
        stacked_type = 'nested'
        description = 'Tắt chế độ bảo trì (Maintenance) cho trang web'
        arguments = [
            (['domain'], dict(help='Tên miền cần tắt bảo trì')),
        ]

    @expose(hide=True)
    def default(self):
        domain = self.app.pargs.domain
        if not domain:
            Log.error(self, "Lỗi: Vui lòng nhập tên miền.")
            return

        site_dir = f"/var/www/{domain}"
        if not os.path.exists(site_dir):
            Log.error(self, f"Lỗi: Site {domain} không tồn tại.")
            return

        Log.info(self, f"Đang tắt chế độ bảo trì cho {domain}...")

        html_path = f"{site_dir}/htdocs/mme-maintenance.html"
        conf_path = f"{site_dir}/conf/nginx/mme-maintenance.conf"

        if os.path.exists(html_path):
            os.remove(html_path)
        
        if os.path.exists(conf_path):
            os.remove(conf_path)

        subprocess.run(["wo", "stack", "reload", "--nginx"], check=False)
        Log.info(self, f"Đã TẮT bảo trì thành công cho {domain}. Website hoạt động bình thường.")


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

    @expose(help="Tự động cấp quyền 644 cho file, 755 cho thư mục và chown www-data:www-data cho thư mục hiện tại")
    def role(self):
        cwd = os.getcwd()
        Log.info(self, f"Đang cấp lại quyền cho toàn bộ file và thư mục tại: {cwd}")
        
        Log.info(self, "Đang đổi chủ sở hữu (chown -R www-data:www-data)...")
        subprocess.run(["chown", "-R", "www-data:www-data", cwd])
        
        Log.info(self, "Đang phân quyền thư mục (chmod 755)...")
        subprocess.run(["find", cwd, "-type", "d", "-exec", "chmod", "755", "{}", "+"])
        
        Log.info(self, "Đang phân quyền file (chmod 644)...")
        subprocess.run(["find", cwd, "-type", "f", "-exec", "chmod", "644", "{}", "+"])
        
        Log.info(self, "Hoàn tất cấp quyền!")

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
    app.handler.register(WOSitePauseController)
    app.handler.register(WOSiteStartController)
    app.handler.register(WOMMEBaseController)
    app.handler.register(WOMMEDeployController)
