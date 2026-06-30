<?php
if (!defined('ABSPATH')) {
    exit;
}

if (defined('WP_CLI') && WP_CLI) {
    class WPMME_CLI_Command {
        /**
         * Convert all existing JPEG and PNG images to WebP format and update database links.
         *
         * ## OPTIONS
         *
         * [--quality=<quality>]
         * : WebP compression quality (1-100). Default is 82.
         *
         * ## EXAMPLES
         *
         *     wp mme webp
         *     wp mme webp --quality=85
         */
        public function webp($args, $assoc_args) {
            if (!function_exists('imagewebp')) {
                WP_CLI::error("Thư viện GD/imagewebp chưa được bật trên PHP server này.");
                return;
            }

            global $wpdb;
            $quality = isset($assoc_args['quality']) ? (int) $assoc_args['quality'] : 82;
            if ($quality < 1 || $quality > 100) {
                $quality = 82;
            }

            WP_CLI::log("Đang quét các ảnh JPEG/PNG trong Media Library...");
            $attachments = $wpdb->get_results("SELECT ID, guid FROM {$wpdb->posts} WHERE post_type = 'attachment' AND post_mime_type IN ('image/jpeg', 'image/png')");

            if (empty($attachments)) {
                WP_CLI::success("Không tìm thấy ảnh JPEG/PNG nào cần chuyển đổi!");
                return;
            }

            $total = count($attachments);
            WP_CLI::log("Tìm thấy {$total} ảnh. Bắt đầu nén sang WebP (quality: {$quality})...");
            $progress = \WP_CLI\Utils\make_progress_bar('Chuyển đổi WebP', $total);

            $converted_count = 0;
            $url_replacements = array();

            $upload_dir = wp_upload_dir();
            $base_dir = $upload_dir['basedir'];

            foreach ($attachments as $att) {
                $file_path = get_attached_file($att->ID);
                if (empty($file_path) || !file_exists($file_path)) {
                    $progress->tick();
                    continue;
                }

                $mime = get_post_mime_type($att->ID);
                $img = null;
                if ($mime === 'image/jpeg') {
                    $img = @imagecreatefromjpeg($file_path);
                } elseif ($mime === 'image/png') {
                    $img = @imagecreatefrompng($file_path);
                    if ($img) {
                        imagepalettetotruecolor($img);
                        imagealphablending($img, true);
                        imagesavealpha($img, true);
                    }
                }

                if (!$img) {
                    $progress->tick();
                    continue;
                }

                $webp_path = preg_replace('/\.(jpg|jpeg|png)$/i', '.webp', $file_path);
                if (imagewebp($img, $webp_path, $quality)) {
                    imagedestroy($img);

                    $old_rel = str_replace($base_dir . '/', '', $file_path);
                    $new_rel = str_replace($base_dir . '/', '', $webp_path);

                    $old_basename = wp_basename($file_path);
                    $new_basename = wp_basename($webp_path);
                    if ($old_basename !== $new_basename) {
                        $url_replacements[$old_basename] = $new_basename;
                    }

                    @unlink($file_path);

                    // Update thumbnails in attachment metadata
                    $meta = wp_get_attachment_metadata($att->ID);
                    if (!empty($meta) && is_array($meta)) {
                        if (!empty($meta['file'])) {
                            $meta['file'] = preg_replace('/\.(jpg|jpeg|png)$/i', '.webp', $meta['file']);
                        }
                        if (!empty($meta['sizes']) && is_array($meta['sizes'])) {
                            $dir_path = dirname($file_path);
                            foreach ($meta['sizes'] as $size => $sdata) {
                                if (!empty($sdata['file'])) {
                                    $thumb_file = $dir_path . '/' . $sdata['file'];
                                    if (file_exists($thumb_file)) {
                                        $thumb_mime = isset($sdata['mime-type']) ? $sdata['mime-type'] : $mime;
                                        $t_img = null;
                                        if ($thumb_mime === 'image/jpeg' || preg_replace('/^.*\./', '', $thumb_file) === 'jpg') {
                                            $t_img = @imagecreatefromjpeg($thumb_file);
                                        } elseif ($thumb_mime === 'image/png' || preg_replace('/^.*\./', '', $thumb_file) === 'png') {
                                            $t_img = @imagecreatefrompng($thumb_file);
                                            if ($t_img) {
                                                imagepalettetotruecolor($t_img);
                                                imagealphablending($t_img, true);
                                                imagesavealpha($t_img, true);
                                            }
                                        }
                                        if ($t_img) {
                                            $t_webp = preg_replace('/\.(jpg|jpeg|png)$/i', '.webp', $thumb_file);
                                            if (imagewebp($t_img, $t_webp, $quality)) {
                                                imagedestroy($t_img);
                                                @unlink($thumb_file);

                                                $old_t_name = $sdata['file'];
                                                $new_t_name = wp_basename($t_webp);
                                                $meta['sizes'][$size]['file'] = $new_t_name;
                                                $meta['sizes'][$size]['mime-type'] = 'image/webp';

                                                if ($old_t_name !== $new_t_name) {
                                                    $url_replacements[$old_t_name] = $new_t_name;
                                                }
                                            } else {
                                                imagedestroy($t_img);
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        wp_update_attachment_metadata($att->ID, $meta);
                    }

                    $new_guid = preg_replace('/\.(jpg|jpeg|png)$/i', '.webp', $att->guid);
                    $wpdb->update($wpdb->posts, array('post_mime_type' => 'image/webp', 'guid' => $new_guid), array('ID' => $att->ID));
                    update_post_meta($att->ID, '_wp_attached_file', $new_rel);

                    $converted_count++;
                } else {
                    imagedestroy($img);
                }

                $progress->tick();
            }

            $progress->finish();
            WP_CLI::success("Đã nén thành công {$converted_count}/{$total} ảnh sang định dạng WebP!");

            if (!empty($url_replacements)) {
                WP_CLI::log("Đang đồng bộ link ảnh (Search & Replace) trong Database bài viết và Elementor...");
                $sr_progress = \WP_CLI\Utils\make_progress_bar('Đồng bộ link DB', count($url_replacements));
                $target_tables = "{$wpdb->posts} {$wpdb->postmeta} {$wpdb->options}";
                foreach ($url_replacements as $old_name => $new_name) {
                    try {
                        \WP_CLI::runcommand("search-replace '{$old_name}' '{$new_name}' {$target_tables} --quiet", array('return' => true));
                    } catch (\Exception $e) {}
                    $sr_progress->tick();
                }
                $sr_progress->finish();
                WP_CLI::success("Đã cập nhật toàn bộ link ảnh trong Database!");
            }
        }
    }

    WP_CLI::add_command('mme', 'WPMME_CLI_Command');
}
