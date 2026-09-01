#!/usr/bin/env python3
import sys
from pathlib import Path

BASE_INPUT_DIR = Path("/home/apfistler/cinnamon/input/html")
SNIPPET_BLOCK = "\n<!-- SNIPPET pages -->\n<!-- SNIPPET articles -->\n"

def ensure_symlink(target_dir: Path, shared_snippet_dir: Path) -> None:
    """Ensures a 'snippet' symlink exists inside target_dir pointing to shared_snippet_dir."""
    symlink_path = target_dir / "snippet"
    
    if symlink_path.is_symlink() or symlink_path.exists():
        if symlink_path.resolve() == shared_snippet_dir.resolve():
            return
        symlink_path.unlink()

    symlink_path.symlink_to(shared_snippet_dir, target_is_directory=True)
    print(f"[SYMLINK] Created: {symlink_path} -> {shared_snippet_dir}")

def ensure_symlinks_in_tree(start_dir: Path, shared_snippet_dir: Path) -> None:
    """Ensures a 'snippet' symlink exists in start_dir and every subfolder under it."""
    ensure_symlink(start_dir, shared_snippet_dir)
    for path in start_dir.rglob("*"):
        if path.is_dir() and path.name not in ("shared_snippet", "snippet"):
            # Avoid placing symlinks inside shared_snippet or nested within existing snippet symlinks
            if shared_snippet_dir in path.parents or "snippet" in path.parts:
                continue
            ensure_symlink(path, shared_snippet_dir)

def append_snippets_if_missing(file_path: Path) -> None:
    """Appends the required snippet comments to an HTML file if absent at the end."""
    content = file_path.read_text(encoding="utf-8")
    
    if not content.rstrip().endswith("<!-- SNIPPET articles -->"):
        new_content = content.rstrip() + SNIPPET_BLOCK
        file_path.write_text(new_content, encoding="utf-8")
        print(f"[UPDATED] {file_path}")

def process_html_files(root_dir: Path, shared_snippet_dir: Path) -> None:
    """Recursively traverses HTML files under root_dir, skipping snippet directories."""
    for html_file in root_dir.rglob("*.html"):
        if shared_snippet_dir in html_file.parents or "snippet" in html_file.parts:
            continue
        append_snippets_if_missing(html_file)

def main(category: str, subdir: str = None) -> None:
    category_dir = BASE_INPUT_DIR / category
    shared_snippet_dir = category_dir / "shared_snippet"

    # Optional 2nd param: Target a specific subfolder if passed, otherwise target category_dir
    target_dir = category_dir / subdir if subdir else category_dir

    if not category_dir.exists():
        print(f"Error: Category directory does not exist: {category_dir}", file=sys.stderr)
        sys.exit(1)

    if not target_dir.exists():
        print(f"Error: Target directory does not exist: {target_dir}", file=sys.stderr)
        sys.exit(1)

    # 1. Ensure shared_snippet directory exists at category root
    shared_snippet_dir.mkdir(parents=True, exist_ok=True)

    # 2. Ensure symlink exists inside target_dir and all nested subdirectories
    ensure_symlinks_in_tree(target_dir, shared_snippet_dir)

    # 3. Recursively process HTML files in the target directory
    process_html_files(target_dir, shared_snippet_dir)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_snippets.py <category> [subdir]", file=sys.stderr)
        sys.exit(1)

    cat_arg = sys.argv[1]
    sub_arg = sys.argv[2] if len(sys.argv) > 2 else None

    main(cat_arg, sub_arg)
