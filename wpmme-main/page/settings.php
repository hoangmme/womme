<?php
if (!defined('ABSPATH')) {
    exit;
}

$options = wpmme_get_options();
?>
<div class="wrap">
    <!-- WordPress will automatically inject admin notices here -->
</div>
<div class="wpmme-wrap">
    <div class="wpmme-header">
        <h1>WPMME Settings <span class="wpmme-version">v<?php echo WPMME_VERSION; ?></span></h1>
    </div>

    <form id="wpmme-settings-form">
        <!-- Editor Group -->
        <h2 class="wpmme-section-title"><span class="dashicons dashicons-edit-page"></span> Editor</h2>
        
        <div class="wpmme-card">
            <div class="wpmme-card-header">
                <div class="wpmme-card-info">
                    <h3>Classic Editor</h3>
                    <p>Use the classic WordPress editor instead of Gutenberg.</p>
                </div>
                <label class="wpmme-switch">
                    <input type="checkbox" name="classic_editor" <?php checked($options['classic_editor']); ?>>
                    <span class="wpmme-slider"></span>
                </label>
            </div>
        </div>

        <div class="wpmme-card">
            <div class="wpmme-card-header">
                <div class="wpmme-card-info">
                    <h3>TinyMCE Plugins</h3>
                    <p>Add extra buttons (font size, color, table, anchor) to the classic editor toolbar.</p>
                </div>
                <label class="wpmme-switch">
                    <input type="checkbox" name="tinymce_plugins" <?php checked($options['tinymce_plugins']); ?>>
                    <span class="wpmme-slider"></span>
                </label>
            </div>
        </div>

        <!-- Images Group -->
        <h2 class="wpmme-section-title"><span class="dashicons dashicons-format-image"></span> Images</h2>

        <div class="wpmme-card">
            <div class="wpmme-card-header">
                <div class="wpmme-card-info">
                    <h3>Media Replacement</h3>
                    <p>Add a button to replace existing media files with new ones while keeping the same URL.</p>
                </div>
                <label class="wpmme-switch">
                    <input type="checkbox" name="media_replace" <?php checked($options['media_replace']); ?>>
                    <span class="wpmme-slider"></span>
                </label>
            </div>
        </div>

        <div class="wpmme-card">
            <div class="wpmme-card-header">
                <div class="wpmme-card-info">
                    <h3>Optimize Image SEO</h3>
                    <p>Automatically set image alt text and title from filename upon upload.</p>
                </div>
                <label class="wpmme-switch">
                    <input type="checkbox" name="image_seo" <?php checked($options['image_seo']); ?>>
                    <span class="wpmme-slider"></span>
                </label>
            </div>
        </div>

        <div class="wpmme-card">
            <div class="wpmme-card-header">
                <div class="wpmme-card-info">
                    <h3>Auto Upload Images</h3>
                    <p>Automatically download external images in post content to media library when saving.</p>
                </div>
                <label class="wpmme-switch">
                    <input type="checkbox" name="auto_upload" <?php checked($options['auto_upload']); ?>>
                    <span class="wpmme-slider"></span>
                </label>
            </div>
        </div>

        <div class="wpmme-card">
            <div class="wpmme-card-header">
                <div class="wpmme-card-info">
                    <h3>Remove IMG Attributes</h3>
                    <p>Remove unnecessary attributes (width, height, class, style) from images in post content.</p>
                </div>
                <label class="wpmme-switch">
                    <input type="checkbox" name="imgattr" <?php checked($options['imgattr']); ?>>
                    <span class="wpmme-slider"></span>
                </label>
            </div>
        </div>

        <div class="wpmme-card has-body">
            <div class="wpmme-card-header">
                <div class="wpmme-card-info">
                    <h3>Auto Rename</h3>
                    <p>Automatically rename files upon upload based on a pattern.</p>
                </div>
                <label class="wpmme-switch">
                    <input type="checkbox" name="rename" id="toggle-rename" <?php checked($options['rename']); ?>>
                    <span class="wpmme-slider"></span>
                </label>
            </div>
            <div class="wpmme-card-body" id="body-rename" <?php echo $options['rename'] ? '' : 'style="display:none;"'; ?>>
                <div class="wpmme-form-group">
                    <label>Filename Pattern</label>
                    <input type="text" name="rename_pattern" value="<?php echo esc_attr($options['rename_pattern']); ?>" class="regular-text">
                    <p class="description">Variables: {domain}, {original}, {random}, {date}, {datetime}</p>
                </div>
                <button type="button" class="button wpmme-btn-action" id="btn-rename-all">Rename All Existing</button>
            </div>
        </div>

        <div class="wpmme-card has-body">
            <div class="wpmme-card-header">
                <div class="wpmme-card-info">
                    <h3>Convert to WEBP</h3>
                    <p>Automatically convert uploaded JPEG/PNG images to WEBP format.</p>
                </div>
                <label class="wpmme-switch">
                    <input type="checkbox" name="webp" id="toggle-webp" <?php checked($options['webp']); ?>>
                    <span class="wpmme-slider"></span>
                </label>
            </div>
            <div class="wpmme-card-body" id="body-webp" <?php echo $options['webp'] ? '' : 'style="display:none;"'; ?>>
                <div class="wpmme-form-group">
                    <label>Quality (1-100)</label>
                    <p class="description" style="margin-bottom: 10px;">Drag the slider to adjust WebP image quality. Lower values reduce file size but decrease visual quality. Higher values look better but result in larger files. Recommended: 80.</p>
                    <div class="wpmme-range-wrap">
                        <input type="range" name="webp_quality" min="1" max="100" value="<?php echo esc_attr($options['webp_quality']); ?>" class="wpmme-range">
                        <span class="wpmme-range-val"><?php echo esc_html($options['webp_quality']); ?></span>
                    </div>
                </div>
                <button type="button" class="button wpmme-btn-action" id="btn-webp-all">Convert All Existing</button>
            </div>
        </div>

        <div class="wpmme-card has-body">
            <div class="wpmme-card-header">
                <div class="wpmme-card-info">
                    <h3>Watermark</h3>
                    <p>Automatically apply a watermark image to uploaded images.</p>
                </div>
                <label class="wpmme-switch">
                    <input type="checkbox" name="watermark" id="toggle-watermark" <?php checked($options['watermark']); ?>>
                    <span class="wpmme-slider"></span>
                </label>
            </div>
            <div class="wpmme-card-body" id="body-watermark" <?php echo $options['watermark'] ? '' : 'style="display:none;"'; ?>>
                <div class="wpmme-form-group">
                    <label>Watermark Image URL</label>
                    <div class="wpmme-upload-wrap">
                        <input type="text" name="watermark_img" id="watermark_img" value="<?php echo esc_attr($options['watermark_img']); ?>" class="regular-text">
                        <button type="button" class="button" id="btn-upload-watermark">Select Image</button>
                    </div>
                </div>
                
                <div class="wpmme-form-group">
                    <label>Position</label>
                    <div class="wpmme-position-grid">
                        <?php 
                        $positions = array(
                            'top-left', 'top-center', 'top-right',
                            'center-left', 'center', 'center-right',
                            'bottom-left', 'bottom-center', 'bottom-right'
                        );
                        foreach ($positions as $pos) {
                            $checked = checked($options['watermark_position'], $pos, false);
                            echo '<label class="wpmme-pos-item"><input type="radio" name="watermark_position" value="'.esc_attr($pos).'" '.$checked.'><span></span></label>';
                        }
                        ?>
                    </div>
                </div>

                <div class="wpmme-form-group">
                    <label>Size (%)</label>
                    <div class="wpmme-range-wrap">
                        <input type="range" name="watermark_size" min="10" max="100" value="<?php echo esc_attr($options['watermark_size']); ?>" class="wpmme-range">
                        <span class="wpmme-range-val"><?php echo esc_html($options['watermark_size']); ?></span>
                    </div>
                </div>

                <div class="wpmme-form-group">
                    <label>Margin (px)</label>
                    <div class="wpmme-range-wrap">
                        <input type="range" name="watermark_margin" min="0" max="100" value="<?php echo esc_attr($options['watermark_margin']); ?>" class="wpmme-range">
                        <span class="wpmme-range-val"><?php echo esc_html($options['watermark_margin']); ?></span>
                    </div>
                </div>

                <div class="wpmme-form-group">
                    <label>Opacity (%)</label>
                    <div class="wpmme-range-wrap">
                        <input type="range" name="watermark_opacity" min="10" max="100" value="<?php echo esc_attr($options['watermark_opacity']); ?>" class="wpmme-range">
                        <span class="wpmme-range-val"><?php echo esc_html($options['watermark_opacity']); ?></span>
                    </div>
                </div>

                <button type="button" class="button wpmme-btn-action" id="btn-watermark-all">Apply to All Existing</button>
            </div>
        </div>

        <!-- Security & Login Group -->
        <h2 class="wpmme-section-title"><span class="dashicons dashicons-shield"></span> Security & Login</h2>

        <div class="wpmme-card">
            <div class="wpmme-card-header">
                <div class="wpmme-card-info">
                    <h3>Disable XML-RPC</h3>
                    <p>Disable XML-RPC services to prevent attacks.</p>
                </div>
                <label class="wpmme-switch">
                    <input type="checkbox" name="disable_xmlrpc" <?php checked($options['disable_xmlrpc']); ?>>
                    <span class="wpmme-slider"></span>
                </label>
            </div>
        </div>

        <div class="wpmme-card">
            <div class="wpmme-card-header">
                <div class="wpmme-card-info">
                    <h3>Remove WP Version</h3>
                    <p>Remove WordPress version meta tag from header, RSS, and assets.</p>
                </div>
                <label class="wpmme-switch">
                    <input type="checkbox" name="remove_version" <?php checked($options['remove_version']); ?>>
                    <span class="wpmme-slider"></span>
                </label>
            </div>
        </div>

        <div class="wpmme-card">
            <div class="wpmme-card-header">
                <div class="wpmme-card-info">
                    <h3>Disable REST API User Enumeration</h3>
                    <p>Block access to /wp-json/wp/v2/users to prevent username leakage.</p>
                </div>
                <label class="wpmme-switch">
                    <input type="checkbox" name="disable_rest_users" <?php checked($options['disable_rest_users']); ?>>
                    <span class="wpmme-slider"></span>
                </label>
            </div>
        </div>

        <div class="wpmme-card">
            <div class="wpmme-card-header">
                <div class="wpmme-card-info">
                    <h3>Disable Author Archive</h3>
                    <p>Redirect author pages and block ?author=N queries.</p>
                </div>
                <label class="wpmme-switch">
                    <input type="checkbox" name="disable_author" <?php checked($options['disable_author']); ?>>
                    <span class="wpmme-slider"></span>
                </label>
            </div>
        </div>

        <div class="wpmme-card">
            <div class="wpmme-card-header">
                <div class="wpmme-card-info">
                    <h3>Disable Comments</h3>
                    <p>Disable comments globally across the entire site.</p>
                </div>
                <label class="wpmme-switch">
                    <input type="checkbox" name="disable_comments" <?php checked($options['disable_comments']); ?>>
                    <span class="wpmme-slider"></span>
                </label>
            </div>
        </div>

        <div class="wpmme-card has-body">
            <div class="wpmme-card-header">
                <div class="wpmme-card-info">
                    <h3>Limit Login Attempts</h3>
                    <p>Block IP addresses that fail to login after multiple attempts.</p>
                </div>
                <label class="wpmme-switch">
                    <input type="checkbox" name="limit_login" id="toggle-limit-login" <?php checked($options['limit_login']); ?>>
                    <span class="wpmme-slider"></span>
                </label>
            </div>
            <div class="wpmme-card-body" id="body-limit-login" <?php echo $options['limit_login'] ? '' : 'style="display:none;"'; ?>>
                <div class="wpmme-form-group">
                    <label>Max Allowed Retries</label>
                    <input type="number" name="limit_login_retries" value="<?php echo esc_attr($options['limit_login_retries']); ?>" class="regular-text" min="1" max="99">
                    <p class="description">Number of failed login attempts allowed before the IP is temporarily blocked.</p>
                </div>
            </div>
        </div>

        <div class="wpmme-card">
            <div class="wpmme-card-header">
                <div class="wpmme-card-info">
                    <h3>Clean Up Admin Bar</h3>
                    <p>Remove unnecessary items (WP Logo, Updates, Comments, etc.) from the top admin bar.</p>
                </div>
                <label class="wpmme-switch">
                    <input type="checkbox" name="admin_bar_clean" <?php checked($options['admin_bar_clean']); ?>>
                    <span class="wpmme-slider"></span>
                </label>
            </div>
        </div>

        <div class="wpmme-card has-body">
            <div class="wpmme-card-header">
                <div class="wpmme-card-info">
                    <h3>Login Logo</h3>
                    <p>Change the default WordPress logo on the login page.</p>
                </div>
                <label class="wpmme-switch">
                    <input type="checkbox" name="login_logo" id="toggle-login-logo" <?php checked($options['login_logo']); ?>>
                    <span class="wpmme-slider"></span>
                </label>
            </div>
            <div class="wpmme-card-body" id="body-login-logo" <?php echo $options['login_logo'] ? '' : 'style="display:none;"'; ?>>
                <div class="wpmme-form-group">
                    <label>Logo Image URL</label>
                    <div class="wpmme-upload-wrap">
                        <input type="text" name="login_logo_url" id="login_logo_url" value="<?php echo esc_attr($options['login_logo_url']); ?>" class="regular-text">
                        <button type="button" class="button" id="btn-upload-logo">Select Image</button>
                    </div>
                </div>
            </div>
        </div>

        <div class="wpmme-card has-body">
            <div class="wpmme-card-header">
                <div class="wpmme-card-info">
                    <h3>Change Login Slug</h3>
                    <p>Change wp-admin/wp-login URL to prevent brute force attacks.</p>
                </div>
                <label class="wpmme-switch">
                    <input type="checkbox" name="login_slug" id="toggle-login-slug" <?php checked($options['login_slug']); ?>>
                    <span class="wpmme-slider"></span>
                </label>
            </div>
            <div class="wpmme-card-body" id="body-login-slug" <?php echo $options['login_slug'] ? '' : 'style="display:none;"'; ?>>
                <div class="wpmme-form-group">
                    <label>Custom Login Slug</label>
                    <input type="text" name="login_slug_value" value="<?php echo esc_attr($options['login_slug_value']); ?>" class="regular-text">
                    <p class="description">Example: zogin</p>
                </div>
            </div>
        </div>

        <h2 class="wpmme-section-title"><span class="dashicons dashicons-update"></span> Plugin Updates</h2>
        
        <div class="wpmme-card has-body">
            <div class="wpmme-card-header">
                <div class="wpmme-card-info">
                    <h3>Manual Update</h3>
                    <p>Force the plugin to download and update to the latest code from GitHub main branch.</p>
                </div>
            </div>
            <div class="wpmme-card-body">
                <p class="description">Clicking the button below will download the latest ZIP from GitHub, extract it, and overwrite this plugin. Use with caution.</p>
                <button type="button" class="button button-secondary wpmme-btn-action" id="btn-force-update">Pull Latest from GitHub</button>
            </div>
        </div>

    </form>
</div>

<div class="wpmme-footer">
    <button type="button" class="button button-primary button-hero" id="wpmme-save">Save Settings</button>
    <button type="button" class="button button-hero" id="wpmme-reset">Reset</button>
</div>

<!-- Modal Template -->
<div class="wpmme-modal-overlay" id="wpmme-modal" style="display:none;">
    <div class="wpmme-modal-content">
        <h3 id="wpmme-modal-title">Action</h3>
        <p id="wpmme-modal-desc">Processing...</p>
        <div class="wpmme-progress">
            <div class="wpmme-progress-bar" id="wpmme-modal-progress"></div>
        </div>
        <p class="wpmme-progress-text" id="wpmme-modal-text">0%</p>
        <div class="wpmme-modal-footer">
            <button class="button" id="wpmme-modal-close">Close</button>
            <button class="button button-primary" id="wpmme-modal-start">Start</button>
        </div>
    </div>
</div>
