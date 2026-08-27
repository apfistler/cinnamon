#!/usr/bin/env python3

import os
import re
import sys
from bs4 import BeautifulSoup
import yaml


class FoldedString(str):
    """Custom str wrapper to force YAML folded block scalar style (>)."""

    pass


def folded_representer(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=">")


yaml.add_representer(FoldedString, folded_representer)


def slugify(text):
    """Converts section titles to clean YAML keys (e.g., 'The Basics' -> 'basics')."""
    text = text.lower().strip()
    text = re.sub(r"^the\s+", "", text)  # Strips leading "the" for cleaner names
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "_", text)


def parse_faq_html(html_file_path):
    if not os.path.exists(html_file_path):
        print(f"Error: File not found at '{html_file_path}'")
        sys.exit(1)

    with open(html_file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    filename = os.path.basename(html_file_path)
    name_attr = filename.replace(".html", "")
    category_attr = name_attr.replace("_faq", "")

    title_el = soup.select_one(".faq-title, h2")
    desc_el = soup.select_one(".faq-description, .faq > p")

    title_text = (
        title_el.get_text(strip=True)
        if title_el
        else f"{category_attr.capitalize()} Frequently Asked Questions"
    )
    desc_text = desc_el.get_text(strip=True) if desc_el else ""

    faq_data = {
        "name": name_attr,
        "category": category_attr,
        "title": title_text,
        "description": desc_text,
        "keywords": [
            f"{category_attr} FAQ",
            f"{category_attr} recovery",
            "behavior change",
            "subconscious habit change",
            "emotional regulation",
        ],
        "topic_areas": [],
    }

    topic_sections = soup.select("section.faq-topic")

    for section in topic_sections:
        section_title_el = section.select_one(
            "h3.faq-topic-title, .faq-topic-title"
        )
        section_title = (
            section_title_el.get_text(strip=True)
            if section_title_el
            else "General"
        )
        topic_name = slugify(section_title)

        topic_obj = {
            "name": topic_name,
            "title": section_title,
            "questions": [],
        }

        faq_items = section.select(".faq-item")
        for item in faq_items:
            question_btn = item.select_one(".faq-question, button")
            if question_btn:
                icon_el = question_btn.select_one(".faq-question-icon")
                if icon_el:
                    icon_el.decompose()
                question_text = question_btn.get_text(strip=True)
            else:
                continue

            answer_div = item.select_one(".faq-answer")
            if answer_div:
                paragraphs = [
                    p.get_text(strip=True)
                    for p in answer_div.find_all("p")
                    if p.get_text(strip=True)
                ]
                raw_answer = "\n\n".join(paragraphs)
                response_text = FoldedString(raw_answer)
            else:
                response_text = FoldedString("")

            topic_obj["questions"].append(
                {"question": question_text, "response": response_text}
            )

        if topic_obj["questions"]:
            faq_data["topic_areas"].append(topic_obj)

    return yaml.dump(faq_data, sort_keys=False, allow_unicode=True, width=80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python html_to_faq_yaml.py <path_to_html_file>")
        sys.exit(1)

    target_path = sys.argv[1]
    print(parse_faq_html(target_path))
