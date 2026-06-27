<?php
if (!defined('ABSPATH')) {
    exit;
}

class WPMME_Auto_Upload {
    public function __construct() {
        add_action('save_post', array($this, 'process_post'), 10, 2);
    }

    public function process_post($post_id, $post) {
        if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) return;
        if (wp_is_post_revision($post_id)) return;
        if ($post->post_type === 'revision') return;

        $content = $post->post_content;
        if (empty($content)) return;

        // Find all images in content
        preg_match_all('/<img[^>]+src=["\']([^"\']+)["\'][^>]*>/i', $content, $matches);
        if (empty($matches[1])) return;

        $site_url = parse_url(home_url(), PHP_URL_HOST);
        $updated = false;

        foreach ($matches[1] as $index => $url) {
            // Skip if already local or data URI
            if (strpos($url, $site_url) !== false) continue;
            if (strpos($url, 'data:image') === 0) continue;

            $response = wp_remote_get($url, array(
                'timeout'   => 30,
                'sslverify' => false,
            ));

            if (is_wp_error($response)) continue;
            if (wp_remote_retrieve_response_code($response) !== 200) continue;

            $image_data = wp_remote_retrieve_body($response);
            if (empty($image_data)) continue;

            $content_type = wp_remote_retrieve_header($response, 'content-type');
            $ext = $this->get_extension($content_type, $url);
            if (!$ext) continue;

            $filename = sanitize_file_name(
                pathinfo(parse_url($url, PHP_URL_PATH), PATHINFO_FILENAME) . '.' . $ext
            );

            // Deduplicate filename
            $upload_dir = wp_upload_dir();
            $filename = wp_unique_filename($upload_dir['path'], $filename);

            $upload = wp_upload_bits($filename, null, $image_data);
            if (!empty($upload['error'])) continue;

            $attachment = array(
                'post_mime_type' => $content_type ?: mime_content_type($upload['file']),
                'post_title'     => pathinfo($filename, PATHINFO_FILENAME),
                'post_content'   => '',
                'post_status'    => 'inherit',
            );

            $attach_id = wp_insert_attachment($attachment, $upload['file'], $post_id);
            if (is_wp_error($attach_id)) continue;

            require_once(ABSPATH . 'wp-admin/includes/image.php');
            $metadata = wp_generate_attachment_metadata($attach_id, $upload['file']);
            wp_update_attachment_metadata($attach_id, $metadata);

            $content = str_replace(
                $matches[0][$index], 
                str_replace($url, $upload['url'], $matches[0][$index]),
                $content
            );
            $updated = true;
        }

        if ($updated) {
            remove_action('save_post', array($this, 'process_post'));
            wp_update_post(array(
                'ID'           => $post_id,
                'post_content' => $content,
            ));
            add_action('save_post', array($this, 'process_post'), 10, 2);
        }
    }

    private function get_extension($content_type, $url) {
        $map = array(
            'image/jpeg'    => 'jpg',
            'image/png'     => 'png',
            'image/gif'     => 'gif',
            'image/webp'    => 'webp',
            'image/svg+xml' => 'svg',
            'image/bmp'     => 'bmp',
        );

        if ($content_type && isset($map[$content_type])) {
            return $map[$content_type];
        }

        $ext = strtolower(pathinfo(parse_url($url, PHP_URL_PATH), PATHINFO_EXTENSION));
        if (in_array($ext, array('jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp'))) {
            return $ext;
        }

        return null;
    }
}
