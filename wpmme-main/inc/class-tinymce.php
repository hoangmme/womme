<?php
if (!defined('ABSPATH')) {
    exit;
}

class WPMME_TinyMCE {
    public function __construct() {
        add_filter('mce_buttons', array($this, 'add_buttons_row_1'));
        add_filter('mce_buttons_2', array($this, 'add_buttons_row_2'));
        add_filter('mce_external_plugins', array($this, 'register_plugins'));
        add_filter('tiny_mce_before_init', array($this, 'custom_settings'));
    }

    public function add_buttons_row_1($buttons) {
        $new_buttons = array('fontsizeselect', 'forecolor', 'backcolor');
        return array_merge($buttons, $new_buttons);
    }

    public function add_buttons_row_2($buttons) {
        $new_buttons = array('table', 'anchor');
        return array_merge($buttons, $new_buttons);
    }

    public function register_plugins($plugins) {
        // Table plugin
        if (file_exists(WPMME_DIR . 'assets/js/tinymce/table/plugin.min.js')) {
            $plugins['table'] = WPMME_URL . 'assets/js/tinymce/table/plugin.min.js';
        }
        
        // Anchor plugin
        if (file_exists(WPMME_DIR . 'assets/js/tinymce/anchor/plugin.min.js')) {
            $plugins['anchor'] = WPMME_URL . 'assets/js/tinymce/anchor/plugin.min.js';
        }

        return $plugins;
    }

    public function custom_settings($settings) {
        $settings['fontsize_formats'] = '8px 10px 12px 14px 16px 18px 20px 24px 28px 32px 36px 48px 64px 72px 96px';
        $settings['block_formats'] = 'Paragraph=p;Heading 1=h1;Heading 2=h2;Heading 3=h3;Heading 4=h4;Heading 5=h5;Heading 6=h6;Preformatted=pre;Code=code';
        return $settings;
    }
}
