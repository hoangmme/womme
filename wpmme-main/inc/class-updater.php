<?php
if (!defined('ABSPATH')) {
    exit;
}

class WPMME_Updater {
    public function __construct() {
        add_action('wp_ajax_wpmme_force_update', array($this, 'handle_force_update'));
    }

    public function handle_force_update() {
        check_ajax_referer('wpmme_nonce', 'nonce');

        if (!current_user_can('manage_options')) {
            wp_send_json_error('Permission denied.');
        }

        require_once ABSPATH . 'wp-admin/includes/file.php';
        require_once ABSPATH . 'wp-admin/includes/misc.php';
        require_once ABSPATH . 'wp-admin/includes/class-wp-upgrader.php';

        WP_Filesystem();
        global $wp_filesystem;

        $zip_url = 'https://github.com/hoangmme/wpmme/archive/refs/heads/main.zip';
        $temp_file = download_url($zip_url);

        if (is_wp_error($temp_file)) {
            wp_send_json_error('Failed to download from GitHub: ' . $temp_file->get_error_message());
        }

        $temp_dir = get_temp_dir() . 'wpmme_update_' . time() . '/';
        $wp_filesystem->mkdir($temp_dir);

        $unzip_result = unzip_file($temp_file, $temp_dir);
        unlink($temp_file);

        if (is_wp_error($unzip_result)) {
            $wp_filesystem->delete($temp_dir, true);
            wp_send_json_error('Failed to unzip the file: ' . $unzip_result->get_error_message());
        }

        // GitHub zips contain a root folder, usually "repo-branch" e.g., "wpmme-main"
        $source_dir = $temp_dir . 'wpmme-main/';
        if (!file_exists($source_dir)) {
            // Find the first directory inside temp_dir if "wpmme-main" is not there
            $files = scandir($temp_dir);
            foreach ($files as $file) {
                if ($file != '.' && $file != '..' && is_dir($temp_dir . $file)) {
                    $source_dir = $temp_dir . $file . '/';
                    break;
                }
            }
        }

        if (!file_exists($source_dir)) {
            $wp_filesystem->delete($temp_dir, true);
            wp_send_json_error('Could not locate the plugin files inside the extracted zip.');
        }

        // Copy files over
        $plugin_dir = WPMME_DIR;
        $copy_result = copy_dir($source_dir, $plugin_dir);

        // Clean up
        $wp_filesystem->delete($temp_dir, true);

        if (is_wp_error($copy_result)) {
            wp_send_json_error('Failed to copy files: ' . $copy_result->get_error_message());
        } elseif ($copy_result === false) {
            wp_send_json_error('Failed to copy files due to file system permissions.');
        }

        wp_send_json_success();
    }
}
