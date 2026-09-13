import os
import subprocess
from pathlib import Path
from PIL import Image

def process_images(input_dir, output_dir, realesrgan_path, scale=2):
    """
    Recursively scans input_dir for images, runs them through Real-ESRGAN for AI enhancement,
    and resizes them back to their original dimensions to clean/sharpen older photos.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    
    # Find all images recursively
    image_files = [f for f in input_path.rglob("*") if f.suffix.lower() in valid_extensions]
    
    print(f"Found {len(image_files)} images to process.")
    
    for img_path in image_files:
        # Preserve relative directory structure in output
        relative_path = img_path.relative_to(input_path)
        dest_file_dir = output_path / relative_path.parent
        dest_file_dir.mkdir(parents=True, exist_ok=True)
        
        temp_upscaled = dest_file_dir / f"temp_upscaled{img_path.suffix}"
        final_output = dest_file_dir / img_path.name
        
        try:
            # 1. Get original dimensions
            with Image.open(img_path) as img:
                orig_width, orig_height = img.size
                
            print(f"Processing: {img_path.name} ({orig_width}x{orig_height})")
            
            # 2. Run Real-ESRGAN AI upscaler via command line
            # Command format: realesrgan-ncnn-vulkan -i input -o output -s scale
            cmd = [
                str(realesrgan_path),
                "-i", str(img_path),
                "-o", str(temp_upscaled),
                "-s", str(scale),
                "-n", "realesr-x4plus" # Model choice
            ]
            
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # 3. Resize back to original dimensions using high-quality downsampling (Lanczos)
            # This bakes in the AI artifact removal and sharpening while keeping the exact original size.
            with Image.open(temp_upscaled) as upscaled_img:
                resized_img = upscaled_img.resize((orig_width, orig_height), Image.Resampling.LANCZOS)
                resized_img.save(final_output)
                
            # Clean up temporary upscaled file
            if temp_upscaled.exists():
                os.remove(temp_upscaled)
                
        except Exception as e:
            print(f"Error processing {img_path.name}: {e}")
            if temp_upscaled.exists():
                os.remove(temp_upscaled)

if __name__ == "__main__":
    # Configuration
    INPUT_DIRECTORY = "./old_photos"
    OUTPUT_DIRECTORY = "./cleaned_photos"
    
    # Path to the standalone Real-ESRGAN executable (download from GitHub releases)
    # e.g., "realesrgan-ncnn-vulkan.exe" on Windows or "./realesrgan-ncnn-vulkan" on Mac/Linux
    REALESRGAN_EXECUTABLE = "./realesrgan-ncnn-vulkan" 
    
    process_images(INPUT_DIRECTORY, OUTPUT_DIRECTORY, REALESRGAN_EXECUTABLE, scale=2)
