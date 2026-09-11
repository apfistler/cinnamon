#!/usr/bin/env python3
"""
CLI tool to annotate HTML articles with Gemini-assisted image suggestions, 
optional instructions.txt context, free image generation, chafa terminal previews, 
and saving directly to the web root: /var/www/adamfistler.com/annotated/<reference_to_input>/
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from bs4 import BeautifulSoup, Tag
from google import genai
from google.genai import types
from PIL import Image
import io

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
        dirs.sort()
        for d in dirs:
            if target_lower in d.lower():
                matched_path = os.path.join(root, d)
                print(f"--> Match found: {matched_path}")
                return matched_path

    # 3. Fail if no direct match or partial match was found
    print(f"Error: Could not resolve input directory for '{query_path}'", file=sys.stderr)
    sys.exit(1)

def preview_image_in_terminal(image_path):
    """Renders an image preview in the SSH terminal using chafa."""
    try:
        subprocess.run(["chafa", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print("\n  [Terminal Image Preview (chafa)]:")
        subprocess.run(["chafa", "-s", "80x30", str(image_path)])
        print()
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n  [Note] 'chafa' is not installed. Run: sudo apt install chafa")
        print(f"  Image saved at: {image_path}\n")

def main():
    parser = argparse.ArgumentParser(description="Annotate HTML articles with Gemini AI and generated images.")
    parser.add_argument("input_dir", type=str, help="Path or partial name to the input article directory")
    args = parser.parse_args()

    # Initialize Gemini Client (reads GEMINI_API_KEY environment variable)
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        print("Run: export GEMINI_API_KEY='your_key' before executing.", file=sys.stderr)
        sys.exit(1)
    
    client = genai.Client(api_key=api_key)

    # Resolve input directory using custom search logic
    resolved_str = resolve_input_dir(args.input_dir, base_dir="input")
    input_path = Path(resolved_str).resolve()

    last_level = input_path.name
    html_filename = f"{last_level}.html"
    html_path = input_path / html_filename

    if not html_path.exists():
        html_files = list(input_path.glob("*.html"))
        if not html_files:
            print(f"Error: Could not find {html_filename} or any .html file in {input_path}", file=sys.stderr)
            sys.exit(1)
        html_path = html_files[0]

    print(f"Processing article: {html_path}")

    # Check for instructions.txt in the input folder
    instructions_file = input_path / "instructions.txt"
    global_instructions = ""
    if instructions_file.exists():
        try:
            with open(instructions_file, "r", encoding="utf-8") as f:
                global_instructions = f.read().strip()
            print(f"  [Info] Loaded instructions from {instructions_file.name}")
        except Exception as e:
            print(f"  [Note] Could not read instructions.txt: {e}")

    # Resolve output structure under web root: /var/www/adamfistler.com/annotated/
    web_base = Path("/var/www/adamfistler.com/annotated")
    try:
        parts = input_path.parts
        if len(parts) >= 2:
            reference_to_input = Path(*parts[-2:])
        else:
            reference_to_input = Path(last_level)
    except Exception:
        reference_to_input = Path(last_level)

    output_dir = web_base / reference_to_input
    img_output_dir = output_dir / "img"
    
    try:
        img_output_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        print(f"Error: Permission denied writing to {output_dir}. Ensure you have write access or run with appropriate permissions.", file=sys.stderr)
        sys.exit(1)

    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    subheadings = soup.find_all(["h2", "h3"])
    print(f"Found {len(subheadings)} subheadings in {html_path.name}.\n")

    alignment_toggle = True  # True = right, False = left

    for idx, heading in enumerate(subheadings):
        heading_text = heading.get_text(strip=True)
        print(f"\n==========================================")
        print(f"Subheading [{idx+1}/{len(subheadings)}]: {heading_text}")
        print(f"==========================================")

        # Check if an image already exists anywhere in the section before the next heading
        has_image = False
        for sibling in heading.next_siblings:
            if isinstance(sibling, Tag) and sibling.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                break
            if isinstance(sibling, Tag) and (sibling.name == "img" or sibling.find("img")):
                has_image = True
                break

        if has_image:
            print("  [Skipped] Image already present in this section.\n")
            continue

        # Gather surrounding context for the section
        context_snippets = []
        for sibling in heading.next_siblings:
            if isinstance(sibling, Tag) and sibling.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                break
            if hasattr(sibling, "get_text"):
                txt = sibling.get_text(strip=True)
                if txt:
                    context_snippets.append(txt)
        context_text = " ".join(context_snippets[:5])

        print("  Consulting Gemini for image concept suggestion...")
        
        # Build prompt incorporating instructions.txt if available
        prompt_text = "I am writing a web article.\n"
        if global_instructions:
            prompt_text += f"Overarching style/project instructions: '{global_instructions}'\n\n"
        
        prompt_text += (
            f"Under the subheading '{heading_text}', the context is: '{context_text}'. "
            f"Suggest a clean, conceptual vector illustration or diagram that would visually anchor this section, "
            f"adhering strictly to any provided project instructions. Keep your suggestion concise."
        )
        
        try:
            chat_response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt_text,
            )
            ai_suggestion = chat_response.text.strip()
        except Exception as e:
            ai_suggestion = f"Illustration representing {heading_text}"
            print(f"  [Note] Error reaching text model: {e}")

        print(f"\n  [Gemini Suggestion]:\n  {ai_suggestion}\n")
        
        choice = input("  Action: [s]kip, [c]reate image via AI & insert, [d]iscuss/tweak prompt, [q]uit? [s/c/d/q]: ").strip().lower()
        
        if choice == 'q':
            print("Exiting.")
            break
        elif choice == 's':
            print("  Skipping section.\n")
            continue
        
        image_prompt = ai_suggestion
        while choice == 'd':
            custom_tweak = input("  Enter your adjustment or chat instruction for the image prompt: ").strip()
            if not custom_tweak:
                break
            
            refining_prompt = f"Based on previous concept '{image_prompt}', apply this adjustment: {custom_tweak}. Output only the final refined visual description for an image generator."
            ref_resp = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=refining_prompt,
            )
            image_prompt = ref_resp.text.strip()
            print(f"\n  [Updated Image Prompt]:\n  {image_prompt}\n")
            
            choice = input("  Action: [s]kip, [c]reate image & insert, [d]iscuss further, [q]uit? [s/c/d/q]: ").strip().lower()
            if choice == 'q':
                sys.exit(0)
            elif choice == 's':
                break

        if choice == 's':
            continue

        if choice == 'c':
            img_filename = input("  Enter output image filename (e.g., behavior.png): ").strip()
            if not img_filename:
                img_filename = f"section_{idx+1}.png"
            
            use_caption = input("  Use figure with caption? (y/N): ").strip().lower() == 'y'
            alt_text = input(f"  Enter alt text [{heading_text}]: ").strip()
            if not alt_text:
                alt_text = heading_text

            print("  Generating image via Gemini Free Tier (gemini-3.1-flash-image)...")
            try:
                img_response = client.models.generate_content(
                    model="gemini-3.1-flash-image",
                    contents=f"Create a clean technical or editorial vector illustration for a web article: {image_prompt}",
                    config=types.GenerateContentConfig(
                        response_modalities=["TEXT", "IMAGE"],
                    ),
                )
                
                saved_successfully = False
                target_img_path = img_output_dir / img_filename
                for part in img_response.candidates[0].content.parts:
                    if part.inline_data is not None:
                        image_data = part.inline_data.data
                        image = Image.open(io.BytesIO(image_data))
                        image.save(target_img_path)
                        print(f"  [Success] Image saved to {target_img_path}")
                        saved_successfully = True
                        break
                
                if not saved_successfully:
                    print("  [Error] Model response did not contain image data. Skipping insertion.\n")
                    continue

                preview_image_in_terminal(target_img_path)

            except Exception as e:
                print(f"  [Error] Failed to generate image: {e}\n")
                continue

            commit_choice = input("  Keep this image and insert into HTML? ([y]/n): ").strip().lower()
            if commit_choice == 'n':
                print("  Discarded insertion for this section.\n")
                if target_img_path.exists():
                    target_img_path.unlink()
                continue

            align = "right" if alignment_toggle else "left"
            alignment_toggle = not alignment_toggle

            web_img_path = f"/annotated/{reference_to_input.as_posix()}/img/{img_filename}"

            if use_caption:
                caption_text = input(f"  Enter caption [{heading_text}]: ").strip()
                if not caption_text:
                    caption_text = heading_text
                
                fig_tag = soup.new_tag("figure", **{"class": f"content-img caption {align}"})
                img_tag = soup.new_tag("img", src=web_img_path, alt=alt_text)
                figcaption_tag = soup.new_tag("figcaption")
                figcaption_tag.string = caption_text
                fig_tag.append(img_tag)
                fig_tag.append(figcaption_tag)
                insert_node = fig_tag
            else:
                div_tag = soup.new_tag("div", **{"class": f"content-img {align}"})
                img_tag = soup.new_tag("img", src=web_img_path, alt=alt_text)
                div_tag.append(img_tag)
                insert_node = div_tag

            heading.insert_after(insert_node)
            print("  [Saved] Layout inserted into article HTML tree.\n")

    output_html_path = output_dir / html_path.name
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(str(soup))

    print(f"\nProcessing complete! Annotated HTML saved to: {output_html_path}")
    print(f"View it live in your browser at: https://adamfistler.com/annotated/{reference_to_input.as_posix()}/{html_path.name}")

if __name__ == "__main__":
    main()
