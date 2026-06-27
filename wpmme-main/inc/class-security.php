<?php
if (!defined('ABSPATH')) {
    exit;
}

class WPMME_Security {
    private $options;

    public function __construct($options) {
        $this->options = $options;

        if (!empty($this->options['disable_xmlrpc'])) {
            $this->disable_xmlrpc();
        }
        if (!empty($this->options['remove_version'])) {
            $this->remove_version();
        }
        if (!empty($this->options['disable_rest_users'])) {
            $this->disable_rest_users();
        }
        if (!empty($this->options['disable_author'])) {
            $this->disable_author_archive();
        }
    }

    private function disable_xmlrpc() {
        add_filter('xmlrpc_enabled', '__return_false');
        add_filter('pings_open', '__return_false', 9999);
        
        add_filter('wp_headers', function ($headers) {
            unset($headers['X-Pingback']);
            return $headers;
        });

        add_action('init', function () {
            if (defined('XMLRPC_REQUEST') && XMLRPC_REQUEST) {
                wp_die('XML-RPC services are disabled on this site.', 'Forbidden', array('response' => 403));
            }
        });
    }

    private function remove_version() {
        remove_action('wp_head', 'wp_generator');
        add_filter('the_generator', '__return_empty_string');

        add_filter('style_loader_src', array($this, 'remove_version_from_url'), 9999);
        add_filter('script_loader_src', array($this, 'remove_version_from_url'), 9999);
    }

    public function remove_version_from_url($src) {
        if (strpos($src, 'ver=') !== false) {
            $src = remove_query_arg('ver', $src);
        }
        return $src;
    }

    private function disable_rest_users() {
        add_filter('rest_endpoints', function ($endpoints) {
            if (isset($endpoints['/wp/v2/users'])) {
                unset($endpoints['/wp/v2/users']);
            }
            if (isset($endpoints['/wp/v2/users/(?P<id>[\d]+)'])) {
                unset($endpoints['/wp/v2/users/(?P<id>[\d]+)']);
            }
            return $endpoints;
        });
    }

    private function disable_author_archive() {
        add_action('template_redirect', function () {
            if (is_author()) {
                wp_redirect(home_url(), 301);
                exit;
            }
        });

        add_action('init', function () {
            if (isset($_REQUEST['author']) && !is_admin()) {
                wp_redirect(home_url(), 301);
                exit;
            }
        });

        add_filter('oembed_response_data', function ($data) {
            if (isset($data['author_name'])) unset($data['author_name']);
            if (isset($data['author_url'])) unset($data['author_url']);
            return $data;
        });
    }
}
