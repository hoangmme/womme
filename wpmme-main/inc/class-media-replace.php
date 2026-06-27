<?php
if (!defined('ABSPATH')) {
    exit;
}

class WPMME_Media_Replace {
    public function __construct() {
        add_filter('media_row_actions', array($this, 'modify_media_list_table_edit_link'), 10, 2);
        add_filter('attachment_fields_to_edit', array($this, 'add_media_replacement_button'), 10, 2);
        add_action('edit_attachment', array($this, 'replace_media'));
        add_action('admin_enqueue_scripts', array($this, 'enqueue_assets'));
        
        // Cache busting filters
        add_filter('wp_calculate_image_srcset', array($this, 'append_cache_busting_param_to_image_srcset'), 10, 5);
        add_filter('wp_get_attachment_image_src', array($this, 'append_cache_busting_param_to_attachment_image_src'), 10, 2);
        add_filter('wp_prepare_attachment_for_js', array($this, 'append_cache_busting_param_to_attachment_for_js'), 10, 2);
        add_filter('wp_get_attachment_url', array($this, 'append_cache_busting_param_to_attachment_url'), 10, 2);
    }

    public function enqueue_assets($hook) {
        // Only load on media pages
        if (!in_array($hook, array('upload.php', 'post.php'))) {
            return;
        }

        wp_enqueue_media();
        wp_enqueue_style('wpmme-media-replace-css', WPMME_URL . 'assets/css/wpmme-media-replace.css', array(), WPMME_VERSION);
        wp_enqueue_script('wpmme-media-replace-js', WPMME_URL . 'assets/js/wpmme-media-replace.js', array('jquery', 'media-views'), WPMME_VERSION, true);

        wp_localize_script('wpmme-media-replace-js', 'mediaReplace', array(
            'selectMediaText' => __('Select Replacement Media', 'wpmme'),
            'performReplacementText' => __('Use as Replacement', 'wpmme')
        ));
    }

    public function modify_media_list_table_edit_link($actions, $post) {
        $new_actions = array();
        foreach ($actions as $key => $value) {
            if ($key == 'edit') {
                $new_actions['edit'] = '<a href="' . get_edit_post_link($post) . '" aria-label="Edit or Replace">Edit or Replace</a>';
            } else {
                $new_actions[$key] = $value;
            }
        }
        return $new_actions;
    }

    public function add_media_replacement_button($fields, $post) {
        global $pagenow, $typenow;

        $is_attachment_edit = ('post.php' === $pagenow && 'attachment' === $typenow);
        $screen             = function_exists('get_current_screen') ? get_current_screen() : null;
        $is_media_library   = ($screen && 'upload' === $screen->base);

        if (!$is_attachment_edit && !$is_media_library && !wp_doing_ajax()) {
            return $fields;
        }

        $original_attachment_id = '';
        $image_mime_type        = '';
        if (is_object($post)) {
            $original_attachment_id = $post->ID;
            if (property_exists($post, 'post_mime_type')) {
                $image_mime_type = $post->post_mime_type;
            }
        }

        if ($original_attachment_id) {
            $fields['asenha-media-replace'] = array(
                'label' => '',
                'input' => 'html',
                'html'  => '
                <div id="media-replace-div" class="postbox attachment-id-' . $original_attachment_id . '" data-original-image-id="' . $original_attachment_id . '">
                    <div class="postbox-header">
                        <h2 class="hndle ui-sortable-handle">' . __('Replace Media', 'wpmme') . '</h2>
                    </div>
                    <div class="inside">
                        <button type="button" id="asenha-media-replace" class="button-secondary button-large asenha-media-replace-button" data-old-image-mime-type="' . esc_attr($image_mime_type) . '" onclick="replaceMedia(\'' . esc_attr($original_attachment_id) . '\',\'' . esc_attr($image_mime_type) . '\');">' . __('Select New Media File', 'wpmme') . '</button>
                        <input type="hidden" id="new-attachment-id-' . $original_attachment_id . '" name="new-attachment-id-' . $original_attachment_id . '" />
                        <div class="asenha-media-replace-notes"><p>' . __('The current file will be replaced with the selected file (same type) while retaining the current ID, date and URL. Just upload a new image and click Save.', 'wpmme') . '</p></div>
                    </div>
                </div>'
            );
        }

        return $fields;
    }

    public function replace_media($old_attachment_id) {
        if (!isset($_POST['new-attachment-id-' . $old_attachment_id]) || empty($_POST['new-attachment-id-' . $old_attachment_id])) {
            return;
        }

        $new_attachment_id = intval(sanitize_text_field($_POST['new-attachment-id-' . $old_attachment_id]));

        if (!current_user_can('delete_post', $new_attachment_id)) {
            return;
        }

        $old_post_meta = get_post($old_attachment_id, ARRAY_A);
        $old_post_mime = $old_post_meta['post_mime_type'];
        $new_post_meta = get_post($new_attachment_id, ARRAY_A);
        $new_post_mime = $new_post_meta['post_mime_type'];

        if (!empty($new_attachment_id) && is_numeric($new_attachment_id) && ($old_post_mime == $new_post_mime)) {
            $new_attachment_meta = wp_get_attachment_metadata($new_attachment_id);
            $new_media_file_path = get_attached_file($new_attachment_id);

            if (!is_file($new_media_file_path)) {
                return;
            }

            // Delete old files from disk
            $this->delete_media_files($old_attachment_id);

            $old_media_file_path = get_attached_file($old_attachment_id);
            if (!file_exists(dirname($old_media_file_path))) {
                wp_mkdir_p(dirname($old_media_file_path));
            }

            // Copy new to old
            copy($new_media_file_path, $old_media_file_path);

            // Regenerate old meta based on new file
            require_once(ABSPATH . 'wp-admin/includes/image.php');
            $old_media_post_meta_updated = wp_generate_attachment_metadata($old_attachment_id, $old_media_file_path);
            wp_update_attachment_metadata($old_attachment_id, $old_media_post_meta_updated);

            // Delete new temporary attachment
            wp_delete_attachment($new_attachment_id, true);

            // Track for cache busting
            $replaced = get_option('wpmme_replaced_media', array());
            if (count($replaced) >= 5) {
                array_shift($replaced);
            }
            $replaced[] = $old_attachment_id;
            update_option('wpmme_replaced_media', array_unique($replaced));
        }
    }

    private function delete_media_files($post_id) {
        $attachment_meta = wp_get_attachment_metadata($post_id);
        $attachment_file_path = get_attached_file($post_id);
        $attachment_file_basename = basename($attachment_file_path);

        if (isset($attachment_meta['sizes']) && is_array($attachment_meta['sizes'])) {
            foreach ($attachment_meta['sizes'] as $size => $size_info) {
                $intermediate_file_path = str_replace($attachment_file_basename, $size_info['file'], $attachment_file_path);
                wp_delete_file($intermediate_file_path);
            }
        }
        wp_delete_file($attachment_file_path);
    }

    public function append_cache_busting_param_to_image_srcset($sources, $size_array, $image_src, $image_meta, $attachment_id) {
        if ($this->should_bust_cache($attachment_id)) {
            foreach ($sources as $size => $source) {
                $source['url'] .= $this->get_timestamp_param($source['url']);
                $sources[$size] = $source;
            }
        }
        return $sources;
    }

    public function append_cache_busting_param_to_attachment_image_src($image, $attachment_id) {
        if (!empty($image[0]) && $this->should_bust_cache($attachment_id)) {
            $image[0] .= $this->get_timestamp_param($image[0]);
        }
        return $image;
    }

    public function append_cache_busting_param_to_attachment_for_js($response, $attachment) {
        if ($this->should_bust_cache($attachment->ID)) {
            if (false !== strpos($response['url'], '?')) {
                $response['url'] .= $this->get_timestamp_param($response['url']);
            }
            if (isset($response['sizes'])) {
                foreach ($response['sizes'] as $size_name => $size) {
                    $response['sizes'][$size_name]['url'] .= $this->get_timestamp_param($size['url']);
                }
            }
        }
        return $response;
    }

    public function append_cache_busting_param_to_attachment_url($url, $attachment_id) {
        if ($this->should_bust_cache($attachment_id)) {
            $url .= $this->get_timestamp_param($url);
        }
        return $url;
    }

    private function should_bust_cache($attachment_id) {
        $replaced = get_option('wpmme_replaced_media', array());
        return in_array($attachment_id, $replaced);
    }

    private function get_timestamp_param($url) {
        $parts = parse_url($url);
        if (isset($parts['query'])) {
            parse_str($parts['query'], $query);
            if (isset($query['t']) && !empty($query['t'])) {
                return '';
            }
            return (false === strpos($url, '?') ? '?' : '&') . 't=' . time();
        }
        return (false === strpos($url, '?') ? '?' : '&') . 't=' . time();
    }
}
