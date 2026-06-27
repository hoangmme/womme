<?php
if (!defined('ABSPATH')) {
    exit;
}

class WPMME_Login {
    private $options;

    public function __construct($options) {
        $this->options = $options;

        if (!empty($this->options['login_logo'])) {
            $this->custom_login_logo();
        }

        if (!empty($this->options['login_slug']) && !empty($this->options['login_slug_value'])) {
            $this->custom_login_slug();
        }
    }

    private function custom_login_logo() {
        add_action('login_enqueue_scripts', array($this, 'enqueue_login_logo_css'));
        
        add_filter('login_headerurl', function () {
            return home_url();
        });

        add_filter('login_headertext', function () {
            return get_bloginfo('name');
        });
    }

    public function enqueue_login_logo_css() {
        $logo_url = !empty($this->options['login_logo_url']) ? $this->options['login_logo_url'] : 'https://mme.vn/wp-content/uploads/2026/06/Group-4.webp';
        
        if (empty($logo_url)) {
            return;
        }
        ?>
        <style type="text/css">
            #login h1 a, .login h1 a {
                background-image: url(<?php echo esc_url($logo_url); ?>) !important;
                background-size: contain !important;
                background-repeat: no-repeat !important;
                background-position: center center !important;
                width: 100% !important;
                height: 84px !important;
                margin-bottom: 20px !important;
            }
            body.login div#login h1 a:focus {
                box-shadow: none;
            }
        </style>
        <?php
    }

    private function custom_login_slug() {
        $slug = sanitize_title($this->options['login_slug_value']);

        // 1. Intercept the custom slug and load wp-login.php directly (No rewrite rules needed)
        add_action('init', function () use ($slug) {
            $request_path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
            $request_path = trim(str_replace(home_url('', 'relative'), '', $request_path), '/');

            if ($request_path === $slug) {
                global $pagenow;
                $pagenow = 'wp-login.php';
                $_SERVER['REQUEST_URI'] = str_replace('/' . $slug, '/wp-login.php', $_SERVER['REQUEST_URI']);
                
                // Define a constant so we know it's a legit request
                define('WPMME_LEGIT_LOGIN', true);
                
                require_once ABSPATH . 'wp-login.php';
                exit;
            }
        }, 1);

        // 2. Block direct wp-login.php access and prevent /wp-admin/ from leaking the slug
        add_action('init', function () {
            $request_path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
            $is_wp_login = (strpos($request_path, 'wp-login.php') !== false);

            if ($is_wp_login && !defined('WPMME_LEGIT_LOGIN') && !is_admin()) {
                // Allow POST requests (form submissions to wp-login.php are standard)
                if ($_SERVER['REQUEST_METHOD'] === 'POST') return;

                // Allow specific actions (logout, resetpass)
                $action = isset($_GET['action']) ? $_GET['action'] : '';
                if (in_array($action, array('logout', 'resetpass', 'rp', 'confirmaction', 'postpass'))) {
                    return;
                }
                if (isset($_GET['interim-login'])) return;

                // Block access - return 404
                global $wp_query;
                if (!isset($wp_query)) $wp_query = new WP_Query();
                $wp_query->set_404();
                status_header(404);
                nocache_headers();
                include(get_query_template('404'));
                exit;
            }

            // Prevent /wp-admin/ from redirecting and revealing the secret slug for unauthenticated users
            if (is_admin() && !is_user_logged_in() && !defined('DOING_AJAX')) {
                if (strpos($request_path, 'admin-post.php') !== false || strpos($request_path, 'load-styles.php') !== false || strpos($request_path, 'load-scripts.php') !== false) {
                    return;
                }

                global $wp_query;
                if (!isset($wp_query)) $wp_query = new WP_Query();
                $wp_query->set_404();
                status_header(404);
                nocache_headers();
                include(get_query_template('404'));
                exit;
            }
        });

        // 3. Filter URLs to use the custom slug
        add_filter('login_url', function ($login_url, $redirect, $force_reauth) use ($slug) {
            $login_url = home_url('/' . $slug . '/');
            if (!empty($redirect)) {
                $login_url = add_query_arg('redirect_to', urlencode($redirect), $login_url);
            }
            if ($force_reauth) {
                $login_url = add_query_arg('reauth', '1', $login_url);
            }
            return $login_url;
        }, 10, 3);

        add_filter('logout_url', function ($logout_url, $redirect) use ($slug) {
            $url = add_query_arg(array(
                'action'   => 'logout',
                '_wpnonce' => wp_create_nonce('log-out'),
            ), home_url('/' . $slug . '/'));
            
            if (!empty($redirect)) {
                $url = add_query_arg('redirect_to', urlencode($redirect), $url);
            }
            return $url;
        }, 10, 2);

        add_filter('register_url', function($register_url) use ($slug) {
            return home_url('/' . $slug . '/?action=register');
        });

        add_filter('lostpassword_url', function($lostpassword_url) use ($slug) {
            return home_url('/' . $slug . '/?action=lostpassword');
        });

        add_filter('site_url', function ($url, $path, $scheme) use ($slug) {
            if ($scheme === 'login' || $scheme === 'login_post') {
                return str_replace('wp-login.php', $slug, $url);
            }
            return $url;
        }, 10, 3);
        
        add_filter('wp_redirect', function($location, $status) use ($slug) {
            if (strpos($location, 'wp-login.php') !== false) {
                $location = str_replace('wp-login.php', $slug, $location);
            }
            return $location;
        }, 10, 2);
    }
}
