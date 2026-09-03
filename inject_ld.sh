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

# 2. Derive relative path under input/ for output targeting
# Handles both absolute (/home/.../cinnamon/input/...) and relative (input/...)
# Flattens EVERY "html/" segment wherever it occurs, not just a leading one.
RELATIVE="${INPUT_PATH#*input/}"
RELATIVE="${RELATIVE//html\//}"
RELATIVE="${RELATIVE#/}"

# 3. Locate the source HTML stub and directory
if [ -d "$INPUT_PATH" ]; then
  DIR_PATH="$INPUT_PATH"
  DIR_NAME=$(basename "$INPUT_PATH")
  HTML_STUB="${INPUT_PATH}/${DIR_NAME}.html"

  if [ ! -f "$HTML_STUB" ]; then
    HTML_STUB=$(find "$INPUT_PATH" -maxdepth 1 -name "*.html" | head -n 1)
  fi
else
  DIR_PATH=$(dirname "$INPUT_PATH")
  HTML_STUB="$INPUT_PATH"
fi

if [ -z "$HTML_STUB" ] || [ ! -f "$HTML_STUB" ]; then
  echo "Error: Could not locate source HTML stub for '$INPUT_PATH'" >&2
  exit 1
fi

# 4. Locate source JSON-LD payload (<name>-ld.json)
BASE_NAME="${HTML_STUB%.html}"
JSON_LD_FILE="${BASE_NAME}-ld.json"

if [ ! -f "$JSON_LD_FILE" ]; then
  echo "Error: JSON-LD file not found at '$JSON_LD_FILE'." >&2
  echo "Run generate_ld.py first before injecting." >&2
  exit 1
fi

# 5. Extract <category> and <name>
NAME=$(basename "$DIR_PATH")
CATEGORY=$(basename "$(dirname "$DIR_PATH")")

# 6. COPY LOGIC: Copy JSON-LD payload to /js/ (served path referenced by the <script src> tag)
TARGET_STRUCTURED_DIR="${WEB_DIR}/js"
TARGET_LD_FILE="${TARGET_STRUCTURED_DIR}/${CATEGORY}_${NAME}-ld.json"
echo "==> Copying JSON-LD payload to '${TARGET_LD_FILE}'..."
mkdir -p "$TARGET_STRUCTURED_DIR"
cp "$JSON_LD_FILE" "$TARGET_LD_FILE"

# 7. RESOLVE OUTPUT HTML TARGET
CLEAN_REL="${RELATIVE%.html}"
OUTPUT_HTML_FILE="output/${CLEAN_REL}.html"

# Fallback: Check if file is stored as output/.../<name>/<name>.html
if [ ! -f "$OUTPUT_HTML_FILE" ] && [ -f "output/${CLEAN_REL}/${NAME}.html" ]; then
  OUTPUT_HTML_FILE="output/${CLEAN_REL}/${NAME}.html"
fi

# Safety guard — never let an empty/garbage path fall through silently
if [ -z "$OUTPUT_HTML_FILE" ] || [ "$OUTPUT_HTML_FILE" = "output/.html" ]; then
  echo "Error: Could not resolve output HTML path from INPUT_PATH='$INPUT_PATH' (RELATIVE='$RELATIVE')." >&2
  exit 1
fi

echo "--> Target Output File: ${OUTPUT_HTML_FILE}"
if [ ! -f "$OUTPUT_HTML_FILE" ]; then
  echo "Error: Target output HTML file does not exist at '${OUTPUT_HTML_FILE}'." >&2
  echo "Make sure you are running inject_ld.sh from your Cinnamon repository root (where output/ is located)." >&2
  exit 1
fi

# Capture original permissions so temp-file swaps below don't leave the file
# at mktemp's default 600 — mv preserves the SOURCE (temp file) permissions,
# not the destination's, when replacing an existing file.
ORIG_PERMS=$(stat -c '%a' "$OUTPUT_HTML_FILE" 2>/dev/null || stat -f '%Lp' "$OUTPUT_HTML_FILE")

# 7b. CLEANUP: strip stray invalid </meta> closing tags (meta is a void element
# and should never have a closing tag). Runs every time, case-insensitive,
# regardless of whether JSON-LD injection below is skipped.
if grep -qi '</meta>' "$OUTPUT_HTML_FILE"; then
  echo "==> Removing stray </meta> tag(s) from '$OUTPUT_HTML_FILE'..."
  TMP_CLEAN=$(mktemp)
  sed -E 's#</[Mm][Ee][Tt][Aa]>##g' "$OUTPUT_HTML_FILE" > "$TMP_CLEAN"
  mv "$TMP_CLEAN" "$OUTPUT_HTML_FILE"
  chmod "$ORIG_PERMS" "$OUTPUT_HTML_FILE"
fi

# 8. Check if already injected (check for this page's specific src reference)
LD_SRC="/js/${CATEGORY}_${NAME}-ld.json"
if grep -qF "$LD_SRC" "$OUTPUT_HTML_FILE"; then
  echo "Skipping injection: JSON-LD reference already present in '$OUTPUT_HTML_FILE'"
  exit 0
fi

# 9. INJECT LOGIC: Inject a <script src="..."> reference before </head>
# (case-insensitive match, safe against & and \ since we build the line ourselves)
echo "==> Injecting JSON-LD reference into '$OUTPUT_HTML_FILE'..."
INJECT_LINE="<script src=\"${LD_SRC}\" type=\"application/ld+json\"></script>"

TMP_OUT=$(mktemp)
echo "This is the output file its trying to modify: $OUTPUT_HTML_FILE"

if grep -qi "</head>" "$OUTPUT_HTML_FILE"; then
  awk -v inject_line="$INJECT_LINE" '
    {
      if (!injected) {
        lower = tolower($0)
        pos = index(lower, "</head>")
        if (pos > 0) {
          pre  = substr($0, 1, pos - 1)
          post = substr($0, pos)
          printf "%s%s\n%s\n", pre, inject_line, post
          injected = 1
          next
        }
      }
      print $0
    }
  ' "$OUTPUT_HTML_FILE" > "$TMP_OUT"
else
  { echo "$INJECT_LINE"; cat "$OUTPUT_HTML_FILE"; } > "$TMP_OUT"
fi

mv "$TMP_OUT" "$OUTPUT_HTML_FILE"
chmod "$ORIG_PERMS" "$OUTPUT_HTML_FILE"
echo "Successfully injected JSON-LD reference into $OUTPUT_HTML_FILE"
