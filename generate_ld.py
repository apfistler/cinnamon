#!/usr/bin/env python3
import sys
import os
import re
import json
import yaml

def clean_html_tags(text):
    """Strip HTML tags and normalize whitespace for schema-friendly text."""
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', text)
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()

def load_yaml(yaml_path):
    """Safely loads YAML content, gracefully handling missing or empty/NULL files."""
    if os.path.exists(yaml_path):
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else {}
        except Exception as e:
            print(f"Warning: Could not parse YAML at '{yaml_path}': {e}", file=sys.stderr)
    return {}

def extract_html_stub_data(html_path):
    """Extracts headline, body paragraphs, and inline images from the content stub."""
    if not os.path.exists(html_path):
        print(f"Error: HTML stub file '{html_path}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract <h1> title
    h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
    headline = clean_html_tags(h1_match.group(1)) if h1_match else ""

    # Extract image tags
    img_matches = re.findall(r'<img[^>]+src=["\'](.*?)["\']', content, re.IGNORECASE)
    images = [
        img if img.startswith("http") else f"https://www.adamfistler.com{img}" 
        for img in img_matches
    ]

    # Extract text paragraphs
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', content, re.IGNORECASE | re.DOTALL)
    clean_paragraphs = [clean_html_tags(p) for p in paragraphs if clean_html_tags(p)]

    # Use first paragraph as excerpt fallback if description isn't in YAML
    summary = clean_paragraphs[0] if clean_paragraphs else ""
    body_text = " ".join(clean_paragraphs)

    return {
        "headline": headline,
        "images": images,
        "summary": summary,
        "body_text": body_text
    }

def derive_canonical_url(html_stub_path, page_meta_yaml):
    """Derives canonical public URL using YAML 'url' field or path structure."""
    if "url" in page_meta_yaml and page_meta_yaml["url"]:
        url = page_meta_yaml["url"]
        return url if url.startswith("http") else f"https://www.adamfistler.com{url}"

    # Fallback: derive relative path from input directory structure
    match = re.search(r'input/html/(.*)$', html_stub_path)
    rel_path = match.group(1) if match else os.path.relpath(html_stub_path, start=os.getcwd())
    
    if not rel_path.startswith('/'):
        rel_path = '/' + rel_path

    return f"https://www.adamfistler.com{rel_path}"

def resolve_paths(target_input):
    """
    Infers site config, page meta yaml, and html stub from a directory path
    or explicit file input.
    """
    # 1. Site-wide config location
    site_config_path = os.path.expanduser("~/cinnamon/etc/config.yaml")

    # 2. If given a directory path
    if os.path.isdir(target_input):
        dir_path = os.path.normpath(target_input)
        dir_name = os.path.basename(dir_path)

        page_meta_path = os.path.join(dir_path, "yaml")
        html_stub_path = os.path.join(dir_path, f"{dir_name}.html")

        # Fallback check if <dirname>.html isn't found
        if not os.path.exists(html_stub_path):
            candidates = [os.path.join(dir_path, f) for f in os.listdir(dir_path) if f.endswith('.html')]
            if candidates:
                html_stub_path = candidates[0]
            else:
                print(f"Error: No HTML stub file found in directory '{dir_path}'", file=sys.stderr)
                sys.exit(1)

        return site_config_path, page_meta_path, html_stub_path

    # 3. If given an explicit HTML file path
    elif os.path.isfile(target_input) and target_input.endswith('.html'):
        html_stub_path = target_input
        dir_path = os.path.dirname(target_input)
        page_meta_path = os.path.join(dir_path, "yaml")
        return site_config_path, page_meta_path, html_stub_path

    else:
        print(f"Error: Target path '{target_input}' is neither a valid directory nor an HTML file.", file=sys.stderr)
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("\nUsage: ./generate_ld.py <directory_path_or_html_file>", file=sys.stderr)
        print("Example: ./generate_ld.py input/html/articles/hypnosis/10_things_choosing_a_hypnotist/\n", file=sys.stderr)
        sys.exit(1)

    target_input = sys.argv[1]

    # Infer input locations automatically
    site_config_path, page_meta_path, html_stub_path = resolve_paths(target_input)

    # Load data sources
    site_config = load_yaml(site_config_path)
    page_meta = load_yaml(page_meta_path)
    stub_data = extract_html_stub_data(html_stub_path)

    # Precedence: Page Meta YAML > HTML Stub > Site Config Default
    headline = (
        page_meta.get("title") 
        or stub_data["headline"] 
        or site_config.get("title", "Adam Fistler")
    )
    
    description = (
        page_meta.get("description") 
        or stub_data["summary"] 
        or site_config.get("tagline", "")
    )

    canonical_url = derive_canonical_url(html_stub_path, page_meta)
    base_url = "https://www.adamfistler.com"

    # Assemble JSON-LD Graph
    json_ld_graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": f"{canonical_url}#webpage",
                "url": canonical_url,
                "name": headline,
                "description": description,
                "publisher": {
                    "@type": "Organization",
                    "name": site_config.get("name", "Adam Fistler"),
                    "url": base_url,
                    "email": site_config.get("email"),
                    "telephone": site_config.get("phone")
                }
            },
            {
                "@type": "Article",
                "@id": f"{canonical_url}#article",
                "isPartOf": {
                    "@id": f"{canonical_url}#webpage"
                },
                "headline": headline,
                "description": description,
                "articleBody": stub_data["body_text"],
                "image": stub_data["images"],
                "author": {
                    "@type": "Person",
                    "@id": f"{base_url}/#adamfistler",
                    "name": "Adam Fistler, BCH",
                    "jobTitle": "Behavioral Change Consultant & Board Certified Hypnotist",
                    "url": f"{base_url}/adam/index.html",
                    "email": site_config.get("email")
                },
                "publisher": {
                    "@type": "Organization",
                    "name": site_config.get("name", "Adam Fistler"),
                    "url": base_url
                }
            }
        ]
    }

    # Generate output file at <name>-ld.json inside the directory
    base_name, _ = os.path.splitext(html_stub_path)
    output_path = f"{base_name}-ld.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(json_ld_graph, f, indent=2)

    print(f"Generated: {output_path}")

if __name__ == "__main__":
    main()
