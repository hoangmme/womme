(function() {
    tinymce.PluginManager.add('changecase', function(editor, url) {
        editor.addCommand('changeCaseCommand', function(ui, value) {
            var sel = editor.dom.decode(editor.selection.getContent());
            var transformedText = "";
            switch (value) {
                case 'nocaps':
                    transformedText = sel.toLowerCase();
                    break;
                case 'allcaps':
                    transformedText = sel.toUpperCase();
                    break;
                case 'sentence':
                    transformedText = sel.toLowerCase().replace(/(^\s*\w|[\.\!\?]\s*\w)/g, function(c) {
                        return c.toUpperCase();
                    });
                    break;
                case 'capitalize':
                    transformedText = sel.toLowerCase().replace(/(^|\s)([a-z])/g, function(m, p1, p2) {
                        return p1 + p2.toUpperCase();
                    });
                    break;
                case 'togglecase':
                    transformedText = sel.split('').map(function(char) {
                        return char === char.toUpperCase() ? char.toLowerCase() : char.toUpperCase();
                    }).join('');
                    break;
            }
            editor.selection.setContent(transformedText);
            editor.save();
            editor.isNotDirty = true;
        });
        editor.addButton('changecase', {
            type: 'listbox',
            text: 'Aa',
            title: 'Change Case',
            icon: false,
            onselect: function(e) {
                var value = this.value();
                editor.execCommand('changeCaseCommand', false, value);
            },
            values: [
                { text: 'UPPERCASE', value: 'allcaps', shortcut: 'Ctrl+Shift+1'},
                { text: 'lowercase', value: 'nocaps', shortcut: 'Ctrl+Shift+2'},
                { text: 'Title Case', value: 'capitalize', shortcut: 'Ctrl+Shift+3'},
                { text: 'Sentence Case', value: 'sentence', shortcut: 'Ctrl+Shift+4'},
                { text: 'tOGGLE cASE', value: 'togglecase', shortcut: 'Ctrl+Shift+5'},
            ]
        });

        editor.addShortcut('Ctrl+Shift+1', '', function() {
            editor.execCommand('changeCaseCommand', false, 'allcaps');
        });

        editor.addShortcut('Ctrl+Shift+2', '', function() {
            editor.execCommand('changeCaseCommand', false, 'nocaps');
        });

        editor.addShortcut('Ctrl+Shift+3', '', function() {
            editor.execCommand('changeCaseCommand', false, 'capitalize');
        });

        editor.addShortcut('Ctrl+Shift+4', '', function() {
            editor.execCommand('changeCaseCommand', false, 'sentence');
        });

        editor.addShortcut('Ctrl+Shift+5', '', function() {
            editor.execCommand('changeCaseCommand', false, 'togglecase');
        });
    });
})();
