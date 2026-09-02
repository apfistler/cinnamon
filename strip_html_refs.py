#!/usr/bin/env python3

import os
import re
import sys

INPUT_DIR = 'input'

# Regex 1: Matches HTML/XML attributes like href="/html/...", src="/html/..."
ATTR_REGEX = re.compile(r'((?:href|src|action|data-[a-z-]+|content)=["\'])/html(?=/|["\'])')

# Regex 2: Matches quotes or key values in YAML like url: "/html/..." or "/html/..."
YAML_REF_REGEX = re.compile(r'(["\'])/html(?=/|["\'])')


def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Apply both replacements
    new_content, count_attr = ATTR_REGEX.subn(r'\1', content)
    new_content, count_yaml = YAML_REF_REGEX.subn(r'\1', new_content)
    
    total_changes = count_attr + count_yaml

    if total_changes > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {file_path} ({total_changes} replacement{'s' if total_changes > 1 else ''})")


def main():
    if not os.path.exists(INPUT_DIR):
        print(f"Error: Directory '{INPUT_DIR}' does not exist.")
        sys.exit(1)

    print(f"Scanning '{INPUT_DIR}' for .html and .yaml files...")

    valid_extensions = ('.html', '.yaml', '.yml')

    for root, _, files in os.walk(INPUT_DIR):
        for file in files:
            if file.endswith(valid_extensions):
                file_path = os.path.join(root, file)
                process_file(file_path)


if __name__ == '__main__':
    main()
