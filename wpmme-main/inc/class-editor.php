<?php
if (!defined('ABSPATH')) {
    exit;
}

class WPMME_Editor {
    public function __construct() {
        // Force classic editor
        add_filter('use_block_editor_for_post', '__return_false');
        add_filter('use_block_editor_for_post_type', '__return_false');

        // Remove Gutenberg styles
        add_action('wp_enqueue_scripts', array($this, 'remove_block_styles'), 100);

        // Add editor styles
        add_filter('mce_css', array($this, 'add_editor_style'));

        // Add body class to editor
        add_filter('tiny_mce_before_init', array($this, 'add_body_class'));
    }

    public function remove_block_styles() {
        wp_dequeue_style('wp-block-library');
        wp_dequeue_style('wp-block-library-theme');
        wp_dequeue_style('wc-blocks-style');
        wp_dequeue_style('global-styles');
    }

    public function add_editor_style($mce_css) {
        if (!empty($mce_css)) {
            $mce_css .= ',';
        }
        $mce_css .= WPMME_URL . 'assets/css/editor-style.css';
        return $mce_css;
    }

    public function add_body_class($settings) {
        $settings['body_class'] = 'wpmme-editor';
        return $settings;
    }
}
