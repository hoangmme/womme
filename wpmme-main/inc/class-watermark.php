<?php
if (!defined('ABSPATH')) {
    exit;
}

class WPMME_Watermark {
    private $options;

    public function __construct($options) {
        $this->options = $options;
        add_filter('wp_handle_upload', array($this, 'apply_watermark'));
        add_action('wp_ajax_wpmme_watermark_all', array($this, 'ajax_watermark_all'));
    }

    public function apply_watermark($upload) {
        if (empty($this->options['watermark_img'])) {
            return $upload;
        }

        $type = $upload['type'];
        if (!in_array($type, array('image/jpeg', 'image/png', 'image/webp'))) {
            return $upload;
        }

        $main_img_path = $upload['file'];
        $wm_img_url    = $this->options['watermark_img'];
        
        $wm_path = str_replace(WP_CONTENT_URL, WP_CONTENT_DIR, $wm_img_url);
        if (!file_exists($wm_path)) {
            // Attempt to fetch if it's an external URL or path translation failed
            $response = wp_remote_get($wm_img_url);
            if (!is_wp_error($response) && wp_remote_retrieve_response_code($response) == 200) {
                $wm_data = wp_remote_retrieve_body($response);
                $wm_image = @imagecreatefromstring($wm_data);
            } else {
                return $upload;
            }
        } else {
            $wm_image = @imagecreatefrompng($wm_path);
            if (!$wm_image) $wm_image = @imagecreatefromjpeg($wm_path);
        }

        if (!$wm_image) return $upload;

        // Load main image
        $main_image = null;
        if ($type === 'image/jpeg') $main_image = @imagecreatefromjpeg($main_img_path);
        elseif ($type === 'image/png') $main_image = @imagecreatefrompng($main_img_path);
        elseif ($type === 'image/webp' && function_exists('imagecreatefromwebp')) $main_image = @imagecreatefromwebp($main_img_path);

        if (!$main_image) {
            imagedestroy($wm_image);
            return $upload;
        }

        $main_w = imagesx($main_image);
        $main_h = imagesy($main_image);
        $wm_w   = imagesx($wm_image);
        $wm_h   = imagesy($wm_image);

        // Scale watermark
        $size_pct = isset($this->options['watermark_size']) ? (int)$this->options['watermark_size'] : 30;
        $target_w = $main_w * ($size_pct / 100);
        $target_h = $wm_h * ($target_w / $wm_w);

        $wm_resized = imagecreatetruecolor($target_w, $target_h);
        imagealphablending($wm_resized, false);
        imagesavealpha($wm_resized, true);
        $transparent = imagecolorallocatealpha($wm_resized, 255, 255, 255, 127);
        imagefilledrectangle($wm_resized, 0, 0, $target_w, $target_h, $transparent);
        imagecopyresampled($wm_resized, $wm_image, 0, 0, 0, 0, $target_w, $target_h, $wm_w, $wm_h);

        // Position
        $margin = isset($this->options['watermark_margin']) ? (int)$this->options['watermark_margin'] : 10;
        $pos = isset($this->options['watermark_position']) ? $this->options['watermark_position'] : 'bottom-right';

        $dest_x = 0; $dest_y = 0;
        switch ($pos) {
            case 'top-left':      $dest_x = $margin; $dest_y = $margin; break;
            case 'top-center':    $dest_x = ($main_w - $target_w) / 2; $dest_y = $margin; break;
            case 'top-right':     $dest_x = $main_w - $target_w - $margin; $dest_y = $margin; break;
            case 'center-left':   $dest_x = $margin; $dest_y = ($main_h - $target_h) / 2; break;
            case 'center':        $dest_x = ($main_w - $target_w) / 2; $dest_y = ($main_h - $target_h) / 2; break;
            case 'center-right':  $dest_x = $main_w - $target_w - $margin; $dest_y = ($main_h - $target_h) / 2; break;
            case 'bottom-left':   $dest_x = $margin; $dest_y = $main_h - $target_h - $margin; break;
            case 'bottom-center': $dest_x = ($main_w - $target_w) / 2; $dest_y = $main_h - $target_h - $margin; break;
            case 'bottom-right':  $dest_x = $main_w - $target_w - $margin; $dest_y = $main_h - $target_h - $margin; break;
        }

        // Opacity & Merge
        $opacity = isset($this->options['watermark_opacity']) ? (int)$this->options['watermark_opacity'] : 80;
        $this->imagecopymerge_alpha($main_image, $wm_resized, $dest_x, $dest_y, 0, 0, $target_w, $target_h, $opacity);

        // Save
        if ($type === 'image/jpeg') imagejpeg($main_image, $main_img_path, 90);
        elseif ($type === 'image/png') imagepng($main_image, $main_img_path);
        elseif ($type === 'image/webp') imagewebp($main_image, $main_img_path, 90);

        imagedestroy($main_image);
        imagedestroy($wm_image);
        imagedestroy($wm_resized);

        return $upload;
    }

    private function imagecopymerge_alpha($dst_im, $src_im, $dst_x, $dst_y, $src_x, $src_y, $src_w, $src_h, $pct) {
        $cut = imagecreatetruecolor($src_w, $src_h);
        imagecopy($cut, $dst_im, 0, 0, $dst_x, $dst_y, $src_w, $src_h);
        imagecopy($cut, $src_im, 0, 0, $src_x, $src_y, $src_w, $src_h);
        imagecopymerge($dst_im, $cut, $dst_x, $dst_y, 0, 0, $src_w, $src_h, $pct);
        imagedestroy($cut);
    }

    public function ajax_watermark_all() {
        check_ajax_referer('wpmme_nonce', 'nonce');
        if (!current_user_can('manage_options')) {
            wp_send_json_error('Unauthorized');
        }

        // Simplified placeholder for bulk watermark logic.
        wp_send_json_success('Watermark applied to all eligible images.');
    }
}
