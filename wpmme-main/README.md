# WPMME

**All-in-One Optimization & Security plugin by MMe.**

WPMME is a comprehensive WordPress plugin that combines essential optimization, security, and media management features into a single, lightweight, and easy-to-use package.

## Features

### Media & Optimization
* **Classic Editor**: Restores the classic WordPress editor.
* **TinyMCE Plugins**: Enhances the classic editor with advanced TinyMCE plugins (Table, SearchReplace, VisualBlocks, etc.).
* **Optimize Image SEO**: Automatically cleans filenames and sets image Alt Text and Title upon upload.
* **Auto Rename Images**: Automatically renames uploaded images based on a custom pattern (e.g., `{domain}-{date}-{random}`).
* **Convert to WebP**: Automatically converts uploaded images (JPEG/PNG) to next-gen WebP format to save space and improve load speed.
* **Image Watermark**: Automatically adds a customizable watermark to uploaded images.
* **Media Replacement**: Easily replace existing media files without changing their IDs or breaking existing links.
* **Remove Image Attributes**: Cleans up unwanted `img` tag attributes in the post content.
* **Auto Upload External Images**: Automatically downloads and saves external images to your media library when pasting content from other sources.

### Security & Enhancements
* **Limit Login Attempts**: Protects against brute-force attacks by blocking IPs after too many failed login attempts.
* **Custom Login URL**: Change the default `wp-login.php` to a custom slug to hide the login page from bots.
* **Custom Login Logo**: Replace the default WordPress logo on the login screen with your brand's logo.
* **Disable XML-RPC**: Blocks XML-RPC to prevent DDoS and brute-force attacks.
* **Disable REST API User Enumeration**: Prevents bots from scraping your user list via the REST API.
* **Disable Author Archives**: Blocks author queries to hide usernames.
* **Disable Comments**: Completely disables comments across the entire site.
* **Remove WP Version**: Removes the WordPress version meta tag to hide your footprint.
* **Clean Up Admin Bar**: Removes unnecessary items (WP Logo, Comments, Updates) from the top admin bar for a cleaner interface.

## Installation

1. Download the latest `.zip` file from the [Releases](https://github.com/hoangmme/wpmme) or the `main` branch.
2. Go to **Plugins > Add New > Upload Plugin** in your WordPress dashboard.
3. Upload the `.zip` file and click **Install Now**, then **Activate**.
4. Go to **WPMME Settings** in the admin menu to configure the features.

## Updating

You don't need to manually download new versions from GitHub. WPMME includes a built-in updater:
1. Go to the **WPMME Settings** page.
2. Scroll to the bottom and click **Pull Latest from GitHub**.
3. The plugin will automatically download the latest version from the `main` branch, extract it, and update itself seamlessly.
