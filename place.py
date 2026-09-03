#!/usr/bin/env python3
import sys
import os
import re
import argparse
import subprocess
import shutil

# Configuration
WEBROOT = "/var/www/adamfistler.com/public_html"

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

def run_ld_pipeline(abs_target_path, script_dir):
    """Executes generate_ld.py followed by inject_ld.sh."""
    generate_script = os.path.join(script_dir, "generate_ld.py")
    inject_script = os.path.join(script_dir, "inject_ld.sh")

    # Step 1: Generate JSON-LD Schema
    if os.path.exists(generate_script):
        print(f"--> [1/2] Generating JSON-LD for: {abs_target_path}")
        res_gen = subprocess.run([sys.executable, generate_script, abs_target_path])
        if res_gen.returncode != 0:
            print(f"Error: generate_ld.py failed (exit code {res_gen.returncode})", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Warning: '{generate_script}' not found. Skipping generation.", file=sys.stderr)

    # Step 2: Inject JSON-LD
    if os.path.exists(inject_script):
        print(f"--> [2/2] Injecting JSON-LD for: {abs_target_path}")
        res_inj = subprocess.run([sys.executable, inject_script, abs_target_path])
        if res_inj.returncode != 0:
            print(f"Error: inject_ld.py failed (exit code {res_inj.returncode})", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Warning: '{inject_script}' not found. Skipping injection.", file=sys.stderr)

def derive_clean_relative_path(raw_input):
    """
    Strips leading 'input/' AND any leading 'html/' or '/html/' segment.
    Example: 'input/html/articles/hypnosis/10_things' -> 'articles/hypnosis/10_things'
    Example: 'input/hypnosis/about' -> 'hypnosis/about'
    """
    # Remove leading input/ or input
    rel = re.sub(r"^input/?", "", raw_input)
    # Strip html/ if present at start of relative path
    rel = re.sub(r"^html/?", "", rel)
    return rel

def main():
    script_dir = os.path.dirname(os.path.realpath(__file__))

    parser = argparse.ArgumentParser(description="Cinnamon 'place' placement and build utility.")
    parser.add_argument("-l", "--generate-ld", action="store_true", help="Force JSON-LD generation and injection")
    parser.add_argument("input_dir", help="Path to input directory (e.g., input/html/articles/...)")

    args, _ = parser.parse_known_args()
    
    # Clean up input path string
    raw_input = args.input_dir.rstrip("/")
    abs_input = os.path.abspath(raw_input)

    # 1. Validation
    if not raw_input.startswith("input/"):
        print(f"Error: directory must be inside input/ (got '{raw_input}')", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(raw_input):
        print(f"Error: input directory does not exist: {raw_input}", file=sys.stderr)
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
    print("Sanitizing files...")
    strip_backticks(html_file)
    strip_backticks(yaml_file)

    # 3. JSON-LD Pipeline (Conditional / Optional)
    if should_generate_ld(raw_input, args.generate_ld):
        run_ld_pipeline(abs_input, script_dir)
    else:
        print("Skipping JSON-LD pipeline (no '/article/' in path and -l flag not set).")

    # 4. Build (cinnamon.py)
    cinnamon_bin = os.path.join(script_dir, "cinnamon.py")
    if not os.path.exists(cinnamon_bin):
        cinnamon_bin = "./cinnamon.py"

    print("Running Cinnamon...")
    res_cin = subprocess.run([sys.executable, cinnamon_bin, raw_input])
    if res_cin.returncode != 0:
        print("Error: Cinnamon build failed.", file=sys.stderr)
        sys.exit(1)

    # 5. Install to WEBROOT (stripping /html/ segment)
    clean_relative = derive_clean_relative_path(raw_input)
    dest_file = os.path.join(WEBROOT, f"{clean_relative}.html")
    compiled_output = os.path.join("output", f"{clean_relative}.html")

    if not os.path.exists(compiled_output):
        print(f"Error: Compiled output file '{compiled_output}' not found.", file=sys.stderr)
        sys.exit(1)

    print("Installing output...")
    os.makedirs(os.path.dirname(dest_file), exist_ok=True)
    shutil.copy2(compiled_output, dest_file)

    print(f"Placed: {dest_file}")

if __name__ == "__main__":
    main()
