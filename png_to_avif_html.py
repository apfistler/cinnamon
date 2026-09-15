#!/usr/bin/env python3

import os
import re
from pathlib import Path

def update_img_tags_in_html(input_dir):
    base_path = Path(input_dir).expanduser()
    if not base_path.exists():
        print(f"Error: Directory {input_dir} does not exist.")
        return

    # Find all HTML and HTM files recursively
    html_files = list(base_path.rglob("*.html")) + list(base_path.rglob("*.htm"))
    total = len(html_files)

    if total == 0:
        print(f"No HTML files found in {base_path}")
        return

    print(f"Found {total} HTML file(s). Scanning and updating <img> tags...")

    # Regex to target <img> tags specifically
    img_tag_pattern = re.compile(r'<img\b[^>]*>', re.IGNORECASE)
    updated_count = 0

    for html_path in html_files:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()

        def replacer(match):
            tag = match.group(0)
            # Replace .png or .PNG with .avif strictly inside the <img> tag
            return re.sub(r'\.png\b', '.avif', tag, flags=re.IGNORECASE)

        new_content = img_tag_pattern.sub(replacer, content)

        if new_content != content:
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated: {html_path.relative_to(base_path)}")
            updated_count += 1

    print(f"\nDone! Processed {total} files. Updated {updated_count} file(s).")

if __name__ == "__main__":
    TARGET_DIR = "~/cinnamon/input"
    update_img_tags_in_html(TARGET_DIR)
