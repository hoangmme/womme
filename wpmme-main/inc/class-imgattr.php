<?php
if (!defined('ABSPATH')) {
    exit;
}

class WPMME_ImgAttr {
    public function __construct() {
        add_filter('content_save_pre', array($this, 'remove_img_attributes'));
    }

    public function remove_img_attributes($content) {
        if (empty($content)) {
            return $content;
        }

        // Use DOMDocument to safely parse and modify HTML
        $dom = new DOMDocument();
        $libxml_previous_state = libxml_use_internal_errors(true);
        
        // Load HTML with UTF-8 encoding
        $dom->loadHTML('<?xml encoding="utf-8" ?>' . $content, LIBXML_HTML_NOIMPLIED | LIBXML_HTML_NODEFDTD);
        
        libxml_clear_errors();
        libxml_use_internal_errors($libxml_previous_state);

        $images = $dom->getElementsByTagName('img');
        $images_to_replace = array();

        foreach ($images as $img) {
            $src = '';
            // Support for lazy loaded images
            if ($img->hasAttribute('data-src')) {
                $src = $img->getAttribute('data-src');
            } elseif ($img->hasAttribute('src')) {
                $src = $img->getAttribute('src');
            }

            $alt = $img->hasAttribute('alt') ? $img->getAttribute('alt') : '';

            // Create a new clean img node
            $new_img = $dom->createElement('img');
            if (!empty($src)) {
                $new_img->setAttribute('src', $src);
            }
            if (!empty($alt)) {
                $new_img->setAttribute('alt', $alt);
            }

            $images_to_replace[] = array('old' => $img, 'new' => $new_img);
        }

        foreach ($images_to_replace as $item) {
            $item['old']->parentNode->replaceChild($item['new'], $item['old']);
        }

        $new_content = $dom->saveHTML();
        // Remove the xml encoding declaration we added
        $new_content = str_replace('<?xml encoding="utf-8" ?>', '', $new_content);

        return $new_content;
    }
}
