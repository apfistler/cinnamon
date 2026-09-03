#!/usr/bin/env bash

set -euo pipefail

WEB_DIR="/var/www/adamfistler.com/public_html"

if [ -z "${1:-}" ]; then
  echo "Error: Missing input path argument."
  echo "Usage: ./inject_ld.sh <directory_path_or_html_file>"
  exit 1
fi

INPUT_PATH="$1"

# 1. Clean trailing slash
INPUT_PATH="${INPUT_PATH%/}"

# 2. Resolve relative path under input/html/
RELATIVE="${INPUT_PATH}"
RELATIVE="${RELATIVE#input/html/}"
RELATIVE="${RELATIVE#html/}"
RELATIVE="${RELATIVE#input/}"
RELATIVE="${RELATIVE#/}"

# 3. Handle directory vs file target resolution
if [ -d "$INPUT_PATH" ]; then
  DIR_NAME=$(basename "$INPUT_PATH")
  HTML_STUB="${INPUT_PATH}/${DIR_NAME}.html"
  
  if [ ! -f "$HTML_STUB" ]; then
    HTML_STUB=$(find "$INPUT_PATH" -maxdepth 1 -name "*.html" | head -n 1)
  fi
else
  HTML_STUB="$INPUT_PATH"
fi

if [ -z "$HTML_STUB" ] || [ ! -f "$HTML_STUB" ]; then
  echo "Error: Could not locate source HTML stub for '$INPUT_PATH'" >&2
  exit 1
fi

# 4. Locate generated JSON-LD payload (<name>-ld.json)
BASE_NAME="${HTML_STUB%.html}"
JSON_LD_FILE="${BASE_NAME}-ld.json"

if [ ! -f "$JSON_LD_FILE" ]; then
  echo "Error: JSON-LD file not found at '$JSON_LD_FILE'." >&2
  echo "Run generate_ld.py first before injecting." >&2
  exit 1
fi

# 5. Extract <category> and <name> from the last two directory components
# Handles both direct folder paths and file paths
if [ -d "$INPUT_PATH" ]; then
  DIR_PATH="$INPUT_PATH"
else
  DIR_PATH=$(dirname "$INPUT_PATH")
fi

NAME=$(basename "$DIR_PATH")
CATEGORY=$(basename "$(dirname "$DIR_PATH")")

# 6. Copy JSON-LD payload to web root's structured_data directory
TARGET_STRUCTURED_DIR="${WEB_DIR}/structured_data"
TARGET_LD_FILE="${TARGET_STRUCTURED_DIR}/${CATEGORY}_${NAME}-ld.json"

echo "==> Copying JSON-LD payload to '${TARGET_LD_FILE}'..."
mkdir -p "$TARGET_STRUCTURED_DIR"
cp "$JSON_LD_FILE" "$TARGET_LD_FILE"

# 7. Determine Cinnamon output HTML location
CLEAN_REL="${RELATIVE%.html}"
OUTPUT_HTML_FILE="output/${CLEAN_REL}.html"

if [ ! -f "$OUTPUT_HTML_FILE" ]; then
  echo "Error: Target built file not found at '$OUTPUT_HTML_FILE'." >&2
  echo "Ensure Cinnamon has built the output site first." >&2
  exit 1
fi

# 8. Check if JSON-LD script tag is already injected
if grep -q 'application/ld+json' "$OUTPUT_HTML_FILE"; then
  echo "Skipping inline injection: JSON-LD block already present in '$OUTPUT_HTML_FILE'"
  exit 0
fi

# 9. Inject JSON-LD directly into HTML using pure Bash/awk
echo "==> Injecting JSON-LD inline into '$OUTPUT_HTML_FILE'..."

# Create wrapped block in temporary file
TMP_BLOCK=$(mktemp)
echo '<script type="application/ld+json">' > "$TMP_BLOCK"
cat "$JSON_LD_FILE" >> "$TMP_BLOCK"
echo '</script>' >> "$TMP_BLOCK"

TMP_OUT=$(mktemp)

# Insert before </head> ignoring case, or prepend if missing
if grep -qi "</head>" "$OUTPUT_HTML_FILE"; then
  awk -v block_file="$TMP_BLOCK" '
    BEGIN {
      while ((getline line < block_file) > 0) {
        block = block line "\n"
      }
      close(block_file)
      injected = 0
    }
    {
      if (!injected && index(tolower($0), "</head>") > 0) {
        sub(/<\/head>/, block "</head>", $0)
        sub(/<\/HEAD>/, block "</HEAD>", $0)
        injected = 1
      }
      print $0
    }
  ' "$OUTPUT_HTML_FILE" > "$TMP_OUT"
  mv "$TMP_OUT" "$OUTPUT_HTML_FILE"
else
  cat "$TMP_BLOCK" "$OUTPUT_HTML_FILE" > "$TMP_OUT"
  mv "$TMP_OUT" "$OUTPUT_HTML_FILE"
fi

rm -f "$TMP_BLOCK" "$TMP_OUT"
echo "Successfully injected JSON-LD into $OUTPUT_HTML_FILE"
