#!/usr/bin/env python3

# Add h_article snippet

import os
import sys

def add_h_article_snippet(root_dir):
    snippet = "<!--SNIPPET h_article -->"
    
    if not os.path.exists(root_dir):
        print(f"Error: Path '{root_dir}' does not exist.")
        return

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dir_name = os.path.basename(dirpath)
        
        # Skip specific directories and hidden folders anywhere in the tree
        if dir_name in ["articles", "snippet", "shared_snippet"] or dir_name.startswith('.'):
            continue
            
        target_filename = f"{dir_name}.html"
        target_file_path = os.path.join(dirpath, target_filename)
        
        if os.path.exists(target_file_path):
            with open(target_file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Avoid duplicate insertion if it's already there
            if snippet not in content:
                with open(target_file_path, "w", encoding="utf-8") as f:
                    f.write(content.rstrip() + "\n" + snippet + "\n")
                print(f"Added snippet to: {target_file_path}")
            else:
                print(f"Snippet already exists in: {target_file_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <path_to_scan>")
        sys.exit(1)
        
    target_directory = sys.argv[1]
    add_h_article_snippet(target_directory)
