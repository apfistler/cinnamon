#!/usr/bin/env python3
"""
publish_to_substack.py — turn a rendered HTML page (or a plain Markdown
file) into a Substack draft with automated 16:9 solid-white banner formatting
and automatic YAML keyword extraction.
"""

import argparse
import hashlib
import os
import re
import sys
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from bs4.element import NavigableString
from dotenv import load_dotenv
import requests
import yaml

BASE_URL = "https://www.adamfistler.com/"

WEB_ROOT = "/var/www/adamfistler.com/public_html"
SUBSTACK_IMG_SUBDIR = "substack_img"
PUBLIC_IMG_BASE_URL = urljoin(BASE_URL, SUBSTACK_IMG_SUBDIR + "/")

IMAGE_MARKDOWN_RE = re.compile(r'!\[([^\]]*)\]\((\S+?)(?:\s+"([^"]*)")?\)')

# Global debug flag
DEBUG = False

def dbg(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}", file=sys.stderr)


def derive_output_paths(input_filename):
    input_path = os.path.abspath(input_filename)
    output_dir = os.path.abspath("output")
    dbg(f"Deriving output paths for input_path={input_path}, output_dir={output_dir}")

    try:
        relative_path = os.path.relpath(input_path, output_dir)
    except ValueError:
        raise ValueError(f"Input file must be located under '{output_dir}': '{input_filename}'")

    if relative_path == ".." or relative_path.startswith(".." + os.sep):
        raise ValueError(f"Input file must be located under '{output_dir}': '{input_filename}'")

    relative_stem = os.path.splitext(relative_path)[0]
    html_path = os.path.join(output_dir, "substack", relative_stem + ".html")
    md_path = os.path.join(output_dir, "substack", relative_stem + ".md")
    dbg(f"Derived relative_path: {relative_path}, html_path: {html_path}, md_path: {md_path}")
    return html_path, md_path, relative_path


def extract_html_title(soup):
    title_tag = soup.find("title")
    if title_tag is None:
        raise ValueError("No <title> element found in input HTML")

    title = title_tag.get_text(strip=True).split("|", 1)[0].strip()
    if not title:
        raise ValueError("Page title is empty")

    dbg(f"Extracted HTML title: {title}")
    return title


def extract_category(content):
    breadcrumb = content.find("nav", class_="breadcrumb")
    if not breadcrumb:
        dbg("No breadcrumb found for category extraction.")
        return None

    items = breadcrumb.find_all("li", class_="breadcrumb-item")
    if len(items) < 2:
        dbg(f"Breadcrumb items count ({len(items)}) is less than 2.")
        return None

    category_text = items[1].get_text(strip=True)
    category = re.sub(r"\s*articles\b", "", category_text, flags=re.IGNORECASE).strip()
    category = re.sub(r"\s+", "_", category).lower()
    dbg(f"Extracted category: {category} from breadcrumb text: '{category_text}'")
    return category or None


def extract_keywords_from_page_yaml(input_filename):
    """
    Looks up the corresponding page YAML file under input/html/<relative_path_without_ext>/<filename_without_ext>.yaml
    and extracts any entries found under the 'keywords:' key.
    """
    try:
        input_path = Path(input_filename).resolve()
        output_dir = Path("output").resolve()
        
        try:
            relative_path = input_path.relative_to(output_dir)
        except ValueError:
            relative_path = Path(input_filename)

        stem_path = relative_path.with_suffix("")
        yaml_path = Path("input/html") / stem_path / f"{stem_path.name}.yaml"
        
        print(f"[KEYWORD DEBUG] Trying to open page YAML file: {yaml_path.resolve()}", file=sys.stderr)
        print(f"[KEYWORD DEBUG] Does target YAML file exist? {yaml_path.exists()}", file=sys.stderr)

        if yaml_path.exists():
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if isinstance(data, dict):
                keywords = data.get("keywords", [])
                if isinstance(keywords, str):
                    keywords = [kw.strip() for kw in keywords.split(",") if kw.strip()]
                elif isinstance(keywords, list):
                    keywords = [str(kw).strip() for kw in keywords if str(kw).strip()]
                
                print(f"[KEYWORD DEBUG] Successfully extracted keywords: {keywords}", file=sys.stderr)
                return keywords
        else:
            print(f"[KEYWORD DEBUG] Page YAML file not found at {yaml_path.resolve()}", file=sys.stderr)
    except Exception as e:
        print(f"[KEYWORD DEBUG] Error extracting keywords from page YAML: {e}", file=sys.stderr)
    return []


def process_and_ai_upscale_thumbnail(thumbnail_url):
    """
    Downloads the thumbnail, upscales it via Real-ESRGAN or high-grade Lanczos scaling,
    and formats it into a strict 16:9 widescreen banner layout with a clean solid-white 
    background padding so transparent cutouts or odd shapes never create dark/blurry artifacts.
    """
    if not thumbnail_url:
        return None

    try:
        dbg(f"Downloading thumbnail for 16:9 solid-white banner formatting: {thumbnail_url}")
        response = requests.get(thumbnail_url, timeout=20)
        response.raise_for_status()

        from PIL import Image
        image = Image.open(BytesIO(response.content))
        
        try:
            from realesrgan_ncnn_py import Realesrgan
            dbg("Initializing local Real-ESRGAN AI model for crystal-clear upscaling...")
            upscaler = Realesrgan(gpuid=0, model=0)
            image = upscaler.process_pil(image)
            dbg("AI upscaling completed successfully.")
        except (ImportError, Exception) as ai_err:
            dbg(f"Real-ESRGAN package/GPU unavailable ({ai_err}), falling back to intelligent high-res resize.")
            new_width = image.width * 2
            new_height = image.height * 2
            image = image.resize((new_width, new_height), Image.LANCZOS)

        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGBA")

        target_width = 1456
        target_height = 816

        fg_ratio = min(target_width / image.width, target_height / image.height)
        fg_width = int(image.width * fg_ratio)
        fg_height = int(image.height * fg_ratio)
        foreground = image.resize((fg_width, fg_height), Image.LANCZOS)

        background = Image.new("RGB", (target_width, target_height), (255, 255, 255))

        paste_x = (target_width - fg_width) // 2
        paste_y = (target_height - fg_height) // 2

        if foreground.mode == "RGBA":
            background.paste(foreground, (paste_x, paste_y), foreground)
        else:
            background.paste(foreground, (paste_x, paste_y))

        final_banner = background

        relative_path = urlparse(thumbnail_url).path.lstrip("/")
        if not relative_path:
            relative_path = hashlib.sha1(thumbnail_url.encode("utf-8")).hexdigest() + ".jpg"

        ext = os.path.splitext(relative_path)[1].lower()
        if not ext or ext not in (".jpg", ".jpeg", ".png"):
            relative_path += ".jpg"

        disk_path = os.path.join(WEB_ROOT, SUBSTACK_IMG_SUBDIR, "thumbnails", relative_path)
        os.makedirs(os.path.dirname(disk_path), exist_ok=True)
        final_banner.save(disk_path, quality=95)

        public_url = urljoin(PUBLIC_IMG_BASE_URL, f"thumbnails/{relative_path}")
        print(f"Thumbnail processed and formatted to 16:9 white banner -> {public_url}")
        return public_url

    except Exception as error:
        print(f"Warning: Could not format thumbnail banner, using original URL ({error})", file=sys.stderr)
        return thumbnail_url


def extract_thumbnail_from_yaml(relative_path):
    try:
        parts = Path(relative_path).parts
        dbg(f"Extracting thumbnail from YAML for relative path parts: {parts}")
        if len(parts) >= 3 and parts[0] == "articles":
            category = parts[1]
            yaml_path = Path("input/html/articles") / category / "articles/articles.yaml"
            dbg(f"Target category: {category}, checking yaml path: {yaml_path}")
            if yaml_path.exists():
                with open(yaml_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                display_tables = data.get("display_table", {})
                target_relative = relative_path.lstrip("/")
                dbg(f"Target relative URL to match: {target_relative}")
                for table_name, items in display_tables.items():
                    if isinstance(items, list):
                        for item in items:
                            link = item.get("link", "")
                            clean_link = link.split("#")[0].lstrip("/")
                            dbg(f"Comparing item link: '{link}' (cleaned: '{clean_link}') against target: '{target_relative}'")
                            if clean_link == target_relative:
                                img = item.get("image")
                                dbg(f"Match found! Mapped image field: {img}")
                                if img:
                                    resolved_img = urljoin(BASE_URL, img)
                                    dbg(f"Resolved absolute thumbnail URL: {resolved_img}")
                                    return process_and_ai_upscale_thumbnail(resolved_img)
            else:
                dbg(f"YAML path does not exist: {yaml_path}")
    except Exception as e:
        print(f"Warning: Could not extract thumbnail from YAML: {e}", file=sys.stderr)
    dbg("No thumbnail found in YAML matching this route.")
    return None


def make_urls_absolute(content):
    dbg("Making relative links/sources absolute inside content body...")
    count = 0
    for tag in content.find_all(["a", "img", "source", "video", "audio"]):
        attribute = "href" if tag.name == "a" else "src"
        value = tag.get(attribute)

        if not value:
            continue

        if value.startswith(("http://", "https://", "//", "data:", "mailto:", "tel:", "#")):
            continue

        old_val = value
        tag[attribute] = urljoin(BASE_URL, value)
        count += 1
        dbg(f"  Converted {tag.name}[{attribute}]: '{old_val}' -> '{tag[attribute]}'")
    dbg(f"Converted {count} relative URLs to absolute.")


def extract_and_format_nav_sections(content):
    nav_markdown_blocks = []
    
    for section in content.find_all("section"):
        heading = section.find(["h2", "h3"])
        heading_text = heading.get_text(strip=True) if heading else ""
        
        links = section.find_all("a", class_="area_pages") or (heading and "Explore my" in heading_text)
        if links:
            dbg(f"Intercepted navigation/recommendation section: '{heading_text}'")
            
            items = []
            for a in section.find_all("a"):
                href = a.get("href", "")
                if href:
                    absolute_href = urljoin(BASE_URL, href)
                    text = a.get_text(strip=True)
                    items.append((text, absolute_href))
            
            if items:
                block_lines = ["---\n", f"### {heading_text}\n"]
                for text, href in items:
                    block_lines.append(f"- [{text}]({href})")
                nav_markdown_blocks.append("\n".join(block_lines) + "\n")
            
            section.decompose()
            dbg(f"Decomposed and removed intercepted section: '{heading_text}'")
            
    return "\n".join(nav_markdown_blocks)


def clean_content(soup):
    content = soup.find("div", id="content")
    if content is None:
        raise ValueError('No <div id="content"> element found in input HTML')

    category = extract_category(content)

    breadcrumb = content.find("nav", class_="breadcrumb")
    if breadcrumb:
        breadcrumb.decompose()
        dbg("Decomposed breadcrumb nav.")

    footer = content.find("footer", id="footer")
    if footer:
        footer.decompose()
        dbg("Decomposed footer.")

    nav_markdown = extract_and_format_nav_sections(content)

    for section in content.find_all("section"):
        heading = section.find(["h2", "h3"])
        if heading and "Explore my Technology" in heading.get_text():
            section.decompose()
            dbg("Decomposed 'Explore my Technology' section.")

    extracted_subtitle = None
    first_h2 = content.find("h2")
    if first_h2:
        text = first_h2.get_text()
        if any(keyword in text for keyword in ["Author:", "BCH", "Behavorial Change Consultant", "@"]):
            first_h2.decompose()
            dbg(f"Decomposed metadata/author H2: '{text.strip()}'")
        else:
            extracted_subtitle = first_h2.get_text(strip=True)
            first_h2.decompose()
            dbg(f"Extracted subtitle from H2: '{extracted_subtitle}'")

    for h in content.find_all(["h1", "h2"]):
        text = h.get_text()
        if any(keyword in text for keyword in ["Author:", "BCH", "Behavorial Change Consultant", "@"]):
            h.decompose()
            dbg(f"Decomposed redundant metadata block: '{text.strip()}'")
        elif h.name == "h1":
            h.decompose()
            dbg("Decomposed redundant H1 block.")
        elif h.name == "h2":
            h.decompose()
            dbg("Decomposed redundant H2 block.")

    for img_div in content.find_all("div", class_="content-img"):
        img = img_div.find("img")
        if img:
            figure = soup.new_tag("figure", **{"class": "image"})
            figure.append(img.extract())

            alt_text = img.get("alt")
            if alt_text:
                figcaption = soup.new_tag("figcaption")
                figcaption.string = alt_text
                figure.append(figcaption)

            img_div.replace_with(figure)
            dbg(f"Converted content-img div to figure tag with alt: '{alt_text}'")

    while content.contents:
        last = content.contents[-1]
        if getattr(last, "name", None) == "br":
            last.extract()
            continue
        if isinstance(last, NavigableString) and not last.strip():
            last.extract()
            continue
        break

    make_urls_absolute(content)
    return content, category, extracted_subtitle, nav_markdown


def generate_html(content):
    return "".join(str(element) for element in content.contents).strip() + "\n"


def inline_to_markdown(element):
    if isinstance(element, NavigableString):
        return str(element)
    if not getattr(element, "name", None):
        return ""

    tag = element.name
    if tag in ("strong", "b"):
        return "**" + "".join(inline_to_markdown(c) for c in element.children) + "**"
    if tag in ("em", "i"):
        return "*" + "".join(inline_to_markdown(c) for c in element.children) + "*"
    if tag == "code":
        return "`" + element.get_text() + "`"
    if tag == "a":
        text = "".join(inline_to_markdown(c) for c in element.children).strip()
        href = element.get("href", "")
        return f"[{text}]({href})" if href else text
    if tag == "br":
        return "  \n"
    if tag == "img":
        alt = element.get("alt", "").strip()
        src = element.get("src", "").strip()
        return f"![{alt}]({src})" if src else ""
    if tag in ("span", "small", "sub", "sup"):
        return "".join(inline_to_markdown(c) for c in element.children)
    return "".join(inline_to_markdown(c) for c in element.children)


def block_to_markdown(element, list_level=0):
    if isinstance(element, NavigableString):
        return str(element).strip()
    if not getattr(element, "name", None):
        return ""

    tag = element.name
    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        level = int(tag[1])
        text = "".join(inline_to_markdown(c) for c in element.children).strip()
        return "#" * level + " " + text + "\n\n"
    if tag == "p":
        text = "".join(inline_to_markdown(c) for c in element.children).strip()
        return text + "\n\n" if text else ""
    if tag == "blockquote":
        text = "".join(block_to_markdown(c) for c in element.children).strip()
        if not text:
            return ""
        return "".join("> " + line + "\n" for line in text.splitlines()) + "\n"
    if tag == "ul":
        output = ""
        for item in element.find_all("li", recursive=False):
            text = "".join(
                inline_to_markdown(c) for c in item.children if getattr(c, "name", None) not in ("ul", "ol")
            ).strip()
            output += "- " + text + "\n"
            for nested in item.find_all(["ul", "ol"], recursive=False):
                nested_lines = block_to_markdown(nested, list_level + 1).rstrip().splitlines()
                output += "".join("  " + line + "\n" for line in nested_lines)
        return output + "\n"
    if tag == "ol":
        output = ""
        for number, item in enumerate(element.find_all("li", recursive=False), start=1):
            text = "".join(
                inline_to_markdown(c) for c in item.children if getattr(c, "name", None) not in ("ul", "ol")
            ).strip()
            output += f"{number}. {text}\n"
        return output + "\n"
    if tag == "hr":
        return "---\n\n"
    if tag == "img":
        alt = element.get("alt", "").strip()
        src = element.get("src", "").strip()
        if not src:
            return ""
        return f"![{alt}]({src})\n\n"
    if tag == "figure":
        img = element.find("img")
        figcaption = element.find("figcaption")
        if img is not None:
            alt = img.get("alt", "").strip()
            src = img.get("src", "").strip()
            caption = figcaption.get_text(strip=True) if figcaption else ""
            if not src:
                return ""
            if caption:
                return f'![{alt}]({src} "{caption}")\n\n'
            return f"![{alt}]({src})\n\n"
        return "".join(
            block_to_markdown(c) if getattr(c, "name", None) else str(c) for c in element.children
        ) + "\n"

    return "".join(
        block_to_markdown(c, list_level) if getattr(c, "name", None) else str(c) for c in element.children
    )


def generate_markdown(content):
    markdown = "".join(block_to_markdown(element) for element in content.children)
    markdown = re.sub(r"[ \t]+\n", "\n", markdown)
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    return markdown.strip() + "\n"


def convert_html_file(input_filename):
    html_path, md_path, relative_path = derive_output_paths(input_filename)
    source_url = urljoin(BASE_URL, relative_path.replace(os.sep, "/"))

    with open(input_filename, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    title = extract_html_title(soup)
    
    thumbnail_url = extract_thumbnail_from_yaml(relative_path)

    if thumbnail_url:
        content_div = soup.find("div", id="content")
        if content_div:
            first_img = content_div.find("img")
            if first_img:
                old_src = first_img.get("src")
                first_img["src"] = thumbnail_url
                dbg(f"Replaced first image src ('{old_src}') with formatted 16:9 white banner: {thumbnail_url}")

    content, category, extracted_subtitle, nav_markdown = clean_content(soup)

    html_output = generate_html(content)
    markdown_output = generate_markdown(content)
    markdown_output = prepend_source_and_website_header(markdown_output, title, source_url, thumbnail_url)

    if nav_markdown:
        markdown_output = markdown_output.strip() + "\n\n" + nav_markdown

    os.makedirs(os.path.dirname(html_path), exist_ok=True)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_output)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown_output)

    print(f"(also saved local copies: {html_path}, {md_path})")
    print(f"Original Source: {source_url}")
    if thumbnail_url:
        print(f"Thumbnail:      {thumbnail_url}")

    return title, category, extracted_subtitle, thumbnail_url, markdown_output


def scale_down_images(markdown_text, scale):
    from PIL import Image

    def replace(match):
        alt, url, caption = match.group(1), match.group(2), match.group(3)
        if not url.startswith(("http://", "https://")):
            return match.group(0)

        try:
            dbg(f"Downloading image for downscaling: {url}")
            response = requests.get(url, timeout=20)
            response.raise_for_status()

            image = Image.open(BytesIO(response.content))
            new_width = max(1, round(image.width * scale))
            new_height = max(1, round(image.height * scale))
            image = image.resize((new_width, new_height), Image.LANCZOS)

            relative_path = urlparse(url).path.lstrip("/")
            if not relative_path:
                relative_path = hashlib.sha1(url.encode("utf-8")).hexdigest() + ".jpg"

            ext = os.path.splitext(relative_path)[1].lower()
            if not ext:
                relative_path += ".jpg"
                ext = ".jpg"
            if ext in (".jpg", ".jpeg") and image.mode in ("RGBA", "P"):
                image = image.convert("RGB")

            disk_path = os.path.join(WEB_ROOT, SUBSTACK_IMG_SUBDIR, relative_path)
            os.makedirs(os.path.dirname(disk_path), exist_ok=True)
            image.save(disk_path)

            public_url = urljoin(PUBLIC_IMG_BASE_URL, relative_path)
            print(f"  scaled {url} -> {new_width}x{new_height} -> {public_url}")
        except Exception as error:
            print(f"  warning: could not scale {url}, leaving it as-is ({error})", file=sys.stderr)
            return match.group(0)

        if caption:
            return f'![{alt}]({public_url} "{caption}")'
        return f"![{alt}]({public_url})"

    return IMAGE_MARKDOWN_RE.sub(replace, markdown_text)


WEBSITE_LINK_LINE = "Adam Fistler Web Site: [https://www.adamfistler.com](https://www.adamfistler.com)\n\n"

def prepend_source_and_website_header(markdown_text, title, source_url, thumbnail_url=None):
    if thumbnail_url:
        dbg(f"Upscaled thumbnail available for social context: {thumbnail_url}")

    source_line = f"Original Source (Canonical): [{title}]({source_url})\n\n"
    header_block = source_line + WEBSITE_LINK_LINE

    heading_match = re.match(r"^#[^\n]*\n+", markdown_text)
    if heading_match:
        insert_at = heading_match.end()
        return markdown_text[:insert_at] + header_block + markdown_text[insert_at:]

    return header_block + markdown_text

def append_subscribe_cta(markdown_text, publication_url):
    clean_pub_url = publication_url.rstrip("/")
    cleaned_base = markdown_text.strip()
    
    cta_block = (
        "\n\n"
    )
    return cleaned_base + cta_block

def extract_title_subtitle(md_text):
    lines = md_text.lstrip("\n").split("\n")
    title = None
    subtitle = None
    consumed = 0

    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip()
        consumed = 1
        while consumed < len(lines) and lines[consumed].strip() == "":
            consumed += 1
        if consumed < len(lines) and re.match(r"^#{1,2}\s+", lines[consumed]):
            subtitle = re.sub(r"^#{1,2}\s+", "", lines[consumed]).strip()
            consumed += 1

    body = "\n".join(lines[consumed:]).lstrip("\n")
    return title, subtitle, body


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:120]


def main():
    global DEBUG
    parser = argparse.ArgumentParser(description="Create (or publish) a Substack draft from a rendered HTML page or a Markdown file.")
    parser.add_argument("input_file", type=Path, help="Path to the .html page (under ./output/) or a plain .md file")
    parser.add_argument("--title", help="Override the auto-detected title")
    parser.add_argument("--subtitle", help="Override the auto-detected subtitle")
    parser.add_argument("--slug", help="Custom URL slug (default: derived from title)")
    parser.add_argument("--tag", action="append", default=[], help="Add a tag (repeatable); the detected category is added automatically for HTML input")
    parser.add_argument("--publish", action="store_true", help="Publish immediately instead of leaving as an unsent draft")
    parser.add_argument("--send", action="store_true", help="When publishing, also email it to subscribers")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable verbose debug logging")
    parser.add_argument("--env-file", default=".env", help="Path to the .env file with credentials (default: ./.env)")
    parser.add_argument(
        "--image-scale",
        type=float,
        default=1.0,
        help="Scale embedded images by this factor before uploading (e.g. 0.5 for 50%%). "
        "Default: 1 (full size, no scaling).",
    )
    args = parser.parse_args()

    DEBUG = args.debug
    dbg("Debug logging enabled.")

    if not (0 < args.image_scale <= 1):
        sys.exit("--image-scale must be greater than 0 and at most 1.")

    if not args.input_file.exists():
        sys.exit(f"File not found: {args.input_file}")

    load_dotenv(args.env_file)

    publication_url = os.getenv("PUBLICATION_URL")
    if not publication_url:
        sys.exit("PUBLICATION_URL is not set. Add it to your .env file.")
    dbg(f"Target publication URL: {publication_url}")

    from substack import Api

    cookies_string = os.getenv("COOKIES_STRING")
    cookies_path = os.getenv("COOKIES_PATH")
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")

    if cookies_string:
        api = Api(cookies_string=cookies_string, publication_url=publication_url)
    elif cookies_path:
        api = Api(cookies_path=cookies_path, publication_url=publication_url)
    elif email and password:
        api = Api(email=email, password=password, publication_url=publication_url)
    else:
        sys.exit("No credentials found. Set COOKIES_STRING, COOKIES_PATH, or EMAIL+PASSWORD in your .env file.")

    suffix = args.input_file.suffix.lower()
    tags = list(args.tag)
    thumbnail_url = None

    yaml_keywords = extract_keywords_from_page_yaml(str(args.input_file))
    if yaml_keywords:
        for kw in yaml_keywords:
            if kw not in tags:
                tags.append(kw)

    if suffix in (".html", ".htm"):
        try:
            detected_title, category, detected_subtitle, thumbnail_url, body_md = convert_html_file(str(args.input_file))
        except ValueError as error:
            sys.exit(str(error))
        if category and category not in tags:
            tags.insert(0, category)
    else:
        raw_md = args.input_file.read_text(encoding="utf-8")
        detected_title, detected_subtitle, body_md = extract_title_subtitle(raw_md)
        fallback_url = urljoin(BASE_URL, args.input_file.name)
        body_md = prepend_source_and_website_header(body_md, detected_title or "Article", fallback_url)

    title = args.title or detected_title
    subtitle = args.subtitle or detected_subtitle

    if not title:
        sys.exit("No title found and none given with --title.")

    slug = args.slug or slugify(title)

    print(f"Title:     {title}")
    print(f"Subtitle:  {subtitle or '(none)'}")
    print(f"Thumbnail: {thumbnail_url or '(none)'}")
    print(f"Slug:      {slug}")
    print(f"Tags:      {tags or '(none)'}")
    print(f"Mode:      {'publish' if args.publish else 'draft only'}")

    if args.image_scale < 1:
        print(f"Scaling embedded images to {int(args.image_scale * 100)}%...")
        body_md = scale_down_images(body_md, args.image_scale)

    body_md = append_subscribe_cta(body_md, publication_url)

    dbg("Calling Substack API create_draft_from_markdown...")
    try:
        result = api.create_draft_from_markdown(
            title=title,
            subtitle=subtitle,
            markdown=body_md,
            tags=tags,
            slug=slug,
            publish=args.publish,
        )
        dbg(f"Substack API raw result: {result}")
    except Exception as e:
        print(f"Error communicating with Substack API: {e}", file=sys.stderr)
        if DEBUG:
            import traceback
            traceback.print_exc()
        sys.exit(1)

    draft = result.get("draft", result)
    draft_id = draft.get("id")
    print(f"\nDraft created (id={draft_id}).")

    if args.publish:
        print("Published." + (" Sent to subscribers." if args.send else " (web only, not emailed — pass --send to email it)"))
    else:
        print(f"Sitting in your Substack dashboard under Drafts — go to {publication_url}/publish/posts to review before sending.")


if __name__ == "__main__":
    main()
