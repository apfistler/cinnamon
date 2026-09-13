#!/usr/bin/env python3

import os
import sys
import subprocess
import shutil
import re
from bs4 import BeautifulSoup

CINNAMON_DIR = os.path.expanduser("~/cinnamon")
INPUT_BASE_DIR = os.path.join(CINNAMON_DIR, "input")
WEB_DIR = "/var/www/adamfistler.com/public_html"
IMG_DIR = os.path.join(WEB_DIR, "img")
TMP_ARTICLES = "/tmp/articles"

def print_help():
    help_text = """
====================================================================
 ARTICLE ANNOTATION TOOL - HELP & USAGE GUIDE
====================================================================
This script steps through each <h2> subheading of an article, lets you
pick or reference an image, and inserts the appropriate HTML tag 
(<div class="content-img"> or <figure>) directly into the file.

INTERACTIVE PROMPTS & ACTIONS:
--------------------------------------------------------------------
  s         - Skip the current subheading.
  q         - Quit the script immediately.
  h         - Display this help message.
  <num>d    - Delete image #<num> from /tmp/articles (with confirmation).

SHORTHAND SYNTAX FOR INSERTION:
--------------------------------------------------------------------
Combine numbers, tags, orientation, and quotes in any order!

  # : Image number from the list (e.g., 1, 2)
  i : Insert as a simple <div> tag (default)
  f : Insert as a <figure> tag with caption support
  l : Left-align the image (default)
  r : Right-align the image

QUOTED ARGUMENTS:
  - First quoted string: Alt text for the image ("Alt Tag")
  - Second quoted string (if <f> or custom path used): Caption or path
  - Third quoted string (if custom path used): Path to external image

EXAMPLES:
  1il "Close up of Cathy Green"
     -> Uses image #1, <div> tag, left aligned, with alt text.

  2fr "Adam at work" "Reflecting on system architecture"
     -> Uses image #2, <figure> tag, right aligned, with alt 
        text and a figure caption.

  ori "A custom diagram" "/home/user/images/diagram.png"
     -> Uses an external image path not in /tmp/articles, right 
        aligned, with a <div> tag and alt text.

  ocr "Custom figure" "Caption text" "/home/user/images/chart.png"
     -> Uses an external image path, right aligned, <figure> tag,
        alt text, and caption.
====================================================================
"""
    print(help_text)

def debug_print(msg, debug_mode):
    if debug_mode:
        print(f"[DEBUG] {msg}")

def run_cb_script(debug_mode):
    script_path = os.path.join(CINNAMON_DIR, "cp_from_cb.sh")
    if not os.path.exists(script_path):
        script_path = "./cp_from_cb.sh"
    
    debug_print(f"Resolved cp_from_cb.sh path to: {script_path}", debug_mode)
    print("Executing cp_from_cb.sh...")
    try:
        subprocess.run([script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: cp_from_cb.sh failed with exit code {e.returncode}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: cp_from_cb.sh script not found.", file=sys.stderr)
        sys.exit(1)

def resolve_input_dir(query_path, base_dir=INPUT_BASE_DIR, debug_mode=False):
    clean_query = query_path.rstrip("/")
    debug_print(f"Resolving input directory for query: {clean_query}", debug_mode)

    if os.path.isdir(clean_query):
        debug_print(f"Found direct directory match: {clean_query}", debug_mode)
        return clean_query

    print(f"Path '{clean_query}' not directly found. Searching from highest level outward...")

    if not os.path.exists(base_dir):
        print(f"Error: Base search directory '{base_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    target_lower = os.path.basename(clean_query).lower()

    for root, dirs, _ in os.walk(base_dir, topdown=True):
        dirs.sort()
        for d in dirs:
            if target_lower in d.lower():
                matched_path = os.path.join(root, d)
                print(f"--> Match found: {matched_path}")
                return matched_path

    print(f"Error: Could not resolve input directory for '{query_path}'", file=sys.stderr)
    sys.exit(1)

def get_temp_images(debug_mode=False):
    if not os.path.exists(TMP_ARTICLES):
        debug_print(f"Temp articles directory {TMP_ARTICLES} does not exist.", debug_mode)
        return []
    images = sorted([f for f in os.listdir(TMP_ARTICLES) if os.path.isfile(os.path.join(TMP_ARTICLES, f))])
    debug_print(f"Found temp images: {images}", debug_mode)
    return images

def parse_shorthand(user_input, available_images, debug_mode=False):
    user_input = user_input.strip()
    debug_print(f"Parsing user input shorthand: '{user_input}'", debug_mode)
    if user_input in ['s', 'q', 'h']:
        return {'action': user_input}

    quotes = re.findall(r'"([^"]*)"', user_input)
    unquoted = re.sub(r'"[^"]*"', '', user_input).strip()

    delete_match = re.search(r'^(\d+)d$', unquoted)
    if delete_match:
        img_idx = int(delete_match.group(1)) - 1
        return {'action': 'delete', 'index': img_idx}

    num_match = re.search(r'^\d+', unquoted)
    img_idx = int(num_match.group()) - 1 if num_match else None
    
    tag_type = 'f' if 'f' in unquoted else 'i'
    orientation = 'right' if 'r' in unquoted else 'left'

    custom_path = None
    alt_tag = ""
    caption = ""

    if len(quotes) >= 1:
        alt_tag = quotes[0]
    if len(quotes) >= 2:
        if tag_type == 'f' or len(quotes) == 3:
            caption = quotes[1]
        if len(quotes) == 3:
            custom_path = quotes[2]
        elif len(quotes) == 2 and ('/' in quotes[1] or '.' in quotes[1]):
            custom_path = quotes[1]
            caption = ""

    img_source = None
    if custom_path:
        img_source = custom_path
    elif img_idx is not None and 0 <= img_idx < len(available_images):
        img_source = os.path.join(TMP_ARTICLES, available_images[img_idx])

    parsed_result = {
        'action': 'insert',
        'tag_type': tag_type,
        'orientation': orientation,
        'alt': alt_tag,
        'caption': caption,
        'source': img_source,
        'img_name': os.path.basename(img_source) if img_source else None
    }
    debug_print(f"Parsed result: {parsed_result}", debug_mode)
    return parsed_result

def main():
    # Parse command line arguments manually to check for -d flag
    debug_mode = False
    args = []
    for arg in sys.argv[1:]:
        if arg == '-d':
            debug_mode = True
        else:
            args.append(arg)

    if len(args) < 1:
        print("Usage: python annotate_articles.py [-d] <input_container>")
        sys.exit(1)

    query_path = args[0]
    debug_print("Debug mode enabled.", debug_mode)

    run_cb_script(debug_mode)

    resolved_input = resolve_input_dir(query_path, debug_mode=debug_mode)
    name = os.path.basename(resolved_input)
    html_file_path = os.path.join(resolved_input, f"{name}.html")
    debug_print(f"Target HTML file path: {html_file_path}", debug_mode)

    if not os.path.exists(html_file_path):
        print(f"Error: HTML file '{html_file_path}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    h2_tags = soup.find_all('h2')

    if not h2_tags:
        print(f"No <h2> subheadings found in {html_file_path}.")
        sys.exit(0)

    # Compute relative path and strip out 'html' container folder segment
    raw_rel_path = os.path.relpath(resolved_input, INPUT_BASE_DIR)
    path_parts = [p for p in raw_rel_path.split(os.sep) if p != 'html']
    flattened_rel_path = os.path.join(*path_parts) if path_parts else ""

    target_img_dir = os.path.join(IMG_DIR, flattened_rel_path)
    debug_print(f"Target image destination directory (flattened): {target_img_dir}", debug_mode)

    total_h2 = len(h2_tags)
    for idx, h2 in enumerate(h2_tags, 1):
        heading_text = h2.get_text(strip=True)
        
        context_snippets = []
        sibling = h2.find_next_sibling()
        while sibling and sibling.name != 'h2':
            if sibling.name == 'p':
                context_snippets.append(sibling.get_text(strip=True))
            sibling = sibling.find_next_sibling()
        
        context_text = " ".join(context_snippets)
        if len(context_text) > 120:
            context_text = context_text[:117] + "..."

        while True:
            print(f"\n--- Subheading [{idx}/{total_h2}]: {heading_text} ---")
            print(f"  Context snippet: {context_text or '[No paragraph context found]'}")
            
            images = get_temp_images(debug_mode)
            print("  Available images in /tmp/articles:")
            if not images:
                print("    (None)")
            else:
                for img_i, img_name in enumerate(images, 1):
                    print(f"    {img_i}) {img_name}")

            user_choice = input("  Action: [s]kip, [q]uit, [h]elp, or shorthand (e.g., 1il \"Alt\", 2fr \"Alt\" \"Cap\"): ").strip()
            
            parsed = parse_shorthand(user_choice, images, debug_mode)
            
            if parsed['action'] == 'q':
                print("Exiting annotation script.")
                sys.exit(0)
            elif parsed['action'] == 'h':
                print_help()
                continue
            elif parsed['action'] == 's':
                print("Skipping subheading.")
                break
            elif parsed['action'] == 'delete':
                del_idx = parsed['index']
                if 0 <= del_idx < len(images):
                    target_to_del = os.path.join(TMP_ARTICLES, images[del_idx])
                    confirm = input(f"  Confirm deletion of '{images[del_idx]}' from /tmp/articles? [y/N]: ").strip().lower()
                    if confirm == 'y':
                        os.remove(target_to_del)
                        print("  Deleted successfully.")
                continue
            elif parsed['action'] == 'insert':
                if not parsed['source'] or not os.path.exists(parsed['source']):
                    print("  Error: Selected image source does not exist. Try again.")
                    continue
                
                final_img_filename = parsed['img_name']
                dest_img_path = os.path.join(target_img_dir, final_img_filename)

                # Ensure destination directory exists before copying
                if not os.path.exists(target_img_dir):
                    debug_print(f"Destination directory '{target_img_dir}' does not exist. Creating it now...", debug_mode)
                    os.makedirs(target_img_dir, exist_ok=True)
                else:
                    debug_print(f"Destination directory '{target_img_dir}' already exists.", debug_mode)

                debug_print(f"Copying '{parsed['source']}' to '{dest_img_path}'", debug_mode)
                shutil.copy2(parsed['source'], dest_img_path)

                # Fix path calculation to avoid duplicating /img/
                rel_subpath = os.path.relpath(dest_img_path, IMG_DIR).replace(os.sep, '/')
                rel_web_path = f"/img/{rel_subpath}"
                
                orientation = parsed['orientation']
                alt = parsed['alt']
                
                if parsed['tag_type'] == 'f':
                    caption = parsed['caption']
                    new_tag_html = f'''\n\n<figure class="content-img caption {orientation}">
    <img src="{rel_web_path}" alt="{alt}" />
    <figcaption>{caption}</figcaption>
</figure>\n\n'''
                else:
                    new_tag_html = f'''\n<div class="content-img {orientation}">
     <img src="{rel_web_path}" alt="{alt}" />
</div>\n\n'''

                new_soup_fragment = BeautifulSoup(new_tag_html, 'html.parser')
                h2.insert_after(new_soup_fragment)

                with open(html_file_path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))

                print(f"  Successfully inserted annotation and copied image to {target_img_dir}")
                break

    print(f"\nAnnotation complete for {html_file_path}!")

if __name__ == '__main__':
    main()
