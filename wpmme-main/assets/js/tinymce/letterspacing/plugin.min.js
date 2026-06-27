(function() {
    tinymce.PluginManager.add('letterspacing', function(editor, url) {
        editor.addCommand('LetterSpacingCommand', function(ui, value) {
            var sel = editor.dom.decode(editor.selection.getContent());
            var transformedText = "";

            // Check if the value is a valid letter spacing value within the range
            if (/^-?\d+px$/.test(value) || /^normal$/i.test(value)) {
                transformedText = '<span style="letter-spacing: ' + value + ';">' + sel + '</span>';
            } else {
                // Handle default case or invalid input
                transformedText = sel;
            }

            editor.selection.setContent(transformedText);
            editor.save();
            editor.isNotDirty = true;
        });

        editor.addButton('letterspacing', {
            type: 'listbox',
            text: 'VA',
            title: 'Letter Spacing',
            icon: false,
            onselect: function(e) {
                var value = this.value();
                editor.execCommand('LetterSpacingCommand', false, value);
            },
            values: [
                { text: 'Normal', value: 'normal' },
                { text: '-4px', value: '-4px' },
                { text: '-2px', value: '-2px' },
                { text: '2px', value: '2px' },
                { text: '4px', value: '4px' },
                { text: '6px', value: '6px' },
                { text: '8px', value: '8px' },
                { text: '10px', value: '10px' },
                { text: '12px', value: '12px' },
                { text: '14px', value: '14px' },
            ]
        });
    });
})();
