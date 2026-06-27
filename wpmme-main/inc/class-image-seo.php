<?php
if (!defined('ABSPATH')) {
    exit;
}

class WPMME_Image_SEO {
    public function __construct() {
        add_action('add_attachment', array($this, 'set_alt_text'));
        add_filter('wp_insert_attachment_data', array($this, 'set_title'), 10, 2);
    }

    public function set_alt_text($attachment_id) {
        if (!wp_attachment_is_image($attachment_id)) {
            return;
        }

        $alt = get_post_meta($attachment_id, '_wp_attachment_image_alt', true);
        if (empty($alt)) {
            $filename = pathinfo(get_attached_file($attachment_id), PATHINFO_FILENAME);
            $alt_text = $this->clean_filename($filename);
            update_post_meta($attachment_id, '_wp_attachment_image_alt', $alt_text);
        }
    }

    public function set_title($data, $postarr) {
        if (isset($data['post_type']) && $data['post_type'] !== 'attachment') {
            return $data;
        }

        if (empty($data['post_title']) || (isset($data['post_name']) && $data['post_title'] === $data['post_name'])) {
            $filename = '';
            if (isset($postarr['file'])) {
                $filename = pathinfo($postarr['file'], PATHINFO_FILENAME);
            } elseif (isset($data['guid'])) {
                $filename = pathinfo($data['guid'], PATHINFO_FILENAME);
            }

            if (!empty($filename)) {
                $cleaned = $this->clean_filename($filename);
                $data['post_title']   = $cleaned;
                $data['post_content'] = $cleaned; // Description
                $data['post_excerpt'] = $cleaned; // Caption
            }
        }
        return $data;
    }

    private function clean_filename($filename) {
        // Replace hyphens and underscores with spaces
        $clean = preg_replace('/[-_]+/', ' ', $filename);
        // Remove sequences of 10 or more digits (like timestamps)
        $clean = preg_replace('/\d{10,}/', '', $clean);
        // Capitalize first letter of each word and trim
        return ucwords(strtolower(trim($clean)));
    }
}
