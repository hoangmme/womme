<?php
if (!defined('ABSPATH')) {
    exit;
}

class WPMME_Comments {
    public function __construct() {
        // Close comments on the front-end
        add_filter('comments_open', '__return_false', 20, 2);
        add_filter('pings_open', '__return_false', 20, 2);

        // Hide existing comments
        add_filter('comments_array', '__return_empty_array', 10, 2);

        // Remove comments page in menu
        add_action('admin_menu', array($this, 'remove_comments_menu'));

        // Remove comments links from admin bar
        add_action('init', array($this, 'remove_admin_bar_comments'));

        // Redirect any user trying to access comments page
        add_action('admin_init', array($this, 'redirect_comments_page'));

        // Remove comments metabox from dashboard
        add_action('admin_init', array($this, 'remove_dashboard_comments_metabox'));

        // Remove comments from admin bar render
        add_action('wp_before_admin_bar_render', array($this, 'remove_admin_bar_comments_render'));

        // Disable support for comments and trackbacks in post types
        add_action('admin_init', array($this, 'remove_post_types_support'));

        // Close comments on front-end via wp_count_comments override
        add_filter('wp_count_comments', array($this, 'override_comment_count'));
    }

    public function remove_comments_menu() {
        remove_menu_page('edit-comments.php');
    }

    public function remove_admin_bar_comments() {
        if (is_admin_bar_showing()) {
            remove_action('admin_bar_menu', 'wp_admin_bar_comments_menu', 60);
        }
    }

    public function redirect_comments_page() {
        global $pagenow;
        if ($pagenow === 'edit-comments.php') {
            wp_redirect(admin_url());
            exit;
        }
    }

    public function remove_dashboard_comments_metabox() {
        remove_meta_box('dashboard_recent_comments', 'dashboard', 'normal');
    }

    public function remove_admin_bar_comments_render() {
        global $wp_admin_bar;
        if (isset($wp_admin_bar)) {
            $wp_admin_bar->remove_menu('comments');
        }
    }

    public function remove_post_types_support() {
        $post_types = get_post_types();
        foreach ($post_types as $post_type) {
            if (post_type_supports($post_type, 'comments')) {
                remove_post_type_support($post_type, 'comments');
                remove_post_type_support($post_type, 'trackbacks');
            }
        }
    }

    public function override_comment_count($count) {
        return (object) array(
            'approved'       => 0,
            'moderated'      => 0,
            'spam'           => 0,
            'trash'          => 0,
            'post-trashed'   => 0,
            'total_comments' => 0,
            'all'            => 0,
        );
    }
}
