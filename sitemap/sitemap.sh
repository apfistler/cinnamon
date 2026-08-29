#!/usr/bin/env bash

# Resolve directory where sitemap.sh is located
SITEMAP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SITE_URL="https://www.adamfistler.com"
OUTPUT_FILE="$w/sitemap.xml"
LOG_FILE="$SITEMAP_DIR/crawl.log"

echo "Crawling $SITE_URL to build sitemap..."

# Crawl site in spider mode (no host directories saved)
wget --spider \
     --recursive \
     --no-host-directories \
     --level=inf \
     --no-verbose \
     --no-parent \
     --output-file="$LOG_FILE" \
     "$SITE_URL"

# Write XML Header
cat <<EOF > "$OUTPUT_FILE"
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
EOF

# Process crawl log:
# 1. Grab URL lines
# 2. Extract column containing URL
# 3. Strip leading "URL:" prefix
# 4. Filter out blank entries and non-http(s) lines
# 5. Exclude static asset extensions
# 6. Sort and deduplicate
# 7. Format clean <url><loc> tags
grep -i 'URL:' "$LOG_FILE" | \
awk '{print $3}' | \
sed 's/^URL://' | \
grep -E '^https?://' | \
grep -E -v '\.(css|js|png|jpg|jpeg|gif|svg|ico|pdf|zip|gz|xml)$' | \
sort -u | \
sed 's/&/&amp;/g' | \
awk '{print "  <url>\n    <loc>" $0 "</loc>\n  </url>"}' >> "$OUTPUT_FILE"

# Write XML Footer
echo '</urlset>' >> "$OUTPUT_FILE"

# Clean up temporary logs and stray wget directories
rm -f "$LOG_FILE"
rm -rf "$SITEMAP_DIR/www.adamfistler.com"
rm -rf css
rm -rf html

echo "Sitemap successfully updated at $OUTPUT_FILE"
