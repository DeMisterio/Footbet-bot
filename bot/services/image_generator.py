import os
import hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

CACHE_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "assets" / "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def generate_vs_image(home_team: str, away_team: str, home_logo_path: str = None, away_logo_path: str = None) -> str:
    """
    Generates a VS graphic and returns the path to the cached image.
    """
    # Create cache key
    cache_key = hashlib.md5(f"{home_team}_{away_team}_{home_logo_path}_{away_logo_path}".encode()).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"{cache_key}.png")
    
    if os.path.exists(cache_path):
        return cache_path
        
    # Image dimensions
    width, height = 800, 400
    
    # White background
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to load default font, fallback to basic
    try:
        font_large = ImageFont.truetype("arial.ttf", 60)
        font_medium = ImageFont.truetype("arial.ttf", 40)
    except IOError:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        
    # Draw VS in center
    vs_text = "VS"
    # Get bounding box for text
    left, top, right, bottom = draw.textbbox((0, 0), vs_text, font=font_large)
    text_w = right - left
    text_h = bottom - top
    draw.text(((width - text_w) / 2, (height - text_h) / 2), vs_text, fill="red", font=font_large)
    
    # Process Home Team (Left)
    if home_logo_path and os.path.exists(home_logo_path):
        try:
            home_logo = Image.open(home_logo_path).convert("RGBA")
            home_logo.thumbnail((250, 250), Image.Resampling.LANCZOS)
            x_offset = int((400 - home_logo.width) / 2)
            y_offset = int((400 - home_logo.height) / 2)
            img.paste(home_logo, (x_offset, y_offset), home_logo)
        except Exception as e:
            draw.text((50, 180), home_team[:15], fill="black", font=font_medium)
    else:
        # Fallback text
        draw.text((50, 180), home_team[:15], fill="black", font=font_medium)
        
    # Process Away Team (Right)
    if away_logo_path and os.path.exists(away_logo_path):
        try:
            away_logo = Image.open(away_logo_path).convert("RGBA")
            away_logo.thumbnail((250, 250), Image.Resampling.LANCZOS)
            x_offset = int(400 + (400 - away_logo.width) / 2)
            y_offset = int((400 - away_logo.height) / 2)
            img.paste(away_logo, (x_offset, y_offset), away_logo)
        except Exception as e:
            draw.text((450, 180), away_team[:15], fill="black", font=font_medium)
    else:
        # Fallback text
        draw.text((450, 180), away_team[:15], fill="black", font=font_medium)
        
    # Save to cache
    img.save(cache_path, "PNG", optimize=True)
    return cache_path
