<?php
if (!defined('ABSPATH')) {
    exit;
}

class WPMME_Settings {
    public function __construct() {
        add_action('wp_ajax_wpmme_save_settings', array($this, 'save_settings'));
        add_action('wp_ajax_wpmme_reset_settings', array($this, 'reset_settings'));
    }

    public function save_settings() {
        check_ajax_referer('wpmme_nonce', 'nonce');

        if (!current_user_can('manage_options')) {
            wp_send_json_error('Unauthorized');
        }

        $options = wpmme_get_options();

        $checkbox_fields = array(
            'classic_editor', 'tinymce_plugins', 'image_seo', 'auto_upload',
            'imgattr', 'rename', 'webp', 'watermark', 'disable_xmlrpc',
            'remove_version', 'disable_rest_users', 'disable_author',
            'disable_comments', 'login_logo', 'login_slug',
            'media_replace', 'admin_bar_clean', 'limit_login'
        );

        foreach ($checkbox_fields as $field) {
            $options[$field] = isset($_POST[$field]) ? true : false;
        }

        if (isset($_POST['rename_pattern'])) {
            $options['rename_pattern'] = sanitize_text_field($_POST['rename_pattern']);
        }
        if (isset($_POST['webp_quality'])) {
            $options['webp_quality'] = absint($_POST['webp_quality']);
        }
        if (isset($_POST['watermark_img'])) {
            $options['watermark_img'] = esc_url_raw($_POST['watermark_img']);
        }
        if (isset($_POST['watermark_position'])) {
            $options['watermark_position'] = sanitize_text_field($_POST['watermark_position']);
        }
        if (isset($_POST['watermark_size'])) {
            $options['watermark_size'] = absint($_POST['watermark_size']);
        }
        if (isset($_POST['watermark_margin'])) {
            $options['watermark_margin'] = absint($_POST['watermark_margin']);
        }
        if (isset($_POST['watermark_opacity'])) {
            $options['watermark_opacity'] = absint($_POST['watermark_opacity']);
        }
        if (isset($_POST['login_logo_url'])) {
            $options['login_logo_url'] = esc_url_raw($_POST['login_logo_url']);
        }
        if (isset($_POST['login_slug_value'])) {
            $options['login_slug_value'] = sanitize_title($_POST['login_slug_value']);
        }
        if (isset($_POST['limit_login_retries'])) {
            $options['limit_login_retries'] = absint($_POST['limit_login_retries']);
        }

        update_option('wpmme_options', $options);

        wp_send_json_success('Settings saved successfully.');
    }

    public function reset_settings() {
        check_ajax_referer('wpmme_nonce', 'nonce');

        if (!current_user_can('manage_options')) {
            wp_send_json_error('Unauthorized');
        }

        $defaults = wpmme_get_default_options();
        update_option('wpmme_options', $defaults);

        wp_send_json_success('Settings reset to defaults.');
    }
}

new WPMME_Settings();
