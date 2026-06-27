<?php
if (!defined('ABSPATH')) {
    exit;
}

class WPMME_Admin_Bar {
    public function __construct() {
        add_action('admin_bar_menu', array($this, 'clean_admin_bar'), 999);
        add_action('admin_head', array($this, 'hide_help_tabs'));
    }

    public function clean_admin_bar($wp_admin_bar) {
        // Remove WordPress Logo
        $wp_admin_bar->remove_node('wp-logo');

        // Remove Updates
        $wp_admin_bar->remove_node('updates');

        // Remove Comments
        $wp_admin_bar->remove_node('comments');

        // Remove New Content
        $wp_admin_bar->remove_node('new-content');

        // Remove Customize
        $wp_admin_bar->remove_node('customize');

        // Remove Howdy
        $my_account = $wp_admin_bar->get_node('my-account');
        if ($my_account) {
            $title = str_replace('Howdy, ', '', $my_account->title);
            $title = str_replace('Chào, ', '', $title); // Handle Vietnamese
            $wp_admin_bar->add_node(array(
                'id' => 'my-account',
                'title' => $title,
            ));
        }
    }

    public function hide_help_tabs() {
        $screen = get_current_screen();
        if ($screen) {
            $screen->remove_help_tabs();
        }
    }
}
