<?php
/**
 * Plugin Name: MMe Core
 * Plugin URI: https://mme.vn
 * Description: All-in-One Optimization & Security plugin by MMe.
 * Version: 1.0.0 (Build 20260628.1505)
 * Author: Hoji
 * Author URI: https://mme.vn
 * Text Domain: wpmme
 * Requires at least: 5.0
 * Requires PHP: 7.2
 */

if (!defined('ABSPATH')) {
    exit;
}

define('WPMME_VERSION', '1.0.0');
define('WPMME_BUILD', '20260630.0235');
define('WPMME_DIR', plugin_dir_path(__FILE__));
define('WPMME_URL', plugin_dir_url(__FILE__));

// Load Feature Classes
require_once WPMME_DIR . 'inc/class-settings.php';
require_once WPMME_DIR . 'inc/class-editor.php';
require_once WPMME_DIR . 'inc/class-tinymce.php';
require_once WPMME_DIR . 'inc/class-image-seo.php';
require_once WPMME_DIR . 'inc/class-security.php';
require_once WPMME_DIR . 'inc/class-auto-upload.php';
require_once WPMME_DIR . 'inc/class-imgattr.php';
require_once WPMME_DIR . 'inc/class-rename.php';
require_once WPMME_DIR . 'inc/class-webp.php';
require_once WPMME_DIR . 'inc/class-watermark.php';
require_once WPMME_DIR . 'inc/class-comments.php';
require_once WPMME_DIR . 'inc/class-login.php';
require_once WPMME_DIR . 'inc/class-admin-bar.php';
require_once WPMME_DIR . 'inc/class-admin-notices.php';
require_once WPMME_DIR . 'inc/class-limit-login.php';
require_once WPMME_DIR . 'inc/class-media-replace.php';
require_once WPMME_DIR . 'inc/class-media-tabs.php';
require_once WPMME_DIR . 'inc/class-updater.php';
require_once WPMME_DIR . 'inc/class-deploy.php';
require_once WPMME_DIR . 'inc/class-cli.php';

// Initialize Plugin
function wpmme_init() {
    $options = wpmme_get_options();

    if (!empty($options['classic_editor'])) {
        new WPMME_Editor();
    }
    if (!empty($options['tinymce_plugins'])) {
        new WPMME_TinyMCE();
    }
    if (!empty($options['image_seo'])) {
        new WPMME_Image_SEO();
    }

    // Security & Logic Features
    new WPMME_Security($options);

    if (!empty($options['auto_upload'])) {
        new WPMME_Auto_Upload();
    }
    if (!empty($options['imgattr'])) {
        new WPMME_ImgAttr();
    }
    if (!empty($options['rename'])) {
        new WPMME_Rename($options);
    }
    if (!empty($options['webp'])) {
        new WPMME_WebP($options);
    }
    if (!empty($options['watermark'])) {
        new WPMME_Watermark($options);
    }
    if (!empty($options['disable_comments'])) {
        new WPMME_Comments();
    }

    // Login customization
    new WPMME_Login($options);

    // ASE Enhancements
    if (!empty($options['admin_bar_clean'])) {
        new WPMME_Admin_Bar();
    }
    
    if (!empty($options['hide_notices'])) {
        new WPMME_Admin_Notices();
    }
    if (!empty($options['limit_login'])) {
        new WPMME_Limit_Login();
    }
    if (!empty($options['media_replace'])) {
        new WPMME_Media_Replace();
    }
    
    if (!empty($options['media_tabs'])) {
        new WPMME_Media_Tabs();
    }
    
    new WPMME_Updater();
    new WPMME_Deploy();
}
add_action('plugins_loaded', 'wpmme_init');

// Activation Hook
register_activation_hook(__FILE__, 'wpmme_activate');
function wpmme_activate() {
    $options = get_option('wpmme_options');
    if (!$options) {
        $defaults = wpmme_get_default_options();
        update_option('wpmme_options', $defaults);
    }
}

// Deactivation Hook
register_deactivation_hook(__FILE__, 'wpmme_deactivate');
function wpmme_deactivate() {
    // Optional cleanup
}

// Helper function to get options with defaults
function wpmme_get_options() {
    $defaults = wpmme_get_default_options();
    $options = get_option('wpmme_options', array());
    return wp_parse_args($options, $defaults);
}

function wpmme_get_default_options() {
    return array(
        'classic_editor'       => true,
        'tinymce_plugins'      => true,
        'image_seo'            => false,
        'auto_upload'          => true,
        'imgattr'              => true,
        'rename'               => true,
        'rename_pattern'       => '{domain}-{date}-{random}',
        'webp'                 => true,
        'webp_quality'         => 82,
        'watermark'            => false,
        'watermark_img'        => '',
        'watermark_position'   => 'bottom-right',
        'watermark_size'       => 30,
        'watermark_margin'     => 10,
        'watermark_opacity'    => 80,
        
        // Media Tabs
        'media_tabs'           => true,

        // Security
        'disable_xmlrpc'       => true,
        'limit_login_retries'  => 4,     
        'remove_version'       => true,
        'disable_rest_users'   => true,
        'disable_author'       => true,
        'disable_comments'     => true,
        'login_logo'           => true,
        'login_logo_url'       => 'https://mme.vn/wp-content/uploads/2026/06/Group-4.webp',
        'login_slug'           => true,
        'login_slug_value'     => 'zogin',
        'media_replace'        => true,
        'admin_bar_clean'      => true,
        'hide_notices'         => true,
        'limit_login'          => true,
        'limit_login_retries'  => 4,
    );
}

// Admin Menu
add_action('admin_menu', 'wpmme_admin_menu');
function wpmme_admin_menu() {
    add_menu_page(
        'MMe Core Settings',
        'MMe Core',
        'manage_options',
        'wpmme-settings',
        'wpmme_settings_page',
        'dashicons-admin-generic',
        80
    );
}

function wpmme_settings_page() {
    require_once WPMME_DIR . 'page/settings.php';
}

// Admin Enqueue
add_action('admin_enqueue_scripts', 'wpmme_admin_assets');
function wpmme_admin_assets($hook) {
    if ($hook !== 'toplevel_page_wpmme-settings') {
        return;
    }

    wp_enqueue_media();
    wp_enqueue_style('wpmme-admin-css', WPMME_URL . 'assets/css/admin.css', array(), WPMME_VERSION);
    wp_enqueue_script('wpmme-admin-js', WPMME_URL . 'assets/js/admin.js', array('jquery'), WPMME_VERSION, true);

    wp_localize_script('wpmme-admin-js', 'wpmme_ajax', array(
        'url'   => admin_url('admin-ajax.php'),
        'nonce' => wp_create_nonce('wpmme_nonce')
    ));

    // Polyfill for ACF / SCF to prevent JS errors on our custom page
    wp_add_inline_script('wpmme-admin-js', 'window.acf = window.acf || {}; window.acf.add_filter = window.acf.add_filter || function() {}; window.acf.add_action = window.acf.add_action || function() {};', 'before');

    // Dequeue known conflicting plugin scripts on our page
    wp_dequeue_script('acf-input');
    wp_dequeue_script('acf-pro-input');
    wp_dequeue_script('scf-admin');
    wp_dequeue_script('smart-custom-fields');
}
