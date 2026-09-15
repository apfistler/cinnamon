#!/usr/bin/env python3

import os
import sys
import hashlib
from pathlib import Path
import yaml

# Configuration paths
WEB_DIR = Path("/var/www/adamfistler.com/public_html")
MANIFEST_PATH = Path("/var/www/adamfistler.com/asset-manifest.yaml")
APACHE_RULES_PATH = Path("/etc/apache2/conf-available/asset-cache-rules.conf")

# Tracked file extensions
TRACKED_EXTENSIONS = {
    ".js",
    ".css",
    ".png",
    ".jpg",
    ".jpeg",
    ".svg",
    ".webp",
    ".ico",
    ".html",
    ".htm",
}
HTML_EXTENSIONS = {".html", ".htm"}


def calculate_sha256(file_path):
  sha256_hash = hashlib.sha256()
  with open(file_path, "rb") as f:
    for byte_block in iter(lambda: f.read(65536), b""):
      sha256_hash.update(byte_block)
  return sha256_hash.hexdigest()


def main():
  # Enforce root execution
  if os.getuid() != 0:
    print("[-] Error: This script must be run as root.", file=sys.stderr)
    sys.exit(1)

  print("Scanning web directory for files...", flush=True)

  # Load existing manifest
  manifest = {}
  if MANIFEST_PATH.exists():
    with open(MANIFEST_PATH, "r") as f:
      manifest = yaml.safe_load(f) or {}

  # Gather files, explicitly ignoring symlinks to prevent infinite loops
  files_to_process = []
  for file_path in WEB_DIR.rglob("*"):
    if file_path.is_file() and not file_path.is_symlink():
      if file_path.suffix in TRACKED_EXTENSIONS:
        files_to_process.append(file_path)

  total_files = len(files_to_process)
  print(f"Found {total_files} files to process.\n", flush=True)

  new_manifest = {}

  # Build Apache rewrite and header rules structure
  apache_rules = [
      "# Generated Asset Cache-Control & Versioning Rules",
      "<IfModule mod_rewrite.c>",
      "    RewriteEngine On",
  ]

  # Loop through files with index tracking for the requested output format
  for idx, file_path in enumerate(files_to_process, 1):
    rel_path = str(file_path.relative_to(WEB_DIR))
    print(f"[{idx} of {total_files}] Processing: {rel_path}", flush=True)

    current_hash = calculate_sha256(file_path)
    short_hash = current_hash[:8]

    # Check if file exists in old manifest and if hash changed
    if rel_path in manifest and manifest[rel_path]["hash"] == current_hash:
      version_id = manifest[rel_path]["version"]
    else:
      version_id = short_hash

    new_manifest[rel_path] = {
        "hash": current_hash,
        "version": version_id,
    }

    # Generate rewrite rules for version-tracked static assets (skip HTML files)
    if file_path.suffix not in HTML_EXTENSIONS:
      stem = file_path.stem
      suffix = file_path.suffix
      parent = file_path.parent.relative_to(WEB_DIR)
      parent_str = "" if str(parent) == "." else str(parent) + "/"

      # In your cache_control_manifest.py, update virtual/real filename construction to:
      virtual_filename = f"/{parent_str}{stem}.v-{version_id}{suffix}"
      real_filename = f"/{parent_str}{stem}{suffix}"
      
      apache_rules.append(f"    RewriteRule ^{virtual_filename}$ {real_filename} [L]")
      
  apache_rules.extend(["</IfModule>", ""])

  # Add Cache-Control Header rules for Apache (mod_headers required)
  apache_rules.extend([
      "<IfModule mod_headers.c>",
      (
          "    # Static Assets (Images, JS, CSS, Fonts) - 1 year (31536000"
          " seconds)"
      ),
      (
          "    <LocationMatch"
          r' "\.v-[a-f0-9]+\.(js|css|png|jpg|jpeg|svg|webp|ico)$">'
      ),
      '        Header set Cache-Control "public, max-age=31536000, immutable"',
      "    </LocationMatch>",
      "",
      "    # HTML Files - 7 days (604800 seconds)",
      '    <LocationMatch "\\.(html|htm)$">',
      '        Header set Cache-Control "public, max-age=604800"',
      "    </LocationMatch>",
      "</IfModule>",
  ])

  # Write updated YAML manifest
  with open(MANIFEST_PATH, "w") as f:
    yaml.safe_dump(new_manifest, f)

  # Write Apache configuration rules
  APACHE_RULES_PATH.parent.mkdir(parents=True, exist_ok=True)
  with open(APACHE_RULES_PATH, "w") as f:
    f.write("\n".join(apache_rules))

  print(
      f"\nManifest successfully updated: {MANIFEST_PATH}\nApache rules written:"
      f" {APACHE_RULES_PATH}",
      flush=True,
  )


if __name__ == "__main__":
  main()
