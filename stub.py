#!/usr/bin/env python3

import sys
from pathlib import Path


cinnamon_dir = Path("/home/apfistler/cinnamon")
input_base_dir = cinnamon_dir / "input/html"
img_dir = Path("/var/www/adamfistler.com/public_html/img")


def create_yaml(yaml_file, name, area):
  content = f"""name: {name}
category: {area}
title: ""
keywords:
"""
  yaml_file.write_text(content)


def main():
  if len(sys.argv) < 3:
    print(f"Usage: {sys.argv[0]} <area> <name> [location]")
    sys.exit(1)

  area = sys.argv[1]
  name = sys.argv[2]
  location = sys.argv[3] if len(sys.argv) > 3 else None

  if location:
    stub_dir = input_base_dir / location / name
  else:
    stub_dir = input_base_dir / area / name

  shared_snippet_dir = input_base_dir / area / "shared_snippet"
  yaml_file = stub_dir / f"{name}.yaml"

  stub_dir.mkdir(parents=True, exist_ok=True)

  if location:
    (img_dir / location).mkdir(parents=True, exist_ok=True)

  snippet_link = stub_dir / "snippet"

  if not snippet_link.exists():
    snippet_link.symlink_to(shared_snippet_dir)

  create_yaml(yaml_file, name, area)

  print(f"Created: {stub_dir}")
  print(f"YAML:    {yaml_file}")
  print(f"Snippet: {snippet_link}")


if __name__ == "__main__":
  main()
