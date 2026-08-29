#!/usr/bin/env bash

SITE_URL="https://www.adamfistler.com"
SITEMAP_DIR="$(dirname "$0")"
OUTPUT_FILE="$w/sitemap.xml"
LOG_FILE="$SITEMAP_DIR/crawl.log"

# Crawl site without saving host directory tree (-nH)
wget --spider \
     --recursive \
     --no-host-directories \
     --level=inf \
     --no-verbose \
     --no-parent \
     --output-file="$LOG_FILE" \
     "$SITE_URL"

# Build sitemap.xml
cat <<EOF > "$OUTPUT_FILE"
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
EOF

grep -i 'URL:' "$LOG_FILE" | \
awk '{print $3}' | \
grep -E -v '\.(css|js|png|jpg|jpeg|gif|svg|ico|pdf|zip|gz|xml)$' | \
sort -u | \
sed 's/&/&amp;/g' | \
awk '{print "  <url>\n    <loc>" $0 "</loc>\n  </url>"}' >> "$OUTPUT_FILE"

echo '</urlset>' >> "$OUTPUT_FILE"

# Clean up temporary logs and stray crawl folders
rm -f "$LOG_FILE"
rm -rf "$SITEMAP_DIR/www.adamfistler.com"
rm -rf css
rm -rf html
