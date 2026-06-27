(function() {
    tinymce.PluginManager.add('signature', function(editor, url) {
        editor.addButton('signature', {
            type: 'menubutton',
            icon: 'signature is-dashicon dashicons dashicons-clipboard',
            menu: [
                {
                    text: 'Clipboard',
                    onclick: function() {
                        jQuery.ajax({
                            url: ajaxurl,
                            method: 'POST',
                            data: {
                                action: 'get_signature_content'
                            },
                            success: function(response) {
                                if (response.success) {
                                    editor.insertContent(response.data);
                                } else {
                                    alert('Failed to retrieve signature content.');
                                }
                            },
                            error: function() {
                                alert('Error fetching signature content.');
                            }
                        });
                    }
                },
                {
                    text: '[signature]',
                    onclick: function() {
                        editor.insertContent('[signature]');
                    }
                }
            ],
            onPostRender: function() {
                jQuery('.is-dashicon').css('font-family', 'dashicons');
            }
        });
    });
})();
