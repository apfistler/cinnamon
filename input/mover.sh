find . -type f -name '*.html' -print0 |
while IFS= read -r -d '' file; do
    dir=$(dirname "$file")
    name=$(basename "$file" .html)
    newdir="$dir/$name"

    mkdir -p "$newdir"

    mv "$file" "$newdir/$name.html"

    if [ -f "$dir/$name.yaml" ]; then
        mv "$dir/$name.yaml" "$newdir/$name.yaml"
    fi
done
