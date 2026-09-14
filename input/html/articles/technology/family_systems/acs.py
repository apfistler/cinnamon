#!/usr/bin/env python3

# add comment section

import os

def add_comments_snippet(root_dir):
    snippet = "<!-- SNIPPET comments -->"
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Target leaf directories (directories with no subdirectories)
        if not dirnames:
            leaf_name = os.path.basename(dirpath)
            
            # Skip if the leaf directory is named "articles"
            if leaf_name == "articles":
                continue
                
            target_filename = f"{leaf_name}.html"
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
            else:
                print(f"Not found: {target_file_path}")

if __name__ == "__main__":
    target_directory = "input/html"
    add_comments_snippet(target_directory)
