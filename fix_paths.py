#!/usr/bin/env python3
import os
import re

WEB_DIR = "/var/www/adamfistler.com/public_html"

# Common asset extensions and folder prefixes to target
asset_extensions = r'\.(css|js|png|jpg|jpeg|gif|svg|ico|webp|avif|pdf|zip)$'

def fix_html_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Match src="..." or href="..." attribute values
    pattern = r'(src|href)=([\'"])([^\'"]+)([\'"])'

    def replace_path(match):
        attr = match.group(1)
        quote1 = match.group(2)
        path = match.group(3)
        quote2 = match.group(4)

        # Skip external, absolute, anchor, or protocol links
        if (path.startswith('/') or 
            path.startswith('http://') or 
            path.startswith('https://') or 
            path.startswith('//') or 
            path.startswith('#') or 
            path.startswith('mailto:') or 
            path.startswith('data:') or 
            path.startswith('javascript:')):
            return match.group(0)

        # Check if the path points to a static asset file or folder
        is_asset = (re.search(asset_extensions, path, re.IGNORECASE) or 
                    path.startswith('css/') or 
                    path.startswith('js/') or 
                    path.startswith('images/') or 
                    path.startswith('img/') or 
                    path.startswith('assets/'))

        if is_asset:
            new_path = '/' + path.lstrip('./')
            return f'{attr}={quote1}{new_path}{quote2}'

        return match.group(0)

    new_content = re.sub(pattern, replace_path, content)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated paths in: {filepath}")

def main():
    if not os.path.exists(WEB_DIR):
        print(f"Error: Directory {WEB_DIR} not found.")
        return

    for root, dirs, files in os.walk(WEB_DIR):
        for file in files:
            if file.endswith('.html'):
                fix_html_file(os.path.join(root, file))

    print("Asset path correction complete.")

if __name__ == '__main__':
    main()
