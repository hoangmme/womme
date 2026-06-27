<?php
if (!defined('ABSPATH')) {
    exit;
}

class WPMME_Limit_Login {
    private $options;
    private $max_retries;
    private $lockout_duration = 20; // minutes
    private $max_lockouts = 4;
    private $long_lockout_duration = 24; // hours

    public function __construct() {
        $this->options = wpmme_get_options();
        $this->max_retries = intval($this->options['limit_login_retries']) > 0 ? intval($this->options['limit_login_retries']) : 4;
        
        add_filter('authenticate', array($this, 'check_login_attempt'), 30, 3);
        add_action('wp_login_failed', array($this, 'log_failed_login'));
        add_action('wp_login', array($this, 'clear_failed_login_log'));
        add_action('login_enqueue_scripts', array($this, 'hide_login_form_if_locked'));
    }

    private function get_client_ip() {
        $ip = '';
        if (isset($_SERVER['HTTP_CLIENT_IP'])) {
            $ip = $_SERVER['HTTP_CLIENT_IP'];
        } elseif (isset($_SERVER['HTTP_X_FORWARDED_FOR'])) {
            $ip = $_SERVER['HTTP_X_FORWARDED_FOR'];
        } elseif (isset($_SERVER['REMOTE_ADDR'])) {
            $ip = $_SERVER['REMOTE_ADDR'];
        }
        return sanitize_text_field(wp_unslash($ip));
    }

    private function get_transient_name() {
        return 'wpmme_lla_' . md5($this->get_client_ip());
    }

    public function log_failed_login($username) {
        $transient_name = $this->get_transient_name();
        $attempts = get_transient($transient_name) ?: array('retries' => 0, 'lockouts' => 0);
        
        $attempts['retries']++;

        if ($attempts['retries'] >= $this->max_retries) {
            $attempts['lockouts']++;
            $attempts['retries'] = 0; // Reset retries after a lockout
            $attempts['locked_until'] = time() + ($this->lockout_duration * 60);

            // Check for long lockout
            if ($attempts['lockouts'] >= $this->max_lockouts) {
                $attempts['locked_until'] = time() + ($this->long_lockout_duration * 3600);
            }
        }

        set_transient($transient_name, $attempts, 24 * 3600);
    }

    public function check_login_attempt($user, $username, $password) {
        $transient_name = $this->get_transient_name();
        $attempts = get_transient($transient_name);

        if ($attempts && isset($attempts['locked_until'])) {
            if (time() < $attempts['locked_until']) {
                $remaining = ceil(($attempts['locked_until'] - time()) / 60);
                return new WP_Error(
                    'locked_out', 
                    sprintf(__('Too many failed login attempts. Please try again in %d minutes.', 'wpmme'), $remaining)
                );
            } else {
                // Lockout expired
                delete_transient($transient_name);
            }
        }

        return $user;
    }

    public function clear_failed_login_log($user_login) {
        $transient_name = $this->get_transient_name();
        delete_transient($transient_name);
    }

    public function hide_login_form_if_locked() {
        $transient_name = $this->get_transient_name();
        $attempts = get_transient($transient_name);

        if ($attempts && isset($attempts['locked_until']) && time() < $attempts['locked_until']) {
            $remaining = ceil(($attempts['locked_until'] - time()) / 60);
            $msg = sprintf(__('Your IP has been temporarily blocked due to too many failed login attempts. Please try again in %d minutes.', 'wpmme'), $remaining);
            ?>
            <style>
                #loginform { display: none !important; }
            </style>
            <script>
                document.addEventListener('DOMContentLoaded', function() {
                    var msg = document.createElement('div');
                    msg.className = 'notice notice-error';
                    msg.innerHTML = '<p><strong>Error:</strong> <?php echo esc_js($msg); ?></p>';
                    var login = document.getElementById('login');
                    if(login) login.insertBefore(msg, login.firstChild);
                });
            </script>
            <?php
        }
    }
}
