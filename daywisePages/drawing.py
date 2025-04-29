import os
import random
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from . import utils

def load_daywise_fonts(config_data: dict):
    """Loads fonts specified in the daywise_config."""
    fonts = {}
    font_paths = config_data.get("font_paths", {})
    default_font = ImageFont.load_default()
    
    def get_font(key, size, default_path_key=None):
        path = font_paths.get(key)
        if not path and default_path_key:
             path = font_paths.get(default_path_key) # fallback key
        
        if path:
            try:
                return ImageFont.truetype(path, size)
            except IOError as e:
                print(f"Warning: Font not found at '{path}' for key '{key}': {e}. Using default.")
                return default_font
            except Exception as e:
                 print(f"Warning: Error loading font '{path}' for key '{key}': {e}. Using default.")
                 return default_font
        else:
            print(f"Warning: Font path key '{key}' not found in daywise_config.font_paths. Using default.")
            return default_font

    fonts['NUM'] = get_font("CHALKBOARD", 400)
    fonts['HEADLINE'] = get_font("CORE_NARE", 125)
    fonts['TIME'] = get_font("BUNGEE", 60)
    fonts['ACT'] = get_font("TIMES_BOLD", 85, default_path_key="TIMES") 
    fonts['SUBTITLE'] = get_font("SUBTITLE", 65, default_path_key="TIMES")
    fonts['PLACEHOLDER'] = default_font
    
    return fonts

def draw_hero_section(page: Image.Image, draw: ImageDraw.ImageDraw, day_data: dict, panel_idx: int, config_data: dict):
    """Draws the hero image, number, and title for one day panel."""
    
    fonts = load_daywise_fonts(config_data)
    NUM_FONT = fonts['NUM']
    HEADLINE_FONT = fonts['HEADLINE']
    PLACEHOLDER_FONT = fonts['PLACEHOLDER']

    panel_w = config_data.get("PANEL_W", 1240)
    page_h = config_data.get("PAGE_H", 3508)
    page_bg_color = tuple(config_data.get("PAGE_BG_COLOR", [246, 235, 215]))
    content_top_margin = config_data.get("CONTENT_TOP_MARGIN", 2087)
    gap_width = config_data.get("GAP_WIDTH", 40)
    jag_amplitude = config_data.get("JAG_AMPLITUDE", 10)
    segment_length = config_data.get("SEGMENT_LENGTH", 20)
    hero_text_color = tuple(config_data.get("HERO_OVERLAY_TEXT_COLOR", [246, 235, 215, 220]))
    headline_num_lines = config_data.get("HEADLINE_NUM_LINES", 3)
    headline_spacing_ratio = config_data.get("HEADLINE_LINE_SPACING_RATIO", 1.2)

    x0 = panel_idx * panel_w

    full_hero_path = day_data.get("hero_image")
    hero_img = None

    if full_hero_path and isinstance(full_hero_path, str):
        try:
            hero_img = Image.open(full_hero_path)
        except FileNotFoundError:
             base_path_no_ext, _ = os.path.splitext(full_hero_path)
             for ext in (".png", ".jpeg", ".jpg"):
                 try:
                     alt_path = base_path_no_ext + ext
                     hero_img = Image.open(alt_path)
                     full_hero_path = alt_path
                     break 
                 except FileNotFoundError:
                     continue
             if not hero_img:
                  print(f"Warning: Hero image not found: {full_hero_path}")
        except Exception as e:
             print(f"Error opening hero image {full_hero_path}: {e}")
             hero_img = None
    else:
        print(f"Warning: No valid hero_image path for Day {day_data.get('day')}")

    final_image = None

    if hero_img is None:
        placeholder_img = Image.new("RGB", (panel_w, page_h), (128, 128, 128))
        dph = ImageDraw.Draw(placeholder_img)
        placeholder_text = f"Missing Image\\nDay {day_data.get('day', '?')}"
        if full_hero_path:
             placeholder_text += f"\\n({os.path.basename(full_hero_path)})"
        try:
            _, _, pw, ph = dph.textbbox((0, 0), placeholder_text, font=PLACEHOLDER_FONT, spacing=4)
        except AttributeError:
             pw, ph = dph.textsize(placeholder_text, font=PLACEHOLDER_FONT, spacing=4) # fallback
        dph.text(((panel_w - pw)//2, (page_h - ph)//2), placeholder_text, font=PLACEHOLDER_FONT, fill="white", align="center")
        print(f"Warning: Using placeholder for hero image Day {day_data.get('day', idx+1)}")
        final_image = placeholder_img 

    else:
        orig_w, orig_h = hero_img.size
        scale = panel_w / orig_w
        new_h = int(orig_h * scale)
        final_image_calc = None

        if new_h > page_h:
             # Image is taller than page height after scaling to width
             scale = page_h / orig_h
             new_w_corrected = int(orig_w * scale)
             hero_img_resized = hero_img.resize((new_w_corrected, page_h), Image.Resampling.LANCZOS)
             final_image_calc = Image.new("RGBA", (panel_w, page_h), (0, 0, 0, 0))
             paste_x = (panel_w - new_w_corrected) // 2
             final_image_calc.paste(hero_img_resized, (paste_x, 0), hero_img_resized.split()[-1] if hero_img_resized.mode == 'RGBA' else None)
        else:
             # Image is shorter than page height after scaling to width
             hero_img_resized = hero_img.resize((panel_w, new_h), Image.Resampling.LANCZOS)
             sample_height = max(1, int(new_h * 0.05))
             bottom_strip = hero_img_resized.crop((0, max(0, new_h - sample_height), panel_w, new_h))
             avg_color = page_bg_color
             try:
                stat = np.array(bottom_strip.convert("RGB"))
                if stat.size > 0:
                    avg_color = tuple(np.mean(stat.reshape(-1, 3), axis=0).astype(int))
             except (ImportError, NameError, ValueError):
                 # Fallback if numpy fails
                 try:
                     pixels = list(bottom_strip.convert("RGB").getdata())
                     if pixels:
                         avg_r = sum(p[0] for p in pixels) / len(pixels)
                         avg_g = sum(p[1] for p in pixels) / len(pixels)
                         avg_b = sum(p[2] for p in pixels) / len(pixels)
                         avg_color = (int(avg_r), int(avg_g), int(avg_b))
                 except Exception as avg_e:
                      print(f"Warning: Could not calculate average color: {avg_e}")
                      avg_color = page_bg_color

             gradient_h = page_h - new_h
             if gradient_h > 0:
                 gradient_strip = Image.new("RGB", (1, gradient_h))
                 gradient_draw = ImageDraw.Draw(gradient_strip)
                 start_color = avg_color
                 darken_factor = 0.6
                 end_color = tuple(max(0, int(c * darken_factor)) for c in start_color)
                 for y in range(gradient_h):
                     ratio = y / (gradient_h - 1) if gradient_h > 1 else 0
                     r = int(start_color[0] * (1 - ratio) + end_color[0] * ratio)
                     g = int(start_color[1] * (1 - ratio) + end_color[1] * ratio)
                     b = int(start_color[2] * (1 - ratio) + end_color[2] * ratio)
                     gradient_draw.point((0, y), fill=(r, g, b))
                 full_gradient = gradient_strip.resize((panel_w, gradient_h), Image.Resampling.BILINEAR)
                 base_img = Image.new("RGB", (panel_w, page_h), end_color)
                 base_img.paste(full_gradient, (0, new_h))
                 final_image_calc = base_img
             else:
                 final_image_calc = Image.new("RGB", (panel_w, page_h), avg_color)

             alpha_mask = hero_img_resized.split()[-1] if hero_img_resized.mode == 'RGBA' else None
             if alpha_mask:
                 final_image_calc = final_image_calc.convert('RGBA')
             final_image_calc.paste(hero_img_resized, (0, 0), alpha_mask)

        final_image = final_image_calc

    if final_image is None:
         print(f"Error: final_image processing failed for Day {day_data.get('day')}. Creating fallback BG.")
         final_image = Image.new("RGB", (panel_w, page_h), page_bg_color)

    hero_img_final_rgba = final_image.convert("RGBA")

    mask = Image.new("L", (panel_w, page_h), 0)
    mask_d = ImageDraw.Draw(mask)
    
    jag_config = {
        "JAG_AMPLITUDE": jag_amplitude,
        "SEGMENT_LENGTH": segment_length
    }

    if panel_idx == 0: # Left panel
        x_edge = panel_w - gap_width // 2
        path = utils.generate_jagged_path(x_edge, 0, page_h, jag_config)
        poly = [(0, 0)] + path + [(0, page_h)]
    else: # Right panel
        x_edge = gap_width // 2
        path = utils.generate_jagged_path(x_edge, 0, page_h, jag_config)
        poly = [(panel_w, 0), (panel_w, page_h)] + path[::-1]
    mask_d.polygon(poly, fill=255)

    page.paste(hero_img_final_rgba, (x0, 0), mask)

    num_txt = f"Day {day_data.get('day', '?')}"
    try:
        _, _, tw, th = draw.textbbox((0, 0), num_txt, font=NUM_FONT)
    except AttributeError:
        tw, th = draw.textsize(num_txt, font=NUM_FONT) # fallback
    num_y = int(content_top_margin * 0.05) 
    draw.text((utils.center_x(x0, panel_w, tw), num_y), num_txt, font=NUM_FONT, fill=hero_text_color)

    title = day_data.get("title", "Default Title").upper()
    lines = utils.split_title_into_lines(title, headline_num_lines)
    max_w = 0
    total_h = 0
    line_hs = []
    for i, line in enumerate(lines):
        try:
            _, _, lw, lh = draw.textbbox((0, 0), line, font=HEADLINE_FONT)
        except AttributeError:
            lw, lh = draw.textsize(line, font=HEADLINE_FONT) # fallback
        max_w = max(max_w, lw)
        line_hs.append(lh)
        total_h += lh * (headline_spacing_ratio if i > 0 else 1)

    headline_y_start = int(content_top_margin * 0.75)

    actual_total_h = 0
    for i, lh_actual in enumerate(line_hs):
        actual_total_h += lh_actual * (headline_spacing_ratio if i > 0 else 1)

    start_y = headline_y_start - actual_total_h / 2
    cur_y = start_y

    for i, line in enumerate(lines):
        try:
             _, _, lw, lh_actual = draw.textbbox((0, 0), line, font=HEADLINE_FONT)
        except AttributeError:
             lw, lh_actual = draw.textsize(line, font=HEADLINE_FONT) # fallback
        draw.text((utils.center_x(x0, panel_w, lw), cur_y), line, font=HEADLINE_FONT, fill=hero_text_color)
        cur_y += lh_actual * headline_spacing_ratio 

def draw_activities(draw: ImageDraw.ImageDraw, day_data: dict, panel_idx: int, config_data: dict):
    """Draws the activities list for a single day panel."""
    
    fonts = load_daywise_fonts(config_data)
    TIME_FONT = fonts['TIME']
    ACT_FONT = fonts['ACT']
    SUBTITLE_FONT = fonts['SUBTITLE']
    
    panel_w = config_data.get("PANEL_W", 1240)
    page_h = config_data.get("PAGE_H", 3508)
    timeline_page_margin = config_data.get("TIMELINE_PAGE_MARGIN", 50)
    bottom_margin = config_data.get("BOTTOM_MARGIN", 20)
    time_color = tuple(config_data.get("ACTIVITY_TIME_COLOR", [220, 220, 220]))
    activity_color = tuple(config_data.get("TIMELINE_TEXT_COLOR", [255, 255, 255]))
    subtitle_color = tuple(config_data.get("ACTIVITY_SUBTITLE_COLOR", [235, 230, 220]))
    divider_color = subtitle_color

    schedule = day_data.get("schedule", [])
    if not schedule:
        return

    panel_x_start = panel_idx * panel_w
    effective_margin = timeline_page_margin - 20 
    content_width = panel_w - 2 * effective_margin 
    text_x = panel_x_start + effective_margin
    if panel_idx == 1:
        text_x += 65 # Indent right panel slightly more

    current_y = page_h * 0.53 # Start activities drawing lower down

    # Spacing constants
    time_activity_gap = 12
    activity_line_spacing = 7
    activity_subtitle_gap = 16 
    subtitle_line_spacing = 5 
    item_gap = 90 # Gap between schedule items

    page_bottom_limit = page_h - bottom_margin

    for item_idx, item in enumerate(schedule):
        time_str = utils.to_ampm(item["time"])
        activity_str = item["activity"]
        subtitle_str = item.get("subtitle", "")

        try:
            _, _, time_w, time_h = draw.textbbox((0,0), time_str, font=TIME_FONT)
        except AttributeError:
             time_w, time_h = draw.textsize(time_str, font=TIME_FONT) # fallback
        
        # Check space for Time
        if current_y + time_h > page_bottom_limit:
             print(f"Warning: Out of space for Day {day_data.get('day')} item {item_idx+1} (time)")
             break
             
        draw.text((text_x, current_y), time_str, font=TIME_FONT, fill=time_color)
        current_y += time_h + time_activity_gap

        wrapped_activity = utils.wrap_text(draw, activity_str, ACT_FONT, content_width)
        act_lines_height = 0
        for i, line in enumerate(wrapped_activity):
            try:
                _, _, line_w, line_h = draw.textbbox((0,0), line, font=ACT_FONT)
            except AttributeError:
                 line_w, line_h = draw.textsize(line, font=ACT_FONT) # fallback
            act_lines_height += line_h + (activity_line_spacing if i < len(wrapped_activity) - 1 else 0)

        # Check space for Activity
        if current_y + act_lines_height > page_bottom_limit:
             print(f"Warning: Out of space for Day {day_data.get('day')} item {item_idx+1} (activity)")
             break

        for i, line in enumerate(wrapped_activity):
            try:
                _, _, line_w, line_h = draw.textbbox((0,0), line, font=ACT_FONT)
            except AttributeError:
                 line_w, line_h = draw.textsize(line, font=ACT_FONT) # fallback
            draw.text((text_x, current_y), line, font=ACT_FONT, fill=activity_color)
            current_y += line_h + activity_line_spacing
        if wrapped_activity:
             current_y -= activity_line_spacing # Remove last spacing

        if subtitle_str:
            current_y += activity_subtitle_gap
            wrapped_subtitle = utils.wrap_text(draw, subtitle_str, SUBTITLE_FONT, content_width)
            sub_lines_height = 0
            for i, line in enumerate(wrapped_subtitle):
                try:
                    _, _, line_w, line_h = draw.textbbox((0,0), line, font=SUBTITLE_FONT)
                except AttributeError:
                     line_w, line_h = draw.textsize(line, font=SUBTITLE_FONT) # fallback
                sub_lines_height += line_h + (subtitle_line_spacing if i < len(wrapped_subtitle) - 1 else 0)

            # Check space for Subtitle
            if current_y + sub_lines_height > page_bottom_limit:
                 print(f"Warning: Out of space for Day {day_data.get('day')} item {item_idx+1} (subtitle)")
                 break

            for i, line in enumerate(wrapped_subtitle):
                try:
                    _, _, line_w, line_h = draw.textbbox((0,0), line, font=SUBTITLE_FONT)
                except AttributeError:
                     line_w, line_h = draw.textsize(line, font=SUBTITLE_FONT) # fallback
                draw.text((text_x, current_y), line, font=SUBTITLE_FONT, fill=subtitle_color)
                current_y += line_h + subtitle_line_spacing
            if wrapped_subtitle:
                 current_y -= subtitle_line_spacing # Remove last spacing

        # --- Draw Divider (optional) ---
        divider_top_gap = 15
        divider_y = current_y + divider_top_gap
        
        if divider_y + 5 < page_bottom_limit and item_idx < len(schedule) - 1:
            divider_width = content_width * 0.30
            draw.line([(text_x, divider_y), (text_x + divider_width, divider_y)], fill=divider_color, width=2)
            current_y = divider_y + 25
        else:
            # No divider or not enough space for it + gap
             if current_y + item_gap > page_bottom_limit and item_idx < len(schedule) - 1:
                  print(f"Warning: Out of space for Day {day_data.get('day')} gap after item {item_idx+1}")
                  break 
             current_y += item_gap

# --- Main generation function (if needed for direct execution/testing) --- 
# This assumes a specific structure (2 days) and uses a local config concept
# In the main project, generate_daywise_page in the generator script handles this better.
# def generate_itinerary_page(itinerary_data: dict, output_path: str, config):
#     """Generates a full two-day itinerary page (kept for reference/testing)."""
#     page = Image.new("RGB", (config.PAGE_W, config.PAGE_H), config.PAGE_BG_COLOR)
#     draw = ImageDraw.Draw(page)

#     if len(itinerary_data.get("days", [])) < 2:
#         print("Error: Test data requires at least two days for this old function.")
#         return

#     day1_data = itinerary_data["days"][0]
#     day2_data = itinerary_data["days"][1]

#     draw_hero_section(page, draw, day1_data, 0, config.__dict__) # Pass config as dict if needed
#     draw_hero_section(page, draw, day2_data, 1, config.__dict__)

#     draw_activities(draw, day1_data, 0, config.__dict__)
#     draw_activities(draw, day2_data, 1, config.__dict__)

#     os.makedirs(os.path.dirname(output_path), exist_ok=True)
#     page.save(output_path, quality=config.OUTPUT_QUALITY, dpi=config.OUTPUT_DPI)
#     print(f"Test itinerary page saved to: {output_path}")

# if __name__ == "__main__":
#     # Direct execution example (requires a local config concept or dummy data)
#     # from . import config # Assuming a local config.py for testing
#     # from . import data   # Assuming a local data.py for testing
#     # output_file = os.path.join(config.OUT_DIR, config.OUTPUT_FILENAME)
#     # generate_itinerary_page(data.itinerary_data, output_file, config)
#     pass
