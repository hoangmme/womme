<?php
if (!defined('ABSPATH')) {
    exit;
}

class WPMME_Deploy {
    public function __construct() {
        add_action('rest_api_init', array($this, 'register_endpoints'));
    }

    public function register_endpoints() {
        register_rest_route('wpmme/v1', '/deploy', array(
            'methods' => 'POST',
            'callback' => array($this, 'handle_deploy_webhook'),
            'permission_callback' => '__return_true', // Cho phép GitHub gọi không cần auth (tạm thời để public, Github tự gửi payload)
        ));
    }

    public function handle_deploy_webhook(WP_REST_Request $request) {
        // Lấy domain hiện tại để báo cho Python Daemon biết site nào đang cần deploy
        $domain = $_SERVER['HTTP_HOST'] ?? '';
        
        // Loại bỏ www. nếu có
        $domain = preg_replace('/^www\./', '', $domain);

        if (empty($domain)) {
            return new WP_Error('missing_domain', 'Không thể xác định tên miền.', array('status' => 400));
        }

        // Tạo request nội bộ (local request) gọi tới cổng 8989 của womme-daemon.py
        $daemon_url = "http://127.0.0.1:8989/hooks/" . urlencode($domain);

        $args = array(
            'method'      => 'POST',
            'timeout'     => 5, // Timeout ngắn vì ta chỉ cần kích hoạt, không cần đợi deploy xong
            'redirection' => 5,
            'httpversion' => '1.0',
            'blocking'    => false, // Non-blocking: Kích hoạt xong trả về ngay cho Github đỡ báo lỗi Timeout
            'headers'     => array(),
            'body'        => array(),
            'cookies'     => array()
        );

        wp_remote_post($daemon_url, $args);

        return rest_ensure_response(array(
            'success' => true,
            'message' => 'Đã gửi lệnh kích hoạt Deploy cho domain: ' . $domain,
            'daemon_url' => $daemon_url
        ));
    }
}
