#!/usr/bin/env python3

import sys
import yaml

def generate_display_table_links(category, yaml_filepath):
    try:
        with open(yaml_filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: File '{yaml_filepath}' not found.", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}", file=sys.stderr)
        sys.exit(1)

    # Locate the display_table dictionary block
    display_table = data.get('display_table', {})
    if not display_table:
        print("Error: No 'display_table' key found in YAML.", file=sys.stderr)
        sys.exit(1)

    # Cycle through all table identifiers (e.g., 'resources') and their items
    for table_name, items in display_table.items():
        if isinstance(items, list):
            for item in items:
                link = item.get('link', '')
                title = item.get('title', '')
                
                # Format: <p><a href="<url>#<category>" class="area_pages"><title></a></p>
                html_output = f'  <p>\n    <a href="{link}#{category}" class="area_pages">\n      {title}\n    </a>\n  </p>'
                print(html_output)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python generate_links.py <category> <yaml_file>", file=sys.stderr)
        sys.exit(1)

    cat_arg = sys.argv[1]
    file_arg = sys.argv[2]
    
    generate_display_table_links(cat_arg, file_arg)
