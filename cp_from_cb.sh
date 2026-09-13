#!/bin/bash

REMOTE_HOST="l"
REMOTE_DIR="./dl"
LOCAL_DIR="/tmp/articles"

debug_log() {
    echo "[DEBUG] $1"
}

fetch_remote_files() {
    debug_log "Ensuring local directory exists: $LOCAL_DIR"
    mkdir -p "$LOCAL_DIR"

    debug_log "Checking what files matching 'ar_*' currently exist on remote host..."
    remote_check=$(ssh "$REMOTE_HOST" "ls -1 ${REMOTE_DIR}/ar_* 2>/dev/null")
    ssh_status=$?

    # If SSH connection failed completely (e.g. host down, timeout, auth error)
    if [ $ssh_status -eq 255 ]; then
        debug_log "SSH connection failed with exit code 255."
        return 255
    fi

    # If no files matched (ls returns non-zero and output is empty), exit gracefully with 0
    if [ -z "$remote_check" ]; then
        debug_log "No matching 'ar_*' files found on remote host. Exiting gracefully with 0."
        exit 0
    fi

    debug_log "Attempting scp from ${REMOTE_HOST}:${REMOTE_DIR}/ar_* to $LOCAL_DIR/"
    scp "${REMOTE_HOST}:${REMOTE_DIR}/ar_*" "$LOCAL_DIR/"
    local scp_status=$?

    if [ $scp_status -ne 0 ]; then
        debug_log "SCP failed with exit code $scp_status."
        return $scp_status
    fi

    debug_log "SCP successful. Removing source files from remote host..."
    ssh "$REMOTE_HOST" "rm -f ${REMOTE_DIR}/ar_*"
    local ssh_status=$?
    
    if [ $ssh_status -ne 0 ]; then
        debug_log "Warning: Remote file cleanup via SSH exited with code $ssh_status."
    else
        debug_log "Remote files successfully cleaned up."
    fi

    return 0
}

strip_prefixes() {
    debug_log "Navigating to local directory: $LOCAL_DIR"
    cd "$LOCAL_DIR" || { debug_log "Failed to change directory to $LOCAL_DIR"; return 1; }

    debug_log "Looking for downloaded files with 'ar_' prefix..."
    local renamed_count=0
    
    for file in ar_*; do
        [ -f "$file" ] || { debug_log "No files matching 'ar_*' found locally."; break; }
        
        local new_name="${file#ar_}"
        debug_log "Renaming: '$file' -> '$new_name'"
        mv "$file" "$new_name"
        renamed_count=$((renamed_count + 1))
    done
    
    debug_log "Finished stripping prefixes. Total files renamed: $renamed_count"
}

process_images() {
    debug_log "Starting ImageMagick conversion loop..."
    local processed_count=0

    for file in *; do
        [ -f "$file" ] || continue

        local base="${file%.*}"
        local output="${base}.png"

        debug_log "Converting '$file' -> '$output'"
        convert -transparent white -resize 400x "$file" "$output"
        local convert_status=$?

        if [ $convert_status -ne 0 ]; then
            debug_log "Error: ImageMagick failed on '$file' with code $convert_status"
            continue
        fi

        if [ "$file" != "$output" ]; then
            debug_log "Removing original source image: '$file'"
            rm "$file"
        else
            debug_log "Skipping deletion; input and output filenames are identical: '$file'"
        fi
        
        processed_count=$((processed_count + 1))
    done

    debug_log "Image processing complete. Total processed: $processed_count"
}

# Main Execution
debug_log "Script execution started."
if fetch_remote_files; then
    strip_prefixes
    process_images
else
    exit_code=$?
    debug_log "Pipeline aborted due to transfer failure with exit code $exit_code."
    exit $exit_code
fi
debug_log "Script execution completed successfully."
