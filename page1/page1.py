# v3 Refactored Page 1 Generator
from PIL import Image, ImageDraw, ImageFont, ImageOps
import os
import urllib.request
import ssl
import io 

# Default config, will be merged with JSON data
DEFAULT_CONFIG = {
    "page_size_px": (2480, 3508), # A4 @ 300 DPI
    "dpi": 300,
    "paths": {
        "input_dir": "inputs",
        "output_dir": "outputs",
        "logo": "inputs/sena_logo_transparent.png", # Default logo path
        "title_font": "fonts/papyrus.ttf",
        "text_font": "/System/Library/Fonts/Optima.ttc", # Consider a cross-platform default
    },
    "text_content": { 
        "title1": "YOUR",
        "title2": "TITLE",
        "dates": "JAN 1 - JAN 10, 2025",
        "prep": "Prepared for  ",
        "name": "Client Name"
    },
    "fonts": {
        "title_size": 220,
        "dates_size": 85,
        "prep_size": 85,
        "name_size": 150
    },
    "layout": {
        "text_start_y": 200,
        "padding_title_lines": 80,
        "padding_below_title": 180,
        "padding_below_dates": 180,
        "padding_below_prep_name": 100,
        "prep_name_manual_v_offset": 65,
        "prep_name_y": 3000 # Y position for "Prepared for Name" line
    },
    "styles": {
        "logo_width": 200,
        "logo_opacity": 0.70,
        "overlay_color": (0, 0, 0, 80),
        "text_fill": "white",
        "text_shadow_color": "grey",
        "text_shadow_offset": (3, 3),
        "jpeg_quality": 95
    }
}

def load_and_fit(path_or_url, size):
    """Open image (local path or URL), convert to RGB, and fill-crop to size."""
    try:
        if path_or_url.startswith("http"):
            # Disable SSL verification for potential self-signed certs - use cautiously
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(path_or_url, context=ctx) as r:
                img = Image.open(io.BytesIO(r.read())).convert("RGB")
        else:
            img = Image.open(os.path.expanduser(path_or_url)).convert("RGB")
        # Fill-crop to target size
        return ImageOps.fit(img, size, Image.LANCZOS, centering=(0.5, 0.5))
    except FileNotFoundError:
        print(f"  -> ❌ Error: File not found: {path_or_url}")
        return None
    except Exception as e:
        print(f"  -> ❌ Error loading/processing image {path_or_url}: {e}")
        return None

def load_fonts(config_data: dict):
    """Load required fonts based on config."""
    try:
        fonts = {
            'title': ImageFont.truetype(config_data["paths"]["title_font"], config_data["fonts"]["title_size"]),
            'dates': ImageFont.truetype(config_data["paths"]["text_font"], config_data["fonts"]["dates_size"]),
            'prep': ImageFont.truetype(config_data["paths"]["text_font"], config_data["fonts"]["prep_size"]),
            'name': ImageFont.truetype(config_data["paths"]["title_font"], config_data["fonts"]["name_size"])
        }
        return fonts
    except IOError as e:
        print(f"Error loading font: {e}")
        print("Ensure font paths in 'page1_config.paths' are correct.")
        return None
    except KeyError as e:
        print(f"Error accessing font config key: {e}")
        print("Ensure 'page1_config' has correct 'paths' and 'fonts' structure.")
        return None

def find_image_path(base_path):
    """Tries to find image with .png, .jpg, or .jpeg extension."""
    if os.path.exists(base_path):
        return base_path
    
    root, _ = os.path.splitext(base_path)
    for ext in [".png", ".jpg", ".jpeg"]:
        img_path = root + ext
        if os.path.exists(img_path):
            return img_path
    return None

def load_process_logo(config_data: dict):
    """Load, resize, and apply opacity to the logo based on config."""
    found_logo_path = None
    try:
        logo_base_path = config_data["paths"]["logo"]
        found_logo_path = find_image_path(logo_base_path)
        
        if not found_logo_path:
            print(f"⚠️ Logo file not found near {logo_base_path}. Skipping logo.")
            return None, 0, 0

        logo_img = Image.open(found_logo_path).convert("RGBA")
        
        logo_width_target = config_data["styles"]["logo_width"]
        ratio = logo_width_target / logo_img.width
        logo_height_actual = int(logo_img.height * ratio)
        logo_width_actual = logo_width_target
        
        logo_img.thumbnail((logo_width_actual, logo_height_actual), Image.LANCZOS)

        opacity_factor = config_data["styles"]["logo_opacity"]
        if logo_img.mode == 'RGBA' and 0.0 <= opacity_factor < 1.0:
            alpha = logo_img.getchannel('A')
            alpha = alpha.point(lambda p: int(p * opacity_factor))
            logo_img.putalpha(alpha)
        
        return logo_img, logo_width_actual, logo_height_actual

    except FileNotFoundError:
        print(f"⚠️ Logo file not found at {found_logo_path or logo_base_path}. Skipping logo.")
        return None, 0, 0
    except KeyError as e:
        print(f"Error accessing logo config key: {e}")
        print("Ensure 'page1_config' has 'paths.logo' and 'styles.logo_width/logo_opacity'.")
        return None, 0, 0
    except Exception as e:
        print(f"⚠️ Error processing logo: {e}. Skipping logo.")
        return None, 0, 0

def generate_page1(output_filename: str, config_data: dict):
    """Generates the cover page using 'inputs/page1_bg.<ext>' and config."""
    # Merge provided config with defaults (deep merge might be better if needed)
    current_config = DEFAULT_CONFIG.copy()
    # Simple update for now, assuming flat structure or controlled overrides
    for key, value in config_data.items():
        if isinstance(value, dict) and key in current_config and isinstance(current_config[key], dict):
             current_config[key].update(value)
        else:
             current_config[key] = value

    inputs_dir = current_config.get("paths", {}).get("input_dir", "inputs")
    expected_bg_base = os.path.join(inputs_dir, "page1_bg")
    page1_bg_path = find_image_path(expected_bg_base)

    if not page1_bg_path:
        print(f"❌ Error: Background image 'page1_bg.<ext>' not found in '{inputs_dir}'.")
        return

    output_dir = current_config.get("paths", {}).get("output_dir", "outputs")
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        print(f"Error creating output directory '{output_dir}': {e}")
        return

    fonts = load_fonts(current_config)
    if not fonts:
        return

    logo_img, logo_width_actual, logo_height_actual = load_process_logo(current_config)

    page_width, page_height = current_config["page_size_px"]
    output_path = os.path.join(output_dir, output_filename)

    print(f"Processing background {page1_bg_path} -> {output_path}...")

    bg = load_and_fit(page1_bg_path, current_config["page_size_px"])
    if not bg:
        print(f"Failed to load background image: {page1_bg_path}")
        return

    bg = bg.convert('RGBA')

    # --- Calculate Text Geometry ---
    text_start_y = current_config["layout"]["text_start_y"]
    pad_title = current_config["layout"]["padding_title_lines"]
    pad_below_title = current_config["layout"]["padding_below_title"]
    pad_below_dates = current_config["layout"]["padding_below_dates"]
    prep_v_offset = current_config["layout"]["prep_name_manual_v_offset"]
    prep_name_y = current_config["layout"].get("prep_name_y", page_height - 300)

    temp_draw = ImageDraw.Draw(Image.new('RGBA', (1,1)))

    y = text_start_y
    bbox1 = temp_draw.textbbox((0, y), current_config["text_content"]["title1"], font=fonts['title'])
    h1 = bbox1[3] - bbox1[1]
    y += h1 + pad_title

    bbox2 = temp_draw.textbbox((0, y), current_config["text_content"]["title2"], font=fonts['title'])
    h2 = bbox2[3] - bbox2[1]
    y += h2 + pad_below_title

    bbox3 = temp_draw.textbbox((0, y), current_config["text_content"]["dates"], font=fonts['dates'])
    # h3 = bbox3[3] - bbox3[1]
    # y_prep_name calculated using direct config value `prep_name_y` below

    prep_text = current_config["text_content"]["prep"]
    name_text = current_config["text_content"]["name"]

    # Measure prep and name for combined centering
    try:
        _, _, prep_w, prep_h = temp_draw.textbbox((0, 0), prep_text, font=fonts['prep'])
        _, _, name_w, name_h = temp_draw.textbbox((0, 0), name_text, font=fonts['name'])
    except AttributeError: # Fallback for older Pillow versions
        prep_w, prep_h = temp_draw.textsize(prep_text, font=fonts['prep'])
        name_w, name_h = temp_draw.textsize(name_text, font=fonts['name'])

    # --- Create Final Image --- 
    final_image = Image.new('RGBA', (page_width, page_height), (0,0,0,0))
    final_image.paste(bg, (0,0))

    # --- Overlay --- 
    overlay_color_value = current_config["styles"]["overlay_color"]
    # Ensure the color is a tuple, as JSON loads it as a list
    overlay = Image.new('RGBA', final_image.size, tuple(overlay_color_value) if isinstance(overlay_color_value, list) else overlay_color_value)
    final_image = Image.alpha_composite(final_image, overlay)

    draw = ImageDraw.Draw(final_image)

    # --- Draw Text --- 
    def draw_centered_with_shadow(y_pos, text, font):
        shadow_offset = current_config["styles"]["text_shadow_offset"]
        shadow_color = current_config["styles"]["text_shadow_color"]
        text_fill = current_config["styles"]["text_fill"]
        try:
             _, _, txt_w, _ = draw.textbbox((0, 0), text, font=font)
        except AttributeError:
             txt_w, _ = draw.textsize(text, font=font)
        x_pos = (page_width - txt_w) / 2
        # Draw shadow first
        draw.text((x_pos + shadow_offset[0], y_pos + shadow_offset[1]), text, font=font, fill=shadow_color)
        # Draw main text
        draw.text((x_pos, y_pos), text, font=font, fill=text_fill)
        return y_pos + _ # Return bottom y

    y = text_start_y
    y = draw_centered_with_shadow(y, current_config["text_content"]["title1"], fonts['title']) 
    y += pad_title
    y = draw_centered_with_shadow(y, current_config["text_content"]["title2"], fonts['title'])
    y += pad_below_title
    y = draw_centered_with_shadow(y, current_config["text_content"]["dates"], fonts['dates'])
    # y += pad_below_dates # No longer needed as prep/name uses direct Y

    # Draw "Prepared for" and "Name" centered together at the specified Y
    total_prep_name_w = prep_w + name_w # Simple sum, assumes no special spacing needed
    start_x = (page_width - total_prep_name_w) / 2
    y_prep = prep_name_y + prep_v_offset # Use direct Y + offset
    y_name = prep_name_y # Use direct Y 

    # Draw shadow first
    shadow_offset = current_config["styles"]["text_shadow_offset"]
    shadow_color = current_config["styles"]["text_shadow_color"]
    text_fill = current_config["styles"]["text_fill"]
    draw.text((start_x + shadow_offset[0], y_prep + shadow_offset[1]), prep_text, font=fonts['prep'], fill=shadow_color)
    draw.text((start_x + prep_w + shadow_offset[0], y_name + shadow_offset[1]), name_text, font=fonts['name'], fill=shadow_color)
    # Draw text
    draw.text((start_x, y_prep), prep_text, font=fonts['prep'], fill=text_fill)
    draw.text((start_x + prep_w, y_name), name_text, font=fonts['name'], fill=text_fill)

    # --- Place Logo --- 
    if logo_img:
        logo_x = (page_width - logo_width_actual) // 2
        logo_y = page_height - logo_height_actual - 100 # 100px padding from bottom
        final_image.paste(logo_img, (logo_x, logo_y), logo_img) 

    # --- Save --- 
    final_image = final_image.convert('RGB')
    final_image.save(
        output_path, 
        "JPEG", 
        quality=current_config["styles"]["jpeg_quality"],
        dpi=(current_config["dpi"], current_config["dpi"])
    )
    print(f"  -> ✅ Saved cover page: {output_path}")

# if __name__ == "__main__":
#     # Example of running directly (if needed for testing)
#     print("Generating page 1 directly...")
#     # Load test config or use defaults
#     test_config = DEFAULT_CONFIG 
#     # You might want to load a specific test JSON here
#     generate_page1(output_filename="page1_direct_test.jpg", config_data=test_config)
