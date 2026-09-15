#!/usr/bin/env python3

import re
from pathlib import Path

def update_yaml_files(input_dir):
    base_path = Path(input_dir).expanduser()
    if not base_path.exists():
        print(f"Error: Directory {input_dir} does not exist.")
        return

    yaml_files = list(base_path.rglob("*.yaml")) + list(base_path.rglob("*.yml"))
    total = len(yaml_files)

    if total == 0:
        print(f"No YAML files found in {base_path}")
        return

    print(f"Found {total} YAML file(s). Scanning and updating references...")
    updated_count = 0

    for yaml_path in yaml_files:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Replace .png or .PNG with .avif
        new_content = re.sub(r'\.png\b', '.avif', content, flags=re.IGNORECASE)

        if new_content != content:
            with open(yaml_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated: {yaml_path.relative_to(base_path)}")
            updated_count += 1

    print(f"\nDone! Processed {total} files. Updated {updated_count} YAML file(s).")

if __name__ == "__main__":
    TARGET_DIR = "~/cinnamon/input"
    update_yaml_files(TARGET_DIR)
