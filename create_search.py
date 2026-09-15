#!/usr/bin/env python3

import os
import json
from html.parser import HTMLParser

class SimpleHTMLParser(HTMLParser):
    """Lightweight HTML parser to extract title, description, and body text."""
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.title_parts = []
        self.description = ""
        self._in_title = False
        self._skip = False
        self._skip_tags = {'script', 'style', 'nav', 'footer', 'header'}

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == 'title':
            self._in_title = True
        elif tag == 'meta':
            attr_dict = dict(attrs)
            if attr_dict.get('name') == 'description':
                self.description = attr_dict.get('content', '')
        elif tag in self._skip_tags:
            self._skip = True

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == 'title':
            self._in_title = False
        elif tag in self._skip_tags:
            self._skip = False

    def handle_data(self, data):
        if self._in_title:
            self.title_parts.append(data)
        elif not self._skip:
            cleaned = data.strip()
            if cleaned:
                self.text_parts.append(cleaned)

    def get_data(self):
        title = "".join(self.title_parts).strip()
        content = " ".join(self.text_parts)
        return title, self.description, content


def update_search_index_entry(relative_path, output_dir, db_filename="search.json"):
    """
    Reads a single compiled HTML file, removes any old entry for it from the 
    search database, parses the new content, and appends the updated entry.
    """
    # 1. Derive the target HTML path based on your relative structure logic
    relative_stem = os.path.splitext(relative_path)[0]
    
    # If your substack or compiled pages live in a specific subfolder or root:
    # (Adjust path joining here if your output files are nested in 'substack/')
    html_path = os.path.join(output_dir, relative_stem + ".html")

    if not os.path.exists(html_path):
        print(f"Search Index Warning: Compiled HTML not found at {html_path}")
        return

    # 2. Parse the HTML file
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    parser = SimpleHTMLParser()
    parser.feed(html_content)
    title, description, body_text = parser.get_data()

    # 3. Determine the clean public URL path
    web_url = '/' + relative_stem + '.html'
    if web_url.endswith('/index.html'):
        web_url = web_url[:-10] + '/'

    db_path = os.path.join(output_dir, db_filename)

    # 4. Load the existing database JSON file (or start fresh)
    database = []
    if os.path.exists(db_path):
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                database = json.load(f)
        except json.JSONDecodeError:
            database = []

    # 5. Remove any pre-existing entry for this exact URL
    database = [item for item in database if item.get('url') != web_url]

    # 6. Assign an ID (increment from max existing or default to 1)
    new_id = max([item.get('id', 0) for item in database], default=0) + 1

    # 7. Append the fresh entry
    database.append({
        "id": new_id,
        "url": web_url,
        "title": title or os.path.basename(relative_path),
        "description": description,
        "content": body_text
    })

    # 8. Write the updated database back to disk
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(database, f, indent=2)

    print(f"Search index updated for: {web_url}")
