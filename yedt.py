#!/usr/bin/env python3

import os
import sys
import re

def update_yaml_category(target_dir, new_category):
    # Pass flags into re.compile instead of subn
    pattern = re.compile(r'^(\s*category\s*:\s*).*$', re.IGNORECASE | re.MULTILINE)
    
    for dirpath, _, filenames in os.walk(target_dir):
        for filename in filenames:
            if filename.endswith('.yaml'):
                file_path = os.path.join(dirpath, filename)
                print(f"Processing: {file_path}")
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Remove flags from subn call
                    new_content, count = pattern.subn(rf'\g<1>{new_category}', content)
                    
                    if count > 0:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"  -> Updated {count} category line(s).")
                    else:
                        print("  -> No 'category:' line found.")
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 yedt.py <category> <dir>")
        sys.exit(1)
        
    category_arg = sys.argv[1]
    dir_arg = sys.argv[2]
    
    if not os.path.isdir(dir_arg):
        print(f"Error: '{dir_arg}' is not a valid directory.")
        sys.exit(1)
        
    update_yaml_category(dir_arg, category_arg)
