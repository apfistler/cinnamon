#!/usr/bin/env python3

import os
import re
import sys

# Regex targeting path references to 'landing' in attributes, URLs, and quotes
# Handles formats like: /landing/, /landing.html, /landing", 'landing/...', etc.
LANDING_REF_REGEX = re.compile(
    r'((?:href|src|action|url|path|data-[a-z-]+|content)=["\']?|["\']|/)\blanding\b(\.html)?'
)


def update_file_references(file_path):
    """Update inside contents from landing/ or landing.html to index/ or index.html."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return

    # Replace occurrences of landing with index in URLs/paths/attributes
    def replace_match(match):
        prefix = match.group(1)
        ext = match.group(2) or ''
        return f"{prefix}index{ext}"

    new_content, count = LANDING_REF_REGEX.subn(replace_match, content)

    if count > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  [Refactored {count} ref(s)] {file_path}")


def rename_landing_files(target_dir):
    """Rename landing.html and landing.yaml files to index.html and index.yaml."""
    for root, _, files in os.walk(target_dir):
        for file in files:
            if file in ('landing.html', 'landing.yaml', 'landing.yml'):
                ext = os.path.splitext(file)[1]
                old_path = os.path.join(root, file)
                new_path = os.path.join(root, f'index{ext}')
                os.rename(old_path, new_path)
                print(f"  [Renamed File] {old_path} -> {new_path}")


def rename_landing_dirs(target_dir):
    """Rename directories named 'landing' to 'index' (bottom-up walk)."""
    for root, dirs, _ in os.walk(target_dir, topdown=False):
        for d in dirs:
            if d == 'landing':
                old_path = os.path.join(root, d)
                new_path = os.path.join(root, 'index')
                os.rename(old_path, new_path)
                print(f"  [Renamed Directory] {old_path} -> {new_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 refactor_landing_to_index.py <input-path>")
        sys.exit(1)

    input_path = os.path.normpath(sys.argv[1])

    if not os.path.exists(input_path):
        print(f"Error: Path '{input_path}' does not exist.")
        sys.exit(1)

    print(f"Processing path: {input_path}\n")

    # Step 1: Update internal references inside HTML and YAML files
    print("--- 1. Updating file contents ---")
    valid_extensions = ('.html', '.yaml', '.yml')
    for root, _, files in os.walk(input_path):
        for file in files:
            if file.endswith(valid_extensions):
                update_file_references(os.path.join(root, file))

    # Step 2: Rename landing.html / landing.yaml files to index.*
    print("\n--- 2. Renaming files ---")
    rename_landing_files(input_path)

    # Step 3: Rename any landing/ directories to index/
    print("\n--- 3. Renaming directories ---")
    rename_landing_dirs(input_path)

    print("\nRefactoring complete.")


if __name__ == '__main__':
    main()
