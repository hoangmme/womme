import os
import subprocess
from cement.core.controller import CementBaseController, expose
from wo.core.logging import Log

class WOSiteCloneController(CementBaseController):
    class Meta:
        label = 'clone'
        stacked_on = 'site'
        stacked_type = 'nested'
        description = 'Nhân bản (Clone) một WordOps site hiện tại sang tên miền mới'
        arguments = [
            (['source_domain'],
             dict(help='Tên miền của site gốc cần clone')),
            (['dest_domain'],
             dict(help='Tên miền của site mới cần tạo')),
            (['--le'],
             dict(action='store_true', help='Tự động cài đặt SSL Let\'s Encrypt cho site mới')),
            (['--force'],
             dict(action='store_true', help='Bắt buộc tạo mới (nếu thư mục site đã tồn tại)')),
        ]

    @expose(hide=True)
    def default(self):
        source = self.app.pargs.source_domain
        dest = self.app.pargs.dest_domain
        le = self.app.pargs.le
        force = self.app.pargs.force

        Log.info(self, f"Bắt đầu quá trình clone từ {source} sang {dest}...")

        # 1. Kiểm tra site gốc
        if not os.path.exists(f"/var/www/{source}/htdocs"):
            Log.error(self, f"Lỗi: Site gốc {source} không tồn tại trong /var/www/")
            return

        # 2. Khởi tạo site mới
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

        # 3. Copy files
        Log.info(self, "Đang sao chép tệp tin từ site gốc sang site mới...")
        
        # Backup wp-config của site mới
        has_config = os.path.exists(f"/var/www/{dest}/htdocs/wp-config.php")
        if has_config:
            subprocess.run(f"cp /var/www/{dest}/htdocs/wp-config.php /tmp/wp-config-{dest}.php", shell=True)
        has_root_config = os.path.exists(f"/var/www/{dest}/wp-config.php")
        if has_root_config:
            subprocess.run(f"cp /var/www/{dest}/wp-config.php /tmp/wp-config-root-{dest}.php", shell=True)
            
        # Dọn dẹp thư mục mới
        subprocess.run(f"rm -rf /var/www/{dest}/htdocs/*", shell=True)
        
        # Copy mã nguồn nhưng loại trừ wp-config.php
        subprocess.run(f"rsync -a --exclude='wp-config.php' /var/www/{source}/htdocs/ /var/www/{dest}/htdocs/", shell=True)
        
        # Restore wp-config cho site mới
        if has_config:
            subprocess.run(f"mv /tmp/wp-config-{dest}.php /var/www/{dest}/htdocs/wp-config.php", shell=True)
        if has_root_config:
            subprocess.run(f"mv /tmp/wp-config-root-{dest}.php /var/www/{dest}/wp-config.php", shell=True)

        # 4. Export & Import Database
        Log.info(self, "Đang chuyển đổi cơ sở dữ liệu (Database)...")
        subprocess.run(f"wp db export /tmp/{source}.sql --path=/var/www/{source}/htdocs --allow-root", shell=True)
        subprocess.run(f"wp db import /tmp/{source}.sql --path=/var/www/{dest}/htdocs --allow-root", shell=True)
        if os.path.exists(f"/tmp/{source}.sql"):
            os.remove(f"/tmp/{source}.sql")

        # 5. Search & Replace URLs
        Log.info(self, "Đang cập nhật URL tên miền trong Database...")
        subprocess.run(f"wp search-replace '//{source}' '//{dest}' --all-tables --path=/var/www/{dest}/htdocs --allow-root", shell=True)
        subprocess.run(f"wp search-replace '{source}' '{dest}' --all-tables --path=/var/www/{dest}/htdocs --allow-root", shell=True)

        # 6. Set Permissions & Clear Cache
        Log.info(self, "Đang phân quyền thư mục và dọn dẹp cache...")
        subprocess.run(f"chown -R www-data:www-data /var/www/{dest}/htdocs", shell=True)
        subprocess.run("wo clean --all", shell=True)

        Log.info(self, f"Thành công! Site {source} đã được nhân bản hoàn chỉnh sang {dest}.")

def load(app):
    app.handler.register(WOSiteCloneController)
