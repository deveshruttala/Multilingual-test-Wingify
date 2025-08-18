
from PIL import Image, ImageChops, ImageDraw
from pathlib import Path
import numpy as np

def image_diff_percent(img_a_path: str, img_b_path: str, diff_out_path: str) -> float:
    """Calculate image difference percentage and save enhanced diff visualization"""
    
    try:
        # Load images
        a = Image.open(img_a_path).convert("RGBA")
        b = Image.open(img_b_path).convert("RGBA")
        
        # Align sizes if different
        if a.size != b.size:
            b = b.resize(a.size, Image.Resampling.LANCZOS)
        
        # Calculate difference
        diff = ImageChops.difference(a, b)
        
        # Create enhanced diff visualization
        enhanced_diff = create_enhanced_diff(a, b, diff)
        
        # Calculate percentage of changed pixels
        diff_array = np.array(diff)
        changed_pixels = np.any(diff_array[:, :, :3] > 0, axis=2)  # Check RGB channels
        total_pixels = changed_pixels.size
        changed_count = np.sum(changed_pixels)
        percent = (changed_count / total_pixels) if total_pixels > 0 else 0.0
        
        # Save enhanced diff
        Path(diff_out_path).parent.mkdir(parents=True, exist_ok=True)
        enhanced_diff.save(diff_out_path)
        
        return percent
        
    except Exception as e:
        print(f"Error in image diff calculation: {e}")
        return 1.0  # Return 100% diff on error

def create_enhanced_diff(img_a: Image.Image, img_b: Image.Image, diff: Image.Image) -> Image.Image:
    """Create an enhanced diff visualization with highlights"""
    
    # Convert to RGB for better visualization
    img_a_rgb = img_a.convert("RGB")
    img_b_rgb = img_b.convert("RGB")
    diff_rgb = diff.convert("RGB")
    
    # Create a side-by-side comparison
    width, height = img_a_rgb.size
    combined_width = width * 3
    
    # Create combined image
    combined = Image.new("RGB", (combined_width, height), "white")
    draw = ImageDraw.Draw(combined)
    
    # Add images side by side
    combined.paste(img_a_rgb, (0, 0))
    combined.paste(img_b_rgb, (width, 0))
    combined.paste(diff_rgb, (width * 2, 0))
    
    # Add labels
    draw.text((10, 10), "Before", fill="black")
    draw.text((width + 10, 10), "After", fill="black")
    draw.text((width * 2 + 10, 10), "Diff", fill="red")
    
    # Add border lines
    draw.line([(width, 0), (width, height)], fill="gray", width=2)
    draw.line([(width * 2, 0), (width * 2, height)], fill="gray", width=2)
    
    return combined

def create_side_by_side_comparison(img_a_path: str, img_b_path: str, output_path: str):
    """Create a side-by-side comparison of two images"""
    
    try:
        img_a = Image.open(img_a_path).convert("RGB")
        img_b = Image.open(img_b_path).convert("RGB")
        
        # Resize to same size if different
        if img_a.size != img_b.size:
            img_b = img_b.resize(img_a.size, Image.Resampling.LANCZOS)
        
        width, height = img_a.size
        combined_width = width * 2
        
        # Create combined image
        combined = Image.new("RGB", (combined_width, height), "white")
        draw = ImageDraw.Draw(combined)
        
        # Add images side by side
        combined.paste(img_a, (0, 0))
        combined.paste(img_b, (width, 0))
        
        # Add labels
        draw.text((10, 10), "English Version", fill="black")
        draw.text((width + 10, 10), "Japanese Version", fill="black")
        
        # Add border line
        draw.line([(width, 0), (width, height)], fill="gray", width=2)
        
        # Save
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        combined.save(output_path)
        
        print(f"📸 Side-by-side comparison saved: {output_path}")
        
    except Exception as e:
        print(f"Error creating side-by-side comparison: {e}")
