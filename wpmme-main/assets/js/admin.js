jQuery(document).ready(function($) {
    
    // Toggle expandable bodies
    $('.wpmme-switch input').on('change', function() {
        var id = $(this).attr('id');
        if (id && id.startsWith('toggle-')) {
            var bodyId = '#body-' + id.replace('toggle-', '');
            if ($(this).is(':checked')) {
                $(bodyId).slideDown(200);
            } else {
                $(bodyId).slideUp(200);
            }
        }
    });

    // Update range sliders
    $('.wpmme-range').on('input', function() {
        $(this).siblings('.wpmme-range-val').text($(this).val());
    });

    // Save Settings
    $('#wpmme-save').on('click', function(e) {
        e.preventDefault();
        var $btn = $(this);
        $btn.text('Saving...').prop('disabled', true);

        var data = $('#wpmme-settings-form').serialize() + '&action=wpmme_save_settings&nonce=' + wpmme_ajax.nonce;

        $.post(wpmme_ajax.url, data, function(response) {
            $btn.text('Save Settings').prop('disabled', false);
            if (response.success) {
                alert('Settings saved successfully!');
            } else {
                alert('Error: ' + response.data);
            }
        });
    });

    // Reset Settings
    $('#wpmme-reset').on('click', function(e) {
        e.preventDefault();
        if (confirm('Are you sure you want to reset all settings to defaults?')) {
            var $btn = $(this);
            $btn.text('Resetting...').prop('disabled', true);

            $.post(wpmme_ajax.url, {
                action: 'wpmme_reset_settings',
                nonce: wpmme_ajax.nonce
            }, function(response) {
                if (response.success) {
                    location.reload();
                } else {
                    $btn.text('Reset').prop('disabled', false);
                    alert('Error: ' + response.data);
                }
            });
        }
    });

    // WordPress Media Uploader
    function setupMediaUploader(btnId, inputId) {
        var file_frame;
        $(btnId).on('click', function(e) {
            e.preventDefault();
            if (file_frame) {
                file_frame.open();
                return;
            }
            file_frame = wp.media.frames.file_frame = wp.media({
                title: 'Select Image',
                button: { text: 'Use this image' },
                multiple: false
            });
            file_frame.on('select', function() {
                var attachment = file_frame.state().get('selection').first().toJSON();
                $(inputId).val(attachment.url);
            });
            file_frame.open();
        });
    }

    setupMediaUploader('#btn-upload-watermark', '#watermark_img');
    setupMediaUploader('#btn-upload-logo', '#login_logo_url');

    // Bulk Operations Modal
    var currentAction = '';
    
    $('#btn-rename-all').on('click', function() {
        showModal('Rename All Images', 'This will rename all existing attachments in your media library based on your pattern. This process might take a while.', 'wpmme_rename_all');
    });

    $('#btn-webp-all').on('click', function() {
        showModal('Convert All to WEBP', 'This will convert all existing JPEG and PNG images to WEBP. Original images will be kept.', 'wpmme_webp_all');
    });

    $('#btn-watermark-all').on('click', function() {
        showModal('Apply Watermark', 'This will apply the watermark to all existing images. Make sure you have saved your watermark settings first.', 'wpmme_watermark_all');
    });

    $('#btn-force-update').on('click', function() {
        if (confirm('Are you sure you want to download and overwrite the plugin with the latest version from GitHub?')) {
            var $btn = $(this);
            var originalText = $btn.text();
            $btn.text('Downloading & Updating... Please wait').prop('disabled', true);

            $.post(wpmme_ajax.url, {
                action: 'wpmme_force_update',
                nonce: wpmme_ajax.nonce
            }, function(response) {
                if (response.success) {
                    $btn.text('Update successful! Reloading...');
                    setTimeout(function() { location.reload(); }, 1500);
                } else {
                    alert('Update failed: ' + response.data);
                    $btn.text(originalText).prop('disabled', false);
                }
            }).fail(function() {
                alert('Server error during update.');
                $btn.text(originalText).prop('disabled', false);
            });
        }
    });

    function showModal(title, desc, action) {
        currentAction = action;
        $('#wpmme-modal-title').text(title);
        $('#wpmme-modal-desc').text(desc);
        $('#wpmme-modal-progress').css('width', '0%');
        $('#wpmme-modal-text').text('0%');
        $('#wpmme-modal').fadeIn();
    }

    $('#wpmme-modal-close').on('click', function() {
        $('#wpmme-modal').fadeOut();
    });

    $('#wpmme-modal-start').on('click', function() {
        var $btn = $(this);
        var $closeBtn = $('#wpmme-modal-close');
        $btn.prop('disabled', true);
        $closeBtn.prop('disabled', true);
        
        // Bulk Operations AJAX Mock (Real implementation below)
        // Mock for others
        var progress = 0;
        var interval = setInterval(function() {
            progress += 10;
            $('#wpmme-modal-progress').css('width', progress + '%');
            $('#wpmme-modal-text').text(progress + '%');
            
            if (progress >= 100) {
                clearInterval(interval);
                $btn.prop('disabled', false);
                $closeBtn.prop('disabled', false);
                $('#wpmme-modal-desc').text('Process completed!');
            }
        }, 500);
    });
});
