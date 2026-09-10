#!/usr/bin/env python3
import sys
import os
import re
import argparse
import subprocess
import shutil

# Configuration
WEBROOT = "/var/www/adamfistler.com/public_html"
SUBSTACK_FLAG_FILENAME = ".substack_published"

def should_generate_ld(target_path, force_ld_flag):
    """
    Returns True if forced via -l flag or if '/article/' or '/articles/'
    is present in the target path.
    """
    if force_ld_flag:
        return True
    
    normalized_path = target_path.lower()
    return "/article/" in normalized_path or "/articles/" in normalized_path

def strip_backticks(file_path):
    """Sanitizes markdown backticks in input files before build."""
    if not os.path.isfile(file_path):
        return
    print(f"  Sanitizing backticks: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        sanitized = content.replace("```", "")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(sanitized)
    except Exception as e:
        print(f"Error sanitizing {file_path}: {e}", file=sys.stderr)
        sys.exit(1)

def run_generate_ld(target_input_path, script_dir):
    """Step 1: Executes generate_ld.py with target_input_path."""
    generate_script = os.path.join(script_dir, "generate_ld.py")
    if os.path.exists(generate_script):
        print(f"--> [1/3] Generating JSON-LD for: {target_input_path}")
        res_gen = subprocess.run([sys.executable, generate_script, target_input_path])
        if res_gen.returncode != 0:
            print(f"Error: generate_ld.py failed (exit code {res_gen.returncode})", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Warning: '{generate_script}' not found. Skipping generation.", file=sys.stderr)

def run_inject_ld(target_input_path, script_dir):
    """Step 3: Executes inject_ld.sh via Bash using the identical input path."""
    inject_script = os.path.join(script_dir, "inject_ld.sh")
    if os.path.exists(inject_script):
        print(f"--> [3/3] Injecting JSON-LD for: {target_input_path}")
        res_inj = subprocess.run(["/usr/bin/env", "bash", inject_script, target_input_path])
        if res_inj.returncode != 0:
            print(f"Error: inject_ld.sh failed (exit code {res_inj.returncode})", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Warning: '{inject_script}' not found. Skipping injection.", file=sys.stderr)

def run_substack_publisher(compiled_output_path, raw_input_path, script_dir):
    """
    Executes pss.py to publish the compiled output file to Substack, 
    provided the publication flag file does not already exist inside raw_input_path.
    Creates the flag file inside raw_input_path only upon a successful exit code (0).
    """
    flag_path = os.path.join(raw_input_path, SUBSTACK_FLAG_FILENAME)
    
    if os.path.exists(flag_path):
        print(f"--> Substack publication flag found at '{flag_path}'. Skipping Substack publishing.")
        return

    pss_script = os.path.join(script_dir, "pss.py")
    if os.path.exists(pss_script):
        print(f"--> Publishing to Substack via pss.py: {compiled_output_path}")
        res_pss = subprocess.run([sys.executable, pss_script, compiled_output_path])
        if res_pss.returncode != 0:
            print(f"Error: pss.py failed (exit code {res_pss.returncode})", file=sys.stderr)
            sys.exit(1)
        
        # Create flag file only on exit code 0
        try:
            with open(flag_path, "w", encoding="utf-8") as f:
                f.write("published\n")
            print(f"--> Substack publication successful. Created flag file: {flag_path}")
        except Exception as e:
            print(f"Warning: Failed to create Substack flag file '{flag_path}': {e}", file=sys.stderr)
    else:
        print(f"Warning: '{pss_script}' not found. Skipping Substack publishing.", file=sys.stderr)

def derive_clean_relative_path(raw_input):
    """
    Strips leading 'input/' AND any leading 'html/' or '/html/' segment.
    Example: 'input/html/articles/hypnosis/10_things' -> 'articles/hypnosis/10_things'
    Example: 'input/hypnosis/about' -> 'hypnosis/about'
    """
    rel = re.sub(r"^input/?", "", raw_input)
    rel = re.sub(r"^html/?", "", rel)
    return rel

def resolve_input_dir(query_path, base_dir="input"):
    """
    Checks if query_path is an exact existing directory.
    If not, performs a top-down partial search starting from base_dir outward.
    Returns the resolved path if found, or exits with an error.
    """
    clean_query = query_path.rstrip("/")
    
    # 1. Direct validation check
    if os.path.isdir(clean_query):
        return clean_query

    print(f"Path '{clean_query}' not directly found. Searching from highest level outward...")

    # Ensure base search directory exists
    if not os.path.exists(base_dir):
        print(f"Error: Base search directory '{base_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    # 2. Top-down traversal (highest-level / shallowest directories evaluated first)
    target_lower = os.path.basename(clean_query).lower()
    
    for root, dirs, _ in os.walk(base_dir, topdown=True):
        # Sort directories alphabetically to maintain deterministic search behavior
        dirs.sort()
        for d in dirs:
            if target_lower in d.lower():
                matched_path = os.path.join(root, d)
                print(f"--> Match found: {matched_path}")
                return matched_path

    # 3. Fail if no direct match or partial match was found
    print(f"Error: Could not resolve input directory for '{query_path}'", file=sys.stderr)
    sys.exit(1)

def main():
    script_dir = os.path.dirname(os.path.realpath(__file__))

    parser = argparse.ArgumentParser(description="Cinnamon 'place' placement and build utility.")
    parser.add_argument("-l", "--generate-ld", action="store_true", help="Force JSON-LD generation and injection")
    parser.add_argument("input_dir", help="Path or partial query to input directory (e.g., input/html/articles/... or 'shack')")

    args, _ = parser.parse_known_args()
    
    # Resolve exact or top-down fuzzy path
    raw_input = resolve_input_dir(args.input_dir)

    # Validation check after resolution
    if not raw_input.startswith("input/"):
        print(f"Error: directory must be inside input/ (got '{raw_input}')", file=sys.stderr)
        sys.exit(1)

    name = os.path.basename(raw_input)
    html_file = os.path.join(raw_input, f"{name}.html")
    yaml_file = os.path.join(raw_input, "yaml")

    # Fallback check if page metadata YAML is named <name>.yaml
    if not os.path.exists(yaml_file):
        alt_yaml = os.path.join(raw_input, f"{name}.yaml")
        if os.path.exists(alt_yaml):
            yaml_file = alt_yaml

    if not os.path.isfile(html_file):
        print(f"Error: expected {html_file}", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(yaml_file):
        print(f"Error: expected {yaml_file}", file=sys.stderr)
        sys.exit(1)

    # 2. Sanitization
    print(f"Processing: {raw_input}")
    print("Sanitizing files...")
    strip_backticks(html_file)
    strip_backticks(yaml_file)

    ld_enabled = should_generate_ld(raw_input, args.generate_ld)

    # Pre-compute relative and compiled output paths so they are available for downstream steps
    clean_relative = derive_clean_relative_path(raw_input)
    compiled_output = os.path.join("output", f"{clean_relative}.html")

    # 3. Pipeline Step 1: Generate JSON-LD Schema
    if ld_enabled:
        run_generate_ld(raw_input, script_dir)
    else:
        print("Skipping JSON-LD generation (no '/article/' in path and -l flag not set).")

    # 4. Pipeline Step 2: Cinnamon Build
    cinnamon_bin = os.path.join(script_dir, "cinnamon.py")
    if not os.path.exists(cinnamon_bin):
        cinnamon_bin = "./cinnamon.py"

    print("--> [2/3] Running Cinnamon...")
    res_cin = subprocess.run([sys.executable, cinnamon_bin, raw_input])
    if res_cin.returncode != 0:
        print("Error: Cinnamon build failed.", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(compiled_output):
        print(f"Error: Compiled output file '{compiled_output}' not found.", file=sys.stderr)
        sys.exit(1)

    # 5. Pipeline Step 3: Inject JSON-LD Schema & Substack Publishing
    if ld_enabled:
        run_inject_ld(raw_input, script_dir)
        run_substack_publisher(compiled_output, raw_input, script_dir)

    # 6. Install to WEBROOT
    dest_file = os.path.join(WEBROOT, f"{clean_relative}.html")

    print("Installing output...")
    os.makedirs(os.path.dirname(dest_file), exist_ok=True)
    shutil.copy2(compiled_output, dest_file)
    os.chmod(dest_file, 0o644)

    print(f"Placed: {dest_file}")

if __name__ == "__main__":
    main()
