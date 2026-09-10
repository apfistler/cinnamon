#!/usr/bin/env bash

init_env() {
    SITEMAP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    SITE_URL="https://adamfistler.com" 
    WEB_DIR="${w:-/var/www/adamfistler.com/public_html}"
    OUTPUT_FILE="$WEB_DIR/sitemap.xml"
    LOG_FILE="$SITEMAP_DIR/crawl.log"
    echo "smd $SITEMAP_DIR"
}

crawl_site() {
    echo "Crawling $SITE_URL to build sitemap..."
    wget --spider \
         --recursive \
         --no-host-directories \
         --level=inf \
         --execute robots=off \
         --output-file="$LOG_FILE" \
         "$SITE_URL"
}

generate_xml_header() {
    cat <<EOF > "$OUTPUT_FILE"
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
EOF
}

process_logs() {
    # Extract, filter, and sort unique URLs from the log
    urls=$(grep -o -E 'https?://[^[:space:]]+' "$LOG_FILE" | \
           grep -E '^https?://(www\.)?adamfistler\.com' | \
           grep -E -v '\.(css|js|png|jpg|jpeg|gif|svg|ico|pdf|zip|gz|xml|txt)$' | \
           sort -u)

    # Iterate through each URL and verify the physical file exists on disk
    while IFS= read -r url; do
        [ -z "$url" ] && continue

        # Strip protocol and domain to get the relative path (e.g., /about/contact)
        path="${url#https://adamfistler.com}"
        path="${path#https://www.adamfistler.com}"

        # Handle root URL separately
        if [ -z "$path" ] || [ "$path" = "/" ]; then
            local_file="$WEB_DIR/index.html"
        else
            # Remove leading slash for path joining
            clean_path="${path#/}"
            
            # Check potential matching file paths on disk:
            # 1. Exact path match (e.g., folder/index.html or static file)
            # 2. Clean URL mapping (.html extension appended)
            # 3. Directory path with index.html
            if [ -f "$WEB_DIR/$clean_path" ]; then
                local_file="$WEB_DIR/$clean_path"
            elif [ -f "$WEB_DIR/$clean_path.html" ]; then
                local_file="$WEB_DIR/$clean_path.html"
            elif [ -d "$WEB_DIR/$clean_path" ] && [ -f "$WEB_DIR/$clean_path/index.html" ]; then
                local_file="$WEB_DIR/$clean_path/index.html"
            else
                local_file="" # File does not exist locally
            fi
        fi

        # If a valid local file exists, append it to the sitemap
        if [ -n "$local_file" ] && [ -f "$local_file" ]; then
            escaped_url=$(echo "$url" | sed 's/&/&amp;/g')
            echo "  <url>" >> "$OUTPUT_FILE"
            echo "    <loc>$escaped_url</loc>" >> "$OUTPUT_FILE"
            echo "  </url>" >> "$OUTPUT_FILE"
        fi
    done <<< "$urls"
}

generate_xml_footer() {
    echo '</urlset>' >> "$OUTPUT_FILE"
}

cleanup() {
    rm -f "$LOG_FILE"
    rm -rf "$SITEMAP_DIR/www.adamfistler.com"
    rm -rf css
    rm -rf html
    echo "Sitemap successfully updated at $OUTPUT_FILE"
}

main() {
    init_env
    crawl_site
    generate_xml_header
    process_logs
    generate_xml_footer
    cleanup
}

main "$@"
