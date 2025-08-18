
from PIL import Image, ImageChops
from pathlib import Path

def image_diff_percent(img_a_path: str, img_b_path: str, diff_out_path: str) -> float:
    a = Image.open(img_a_path).convert("RGBA")
    b = Image.open(img_b_path).convert("RGBA")
    # Align sizes
    if a.size != b.size:
        b = b.resize(a.size)
    diff = ImageChops.difference(a, b)
    bbox = diff.getbbox()
    if not bbox:
        percent = 0.0
    else:
        # Compute % of changed pixels (any nonzero channel)
        nonzero = 0
        px = diff.load()
        w, h = diff.size
        for y in range(h):
            for x in range(w):
                if px[x, y] != (0, 0, 0, 0):
                    nonzero += 1
        percent = nonzero / float(w * h)
    Path(diff_out_path).parent.mkdir(parents=True, exist_ok=True)
    diff.save(diff_out_path)
    return percent
