#!/usr/bin/env python3
import sys
import re
from pathlib import Path

def process_file(file_path: Path) -> None:
    content = file_path.read_text(encoding="utf-8")
    
    # 1. Remove all existing <!-- ABOUT_AUTHOR --> tags and clean up extra blank lines left behind
    cleaned_content = re.sub(r'<!--\s*ABOUT_AUTHOR\s*-->\n?', '', content)

    # 2. Match the first occurrence of any SNIPPET comment tag
    # Matches patterns like <!-- SNIPPET pages -->, <!-- SNIPPET articles -->, etc.
    snippet_pattern = re.compile(r'(<!--\s*SNIPPET.*?>)', re.IGNORECASE)
    match = snippet_pattern.search(cleaned_content)

    if match:
        # Insert <!-- ABOUT_AUTHOR --> right above the first SNIPPET tag
        start_idx = match.start()
        new_content = (
            cleaned_content[:start_idx] 
            + "<!-- ABOUT_AUTHOR -->\n" 
            + cleaned_content[start_idx:]
        )
        
        if new_content != content:
            file_path.write_text(new_content, encoding="utf-8")
            print(f"[INSERTED] {file_path}")
        else:
            print(f"[NO CHANGE] {file_path}")
    else:
        # If no snippet tags exist at all, write back cleaned content if modifications occurred
        if cleaned_content != content:
            file_path.write_text(cleaned_content, encoding="utf-8")
            print(f"[REMOVED OLD TAGS] {file_path}")
        else:
            print(f"[SKIPPED - NO SNIPPET TAG] {file_path}")


def scan_and_process(target_dir: Path) -> None:
    if not target_dir.exists() or not target_dir.is_dir():
        print(f"Error: Directory '{target_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    for html_file in target_dir.rglob("*.html"):
        # Skip shared_snippet and snippet symlink directories
        if "shared_snippet" in html_file.parts or "snippet" in html_file.parts:
            continue
        process_file(html_file)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_about_author.py /path/to/target_directory", file=sys.stderr)
        sys.exit(1)

    target_path = Path(sys.argv[1]).resolve()
    scan_and_process(target_path)
