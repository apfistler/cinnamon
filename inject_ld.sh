#!/usr/bin/env bash

set -euo pipefail

WEB_DIR="/var/www/adamfistler.com/public_html"

if [ -z "${1:-}" ]; then
  echo "Error: Missing input path argument."
  exit 1
fi

INPUT_PATH="$1"

# 1. Clean up trailing slash
INPUT_PATH="${INPUT_PATH%/}"

# 2. Extract RELATIVE path (strip 'input/', 'html/', leading slashes)
RELATIVE="${INPUT_PATH#input/}"
RELATIVE="${RELATIVE#html/}"
RELATIVE="${RELATIVE#html}"
RELATIVE="${RELATIVE#/}"

# Example: "groups/upcoming_events"
NAME=$(basename "$RELATIVE")
CATEGORY_DIR=$(dirname "$RELATIVE")

# Flatten category for json filename: "groups_upcoming_events-ld.json"
if [ "$CATEGORY_DIR" = "." ]; then
  JSON_FILENAME="${NAME}-ld.json"
else
  CATEGORY_FLAT=$(echo "$CATEGORY_DIR" | tr '/' '_')
  JSON_FILENAME="${CATEGORY_FLAT}_${NAME}-ld.json"
fi

# The exact path where Cinnamon generated the HTML file
OUTPUT_HTML_FILE="output/${RELATIVE}.html"
JSON_DIR="${WEB_DIR}/structured_data"
JSON_FULL_PATH="${JSON_DIR}/${JSON_FILENAME}"

SCRIPT_TAG="<script type=\"application/ld+json\" src=\"/structured_data/${JSON_FILENAME}\"></script>"

# Create structured_data dir if missing
mkdir -p "$JSON_DIR"

# Generate JSON-LD template if missing
if [ ! -f "$JSON_FULL_PATH" ]; then
  echo "==> Creating structured data file: $JSON_FULL_PATH"
  cat <<EOF > "$JSON_FULL_PATH"
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "WebPage",
      "@id": "https://www.adamfistler.com/${RELATIVE}.html#webpage",
      "url": "https://www.adamfistler.com/${RELATIVE}.html",
      "name": "${NAME}"
    }
  ]
}
EOF
fi

# Inject script tag into the compiled HTML file in output/
if [ -f "$OUTPUT_HTML_FILE" ]; then
  if grep -Fq "$JSON_FILENAME" "$OUTPUT_HTML_FILE"; then
    echo "==> Script tag already exists in $OUTPUT_HTML_FILE"
  else
    echo "==> Injecting script tag into $OUTPUT_HTML_FILE"
    if grep -q "</head>" "$OUTPUT_HTML_FILE"; then
      sed -i "/<\/head>/i \  ${SCRIPT_TAG}" "$OUTPUT_HTML_FILE"
    else
      sed -i "1i ${SCRIPT_TAG}" "$OUTPUT_HTML_FILE"
    fi
  fi
else
  echo "ERROR: Target file not found at: $OUTPUT_HTML_FILE"
  echo "Check where cinnamon.py is outputting the built HTML."
  exit 1
fi
