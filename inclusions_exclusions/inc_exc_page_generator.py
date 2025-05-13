import os
import json # Added json import
import textwrap # Added textwrap import
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
import numpy as np # For gradient generation

# --- Constants ---
WIDTH = 2480 # Standard A4 width @ 300 DPI
HEIGHT = 3508

PAGE_BG_COLOR = "#1F1F1F" # Dark background for the page
CARD_MARGIN = 90       # Increased from 60 to significantly reduce card height
CARD_RADIUS = 40       # Corner radius for the card
CARD_BG_COLOR = "#F0F0F0" # Light background for the card itself (subtle)

# Card dimensions derived from page size and margin
CARD_WIDTH = WIDTH - 2 * CARD_MARGIN
CARD_HEIGHT = HEIGHT - 2 * CARD_MARGIN
CARD_X0 = CARD_MARGIN
CARD_Y0 = CARD_MARGIN
CARD_X1 = CARD_X0 + CARD_WIDTH
CARD_Y1 = CARD_Y0 + CARD_HEIGHT
CARD_MID_X = CARD_X0 + CARD_WIDTH // 2

# Half-width of the card content area
HALF_CARD_WIDTH = CARD_WIDTH // 2

COLOR_TEAL_BG = "#356F6A"
# COLOR_TEAL_LINES = "#7DB7B2" # No longer used on teal bg
COLOR_CHARCOAL_TEXT = "#1F1F1F"
COLOR_WHITE_TEXT = "#FFFFFF"
COLOR_BROWN_LINES = "#5C2C28"
COLOR_LEFT_LINES = "#E0E0E0" # Light grey lines for the left (beach) side
GRADIENT_COLOR_START = (251, 113, 133) # #FB7185 in RGB

# Placeholder text (adjust if needed)
TEXT_INCLUDED = "What's Included ✓"
TEXT_NOT_INCLUDED = "What's Not Included ✕"

# Layout constants (relative to card or half-card)
TITLE_FONT_SIZE = 80 # Adjust as needed
TITLE_TOP_MARGIN = 130 # Reduced from 150 to move title block up
LINE_START_Y_OFFSET = 400 # Y offset for first line *within* the card half
LINE_SPACING = 80 # Adjust spacing between lines
LINE_LENGTH = 400 # Adjust length of placeholder lines (relative to half-card width)
LINE_THICKNESS = 4 # Adjust thickness of lines
CARD_BLUR_RADIUS = 45 # Increased from 20 for more pronounced blur
TEXT_SHADOW_COLOR = (0, 0, 0, 128)  # Shadow for white text
TEXT_SHADOW_OFFSET = (3, 3)         # Shadow offset

# New constants for items
ITEM_FONT_SIZE = 90 # Increased font size further
ITEM_LINE_SPACING = 120 # Increased spacing further
COLUMN_PADDING = 70 # Slightly increased padding
DIVIDER_COLOR = (100, 100, 100, 150) # Semi-transparent grey for divider
DIVIDER_THICKNESS = 2
LIST_ICON_SIZE = 65 # Increased size for icons within the list items
LIST_ICON_TEXT_SPACING = 30 # Increased space between list icon and text

# Font paths (add path for item font)
FONT_PATH_PLAYFAIR = 'fonts/PlayfairDisplay-VariableFont_wght.ttf'
FONT_PATH_ITEM = 'fonts/Chalkboard-Regular.ttf' # Updated to use Chalkboard

# Icon paths (assuming they are in an 'icons' folder)
ICON_PATH_TICK = 'icons/tick.webp' 
ICON_PATH_CROSS = 'icons/cross.png'
ICON_SIZE = 100 # Reduced from 200, was 80 before user change
TITLE_ICON_SPACING = 25 
# HEADER_BAND_COLOR = (0, 0, 0, 0) # Removed, header band will not be drawn separately
MAX_ITEM_LINES = 3 

def create_gradient(width, height, start_color, end_alpha=0.0):
    """Creates a vertical linear gradient image."""
    gradient = Image.new('RGBA', (width, height))
    draw = ImageDraw.Draw(gradient)
    start_r, start_g, start_b = start_color
    for y in range(height):
        # Start with 40% opacity (alpha = 102) at the top, fading to transparent
        current_alpha = int(102 * (1 - y / height))
        draw.line([(0, y), (width, y)], fill=(start_r, start_g, start_b, current_alpha))
    return gradient

def generate_inc_exc_page(
    output_filename: str,
    font_path_title: str,
    font_path_item: str, # Added item font path
    bg_image_path: str,
    base_output_dir: str,
    inclusions_list: list, # Added inclusions data
    exclusions_list: list  # Added exclusions data
):
    """Generates the inclusions/exclusions page with the specified card design."""
    output_path = os.path.join(base_output_dir, output_filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # --- Load Assets Early ---
    try:
        font_title = ImageFont.truetype(font_path_title, TITLE_FONT_SIZE)
        font_item = ImageFont.truetype(font_path_item, ITEM_FONT_SIZE) # Load item font
    except IOError as e:
        print(f"Error: Font file not found ({e}). Cannot generate page.")
        # Try loading at least one font if possible, or fallback?
        try: font_title = ImageFont.truetype(font_path_title, TITLE_FONT_SIZE)
        except: font_title = ImageFont.load_default(size=TITLE_FONT_SIZE)
        try: font_item = ImageFont.truetype(font_path_item, ITEM_FONT_SIZE)
        except: font_item = ImageFont.load_default(size=ITEM_FONT_SIZE)
        print("Attempting to use default fonts.")
        # return # Decide if we should exit if fonts fail

    # Load Icons
    tick_icon, cross_icon = None, None
    list_tick_icon, list_cross_icon = None, None # Icons for list items
    try:
        if os.path.exists(ICON_PATH_TICK):
            # Load for title
            tick_icon = Image.open(ICON_PATH_TICK).convert("RGBA")
            tick_icon = tick_icon.resize((ICON_SIZE, ICON_SIZE), Image.Resampling.LANCZOS)
            # Load for list items
            list_tick_icon = Image.open(ICON_PATH_TICK).convert("RGBA")
            list_tick_icon = list_tick_icon.resize((LIST_ICON_SIZE, LIST_ICON_SIZE), Image.Resampling.LANCZOS)
        else:
            print(f"Warning: Tick icon not found at {ICON_PATH_TICK}")
    except Exception as e:
        print(f"Error loading tick icon: {e}")

    try:
        if os.path.exists(ICON_PATH_CROSS):
            # Load for title
            cross_icon = Image.open(ICON_PATH_CROSS).convert("RGBA")
            cross_icon = cross_icon.resize((ICON_SIZE, ICON_SIZE), Image.Resampling.LANCZOS)
            # Load for list items
            list_cross_icon = Image.open(ICON_PATH_CROSS).convert("RGBA")
            list_cross_icon = list_cross_icon.resize((LIST_ICON_SIZE, LIST_ICON_SIZE), Image.Resampling.LANCZOS)
        else:
            print(f"Warning: Cross icon not found at {ICON_PATH_CROSS}")
    except Exception as e:
        print(f"Error loading cross icon: {e}")

    try:
        bg_image_full = Image.open(bg_image_path).convert("RGBA") # Use RGBA for potential transparency later
    except FileNotFoundError:
        print(f"Error: Background image not found at {bg_image_path}. Cannot generate page.")
        return

    # --- Create Base Image with Full Background ---
    # Resize/Crop background image to fit the full page
    img_aspect = bg_image_full.width / bg_image_full.height
    page_aspect = WIDTH / HEIGHT

    if img_aspect > page_aspect:
        new_height = HEIGHT
        new_width = int(new_height * img_aspect)
        resized_bg = bg_image_full.resize((new_width, new_height), Image.Resampling.LANCZOS)
        crop_x = (new_width - WIDTH) // 2
        final_bg = resized_bg.crop((crop_x, 0, crop_x + WIDTH, new_height))
    else:
        new_width = WIDTH
        new_height = int(new_width / img_aspect)
        resized_bg = bg_image_full.resize((new_width, new_height), Image.Resampling.LANCZOS)
        crop_y = (new_height - HEIGHT) // 2
        final_bg = resized_bg.crop((0, crop_y, new_width, crop_y + HEIGHT))

    if final_bg.size != (WIDTH, HEIGHT):
         final_bg = final_bg.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

    # Create the base image and paste the full background
    img = Image.new('RGBA', (WIDTH, HEIGHT)) # Use RGBA
    img.paste(final_bg, (0, 0))
    draw = ImageDraw.Draw(img) # Draw object for the main image

    # --- Create Card Base & Mask (for rounded corners) ---
    # Define card coordinates directly on the main image
    card_box = (CARD_X0, CARD_Y0, CARD_X1, CARD_Y1)

    # 1. Crop the background area where the card will be
    background_crop = img.crop(card_box)

    # 2. Apply Gaussian blur
    blurred_crop = background_crop.filter(ImageFilter.GaussianBlur(CARD_BLUR_RADIUS))

    # 3. Create a rounded corner mask (same dimensions as the card)
    mask = Image.new('L', (CARD_WIDTH, CARD_HEIGHT), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, CARD_WIDTH, CARD_HEIGHT], radius=CARD_RADIUS, fill=255)

    # 4. Paste the blurred background onto the main image using the mask
    if blurred_crop.mode != 'RGBA' and img.mode == 'RGBA':
        blurred_crop = blurred_crop.convert('RGBA')
    
    # Create a light, semi-transparent overlay for the card area
    card_overlay = Image.new('RGBA', (CARD_WIDTH, CARD_HEIGHT), (240, 240, 240, 95)) # Alpha reduced to 140 (from 170)
    
    # Composite the light overlay onto the blurred crop
    if blurred_crop.mode != 'RGBA':
        blurred_crop = blurred_crop.convert('RGBA') 
    
    # Create a temporary image for the card face by pasting blurred_crop, then overlay
    card_face = Image.new('RGBA', (CARD_WIDTH, CARD_HEIGHT))
    card_face.paste(blurred_crop, (0,0)) 
    card_face = Image.alpha_composite(card_face, card_overlay)

    # Paste the final card_face (blurred_crop + light_overlay) onto the main image using the mask
    img.paste(card_face, (CARD_X0, CARD_Y0), mask)

    # --- Optional: Add a subtle border like in the hotel page ---
    draw = ImageDraw.Draw(img) # Re-initialize draw on the main image
    border_color = (200, 200, 200, 90) # Subtle light grey border
    border_thickness = 2
    draw.rounded_rectangle(
        card_box,
        radius=CARD_RADIUS,
        outline=border_color,
        width=border_thickness
    )

    # --- Draw Content (Titles and Items) directly onto the main image ---
    # Adjust coordinates to be relative to the page (img), not the removed card_img

    # --- Content Drawing Area (Centered within the card coordinates) ---
    content_x_start = CARD_X0 # Start at the card's left edge on the page
    content_width = CARD_WIDTH # Use full card width
    column_width = (content_width // 2) - COLUMN_PADDING 
    left_col_x_start = content_x_start + COLUMN_PADDING
    right_col_x_start = content_x_start + (content_width // 2) + COLUMN_PADDING

    # --- Calculate Title Heights for Header Band (now just for layout reference) ---
    try:
        bbox_incl_header = draw.textbbox((0, 0), TEXT_INCLUDED.replace(" ✓", "").strip(), font=font_title)
        title_text_height = bbox_incl_header[3] - bbox_incl_header[1]
    except AttributeError:
        _, title_text_height = draw.textsize(TEXT_INCLUDED.replace(" ✓", "").strip(), font=font_title)
    
    # header_band_height = title_text_height + 40 
    # header_band_y0 = CARD_Y0 + TITLE_TOP_MARGIN - 20 
    # header_band_y1 = header_band_y0 + header_band_height

    # # Draw header bands (subtle dark overlay behind titles) -> REMOVED
    # # Left Header Band
    # draw.rectangle(
    #     (CARD_X0, header_band_y0, CARD_MID_X, header_band_y1),
    #     fill=HEADER_BAND_COLOR
    # )
    # # Right Header Band
    # draw.rectangle(
    #     (CARD_MID_X, header_band_y0, CARD_X1, header_band_y1),
    #     fill=HEADER_BAND_COLOR
    # )

    # --- Left Column Title (Included) --- 
    text_included_only = TEXT_INCLUDED.replace(" ✓", "").strip()
    try:
        bbox_incl = draw.textbbox((0, 0), text_included_only, font=font_title)
        text_width_incl = bbox_incl[2] - bbox_incl[0]
        text_height_incl = bbox_incl[3] - bbox_incl[1]
    except AttributeError:
        text_width_incl, text_height_incl = draw.textlength(text_included_only, font=font_title), font_title.getbbox(text_included_only)[3]

    # Calculate combined width (icon + space + text)
    combined_width_incl = ICON_SIZE + TITLE_ICON_SPACING + text_width_incl if tick_icon else text_width_incl
    title_x_start_incl = left_col_x_start + (column_width - combined_width_incl) // 2 # Center combined element
    title_y_incl = CARD_Y0 + TITLE_TOP_MARGIN

    # Draw Icon (if available)
    icon_y_offset_manual = 25 # Pixels to bump icon down relative to text center alignment
    icon_y_incl = title_y_incl + (text_height_incl - ICON_SIZE) // 2 + icon_y_offset_manual
    current_x_incl = title_x_start_incl
    if tick_icon:
        # Ensure tick_icon is RGBA if img is RGBA, for proper alpha blending with shadow
        if tick_icon.mode != 'RGBA' and img.mode == 'RGBA':
            tick_icon = tick_icon.convert('RGBA')
        img.paste(tick_icon, (int(current_x_incl), int(icon_y_incl)), tick_icon) 
        current_x_incl += ICON_SIZE + TITLE_ICON_SPACING

    # Draw Text (with shadow)
    # Shadow for title
    draw.text(
        (current_x_incl + TEXT_SHADOW_OFFSET[0], title_y_incl + TEXT_SHADOW_OFFSET[1]),
        text_included_only, 
        fill=TEXT_SHADOW_COLOR, 
        font=font_title
    )
    # Main title text
    draw.text((current_x_incl, title_y_incl), text_included_only, fill=COLOR_CHARCOAL_TEXT, font=font_title)

    # --- Right Column Title (Not Included) --- 
    text_excluded_only = TEXT_NOT_INCLUDED.replace(" ✕", "").strip() # Remove cross text
    try:
        bbox_excl = draw.textbbox((0, 0), text_excluded_only, font=font_title)
        text_width_excl = bbox_excl[2] - bbox_excl[0]
        text_height_excl = bbox_excl[3] - bbox_excl[1]
    except AttributeError:
        text_width_excl, text_height_excl = draw.textlength(text_excluded_only, font=font_title), font_title.getbbox(text_excluded_only)[3]

    # Calculate combined width (icon + space + text)
    combined_width_excl = ICON_SIZE + TITLE_ICON_SPACING + text_width_excl if cross_icon else text_width_excl
    title_x_start_excl = right_col_x_start + (column_width - combined_width_excl) // 2 # Center combined element
    title_y_excl = CARD_Y0 + TITLE_TOP_MARGIN

    # Draw Icon (if available)
    icon_y_offset_manual = 35 # Pixels to bump icon down relative to text center alignment
    icon_y_excl = title_y_excl + (text_height_excl - ICON_SIZE) // 2 + icon_y_offset_manual
    current_x_excl = title_x_start_excl
    if cross_icon:
        # Ensure cross_icon is RGBA if img is RGBA
        if cross_icon.mode != 'RGBA' and img.mode == 'RGBA':
            cross_icon = cross_icon.convert('RGBA')
        img.paste(cross_icon, (int(current_x_excl), int(icon_y_excl)), cross_icon)
        current_x_excl += ICON_SIZE + TITLE_ICON_SPACING
    
    # Draw Text (with shadow)
    # Shadow for title
    draw.text(
        (current_x_excl + TEXT_SHADOW_OFFSET[0], title_y_excl + TEXT_SHADOW_OFFSET[1]),
        text_excluded_only, 
        fill=TEXT_SHADOW_COLOR, 
        font=font_title
    )
    # Main title text
    draw.text((current_x_excl, title_y_excl), text_excluded_only, fill=COLOR_CHARCOAL_TEXT, font=font_title)

    # --- Draw Vertical Divider --- 
    divider_x = content_x_start + content_width // 2
    # Start divider slightly below titles, end before card bottom
    divider_y_start = title_y_incl + max(text_height_incl, text_height_excl) + 40 
    divider_y_end = CARD_Y1 - CARD_MARGIN # End margin from bottom of card
    draw.line([(divider_x, divider_y_start), (divider_x, divider_y_end)], 
              fill=DIVIDER_COLOR, width=DIVIDER_THICKNESS)

    # --- Draw Inclusion Items (Left Column) --- 
    # current_y = header_band_y1 + 40 # Start items below header band + padding
    # Titles are at CARD_Y0 + TITLE_TOP_MARGIN. Start items below that.
    current_y = CARD_Y0 + TITLE_TOP_MARGIN + title_text_height + 300 # Increased gap from 60 to 100
    available_text_width = column_width - LIST_ICON_SIZE - LIST_ICON_TEXT_SPACING - COLUMN_PADDING 
    
    # Estimate wrap width (adjust multiplier as needed for Chalkboard font)
    # avg_char_width_est = font_item.size * 0.35 # Reduced multiplier from 0.5
    wrap_width_chars = 25 # Directly set for more text per line
    # if avg_char_width_est > 0:
    #     wrap_width_chars = max(25, int(available_text_width / avg_char_width_est)) # Ensure minimum wrap width, increased min
    print(f"Left Column: Item Font Size={ITEM_FONT_SIZE}, Available Width={available_text_width}, Est Wrap Chars={wrap_width_chars}")

    for item in inclusions_list:
        lines = textwrap.wrap(item, width=wrap_width_chars)
        if lines:
            # Truncate lines if more than MAX_ITEM_LINES
            if len(lines) > MAX_ITEM_LINES:
                lines = lines[:MAX_ITEM_LINES]
                if len(lines[-1]) > 3: # Ensure there's space for ellipsis
                    lines[-1] = lines[-1][:-3] + "..."
                else:
                    lines[-1] = "..." # If last line is too short, just use ellipsis
            
            first_line_height_approx = font_item.size 
            icon_y = current_y + (first_line_height_approx - LIST_ICON_SIZE) // 2
            # Draw list tick icon
            if list_tick_icon:
                 # Ensure icon is RGBA if main image is
                 if list_tick_icon.mode != 'RGBA' and img.mode == 'RGBA':
                     list_tick_icon = list_tick_icon.convert('RGBA')
                 img.paste(list_tick_icon, (left_col_x_start, int(icon_y)), list_tick_icon)
            
            # Calculate text start position
            text_x = left_col_x_start + LIST_ICON_SIZE + LIST_ICON_TEXT_SPACING
            
            # Draw first line of text (with shadow)
            draw.text(
                (text_x + TEXT_SHADOW_OFFSET[0], current_y + TEXT_SHADOW_OFFSET[1]),
                lines[0], 
                fill=TEXT_SHADOW_COLOR, 
                font=font_item
            )
            draw.text((text_x, current_y), lines[0], fill=COLOR_CHARCOAL_TEXT, font=font_item)
            current_y += ITEM_LINE_SPACING 
            # Draw subsequent wrapped lines (indented to align with first line text, with shadow)
            for line_idx, line in enumerate(lines[1:]):
                # Shadow for wrapped line
                draw.text(
                    (text_x + TEXT_SHADOW_OFFSET[0], current_y + TEXT_SHADOW_OFFSET[1]),
                    line, 
                    fill=TEXT_SHADOW_COLOR, 
                    font=font_item
                )
                draw.text((text_x, current_y), line, fill=COLOR_CHARCOAL_TEXT, font=font_item)
                current_y += ITEM_LINE_SPACING 
        else: # Handle empty items?
            current_y += ITEM_LINE_SPACING
        # No extra space between items to maximize vertical fill

    # --- Draw Exclusion Items (Right Column) --- 
    # current_y = header_band_y1 + 40 # Reset Y to start below header band + padding
    current_y = CARD_Y0 + TITLE_TOP_MARGIN + title_text_height + 300 # Reset Y, Increased gap from 60 to 100
    available_text_width = column_width - LIST_ICON_SIZE - LIST_ICON_TEXT_SPACING - COLUMN_PADDING
    # avg_char_width_est = font_item.size * 0.35 # Reduced multiplier from 0.5
    wrap_width_chars = 25 # Directly set for more text per line
    # if avg_char_width_est > 0:
    #     wrap_width_chars = max(25, int(available_text_width / avg_char_width_est))
    print(f"Right Column: Item Font Size={ITEM_FONT_SIZE}, Available Width={available_text_width}, Est Wrap Chars={wrap_width_chars}")

    for item in exclusions_list:
        lines = textwrap.wrap(item, width=wrap_width_chars)
        if lines:
            # Truncate lines if more than MAX_ITEM_LINES
            if len(lines) > MAX_ITEM_LINES:
                lines = lines[:MAX_ITEM_LINES]
                if len(lines[-1]) > 3:
                    lines[-1] = lines[-1][:-3] + "..."
                else:
                    lines[-1] = "..."

            first_line_height_approx = font_item.size
            icon_y = current_y + (first_line_height_approx - LIST_ICON_SIZE) // 2
            # Draw list cross icon
            if list_cross_icon:
                 # Ensure icon is RGBA if main image is
                 if list_cross_icon.mode != 'RGBA' and img.mode == 'RGBA':
                     list_cross_icon = list_cross_icon.convert('RGBA')
                 img.paste(list_cross_icon, (right_col_x_start, int(icon_y)), list_cross_icon)
            
            text_x = right_col_x_start + LIST_ICON_SIZE + LIST_ICON_TEXT_SPACING
            
            # Draw first line of text (with shadow)
            draw.text(
                (text_x + TEXT_SHADOW_OFFSET[0], current_y + TEXT_SHADOW_OFFSET[1]),
                lines[0], 
                fill=TEXT_SHADOW_COLOR, 
                font=font_item
            )
            draw.text((text_x, current_y), lines[0], fill=COLOR_CHARCOAL_TEXT, font=font_item)
            current_y += ITEM_LINE_SPACING
            # Draw subsequent wrapped lines (with shadow)
            for line_idx, line in enumerate(lines[1:]):
                # Shadow for wrapped line
                draw.text(
                    (text_x + TEXT_SHADOW_OFFSET[0], current_y + TEXT_SHADOW_OFFSET[1]),
                    line, 
                    fill=TEXT_SHADOW_COLOR, 
                    font=font_item
                )
                draw.text((text_x, current_y), line, fill=COLOR_CHARCOAL_TEXT, font=font_item)
                current_y += ITEM_LINE_SPACING
        else:
            current_y += ITEM_LINE_SPACING
        # No extra space between items

    # --- Save Image ---
    try:
        # Save as RGB (discard alpha)
        print(f"Attempting to save image to: {output_path}")
        img_rgb = img.convert('RGB')
        img_rgb.save(output_path)
        print(f"Successfully completed save command for: {output_path}")
        # Explicitly close images
        img_rgb.close() 
        img.close()
        # Original success message remains
        print(f"Successfully generated inclusions/exclusions page: {output_path}")
    except Exception as e:
        print(f"Error saving image {output_path}: {e}")
        # Close images in case of error too, if they exist
        if 'img_rgb' in locals() and img_rgb:
            img_rgb.close()
        if 'img' in locals() and img:
            img.close()

# Example Usage (if you want to run this script directly)
if __name__ == '__main__':
    # Assume assets are relative to the workspace root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.abspath(os.path.join(script_dir, '..')) # Go up one level

    font_title_file = os.path.join(workspace_root, FONT_PATH_PLAYFAIR)
    font_item_file = os.path.join(workspace_root, FONT_PATH_ITEM) # Use updated item font path
    bg_img_file = os.path.join(workspace_root, 'inputs', 'incexc_bg.jpg')
    details_file = os.path.join(workspace_root, 'inputs', 'itinerary_details.json') # Path to json
    output_dir = os.path.join(workspace_root, 'outputs')
    output_file = 'page_6_inc_exc.jpg'

    # --- Load Data from JSON ---
    inclusions = []
    exclusions = []
    if not os.path.exists(details_file):
        print(f"Error: Itinerary details file not found at {details_file}")
        # Use placeholder data if file not found?
        inclusions = ["Placeholder Inclusion 1", "Placeholder Inclusion 2 which is quite long and needs wrapping maybe"]
        exclusions = ["Placeholder Exclusion 1", "Placeholder Exclusion 2"]
    else:
        try:
            with open(details_file, 'r') as f:
                data = json.load(f)
            inclusions = data.get("itinerary_details", {}).get("inclusions", [])
            exclusions = data.get("itinerary_details", {}).get("exclusions", [])
            if not inclusions:
                 print("Warning: No 'inclusions' found in JSON data.")
            if not exclusions:
                 print("Warning: No 'exclusions' found in JSON data.")
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {details_file}")
            # Handle error? Use placeholders?
        except Exception as e:
            print(f"Error reading details file {details_file}: {e}")
            # Handle error?

    # Check if assets exist before running (include icons check)
    assets_ok = True
    if not os.path.exists(font_title_file):
        print(f"Title font not found: {font_title_file}")
        assets_ok = False # Might be more critical?
    if not os.path.exists(font_item_file):
         print(f"Item font not found: {font_item_file} (Will use default)")
         # Don't set assets_ok to False, allow fallback
    if not os.path.exists(bg_img_file):
        print(f"Background image not found: {bg_img_file}")
        assets_ok = False
    if not os.path.exists(os.path.join(workspace_root, ICON_PATH_TICK)):
         print(f"Tick icon not found: {ICON_PATH_TICK}")
         # Might want to allow fallback to text? For now, just warn.
    if not os.path.exists(os.path.join(workspace_root, ICON_PATH_CROSS)):
         print(f"Cross icon not found: {ICON_PATH_CROSS}")
         # Might want to allow fallback to text? For now, just warn.

    if assets_ok: # Proceed if critical assets (bg, title font) exist
        generate_inc_exc_page(
            output_file,
            font_title_file,
            font_item_file,
            bg_img_file,
            output_dir,
            inclusions, # Pass loaded data
            exclusions  # Pass loaded data
        )
    else:
        print("Generation skipped due to missing critical assets (background or title font).") 