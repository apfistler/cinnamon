#!/usr/bin/env python3

import subprocess
from pathlib import Path

def convert_pngs_to_avif(base_dir):
    base_path = Path(base_dir)
    if not base_path.exists():
        print(f"Error: Directory {base_dir} does not exist.")
        return

    # Find all PNG files recursively across all subdirectories (case-insensitive)
    png_files = [p for p in base_path.rglob("*") if p.suffix.lower() == '.png']
    total = len(png_files)

    if total == 0:
        print(f"No PNG files found in {base_dir}")
        return

    print(f"Found {total} total PNG file(s). Starting conversion...\n")

    for idx, png_path in enumerate(png_files, 1):
        avif_path = png_path.with_suffix(".avif")
        
        print(f"[{idx}/{total}] Converting: {png_path}")
        
        try:
            # Run avifenc with quality set to 60 (adjust -q if desired, range 0-100)
            subprocess.run(
                ["avifenc", "-q", "60", str(png_path), str(avif_path)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError as e:
            print(f"  -> Failed to convert {png_path.name}: {e}")
        except FileNotFoundError:
            print("\nError: 'avifenc' tool not found. Make sure libavif-bin is installed.")
            break

    print("\nBatch conversion complete! Both formats are stored side by side.")

if __name__ == "__main__":
    TARGET_DIR = "/var/www/adamfistler.com/public_html/img"
    convert_pngs_to_avif(TARGET_DIR)
