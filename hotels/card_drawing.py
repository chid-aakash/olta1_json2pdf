import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datetime import datetime # Added for robust date parsing

# Import shared constants (if needed, e.g., text colors)
# Assuming hotels_page_generator defines TEXT_DARK
try:
    from .hotels_page_generator import TEXT_DARK # Import TEXT_DARK
except ImportError:
    # Fallback if run directly or structure changes
    TEXT_DARK = (33, 33, 33) # Define fallback
    print("Warning: Could not import TEXT_DARK, using fallback.")

# --- Card 1 (Main Info) Constants ---
CARD1_CORNER_RADIUS = 24
CARD1_VPADDING = 85
CARD1_HPADDING = 105
CARD1_MIN_WIDTH = 1000
CARD1_MAX_WIDTH_RATIO = 0.85
CARD1_TOP_POS_RATIO = 0.09 # Nudged up (user setting)
CARD1_BLUR_RADIUS = 20 # Increased blur slightly for pop
TEXT_LIGHT = (255, 255, 255)
TEXT_SHADOW_COLOR_CARD = (0, 0, 0, 128) # Shadow for light text on cards
TEXT_SHADOW_OFFSET_CARD = (2, 2)      # Shadow offset for light text on cards

# --- Element Spacing & Sizing ---
NAME_STAR_SPACING = 210 # Increased from 180
STAR_ICON_PATH = "icons/star.png"
STAR_ICON_SIZE = 95 # Increased from 80
STAR_SPACING = 10 # Increased from 8

STAR_DETAIL_SPACING = 140 # Increased from 120

LOCATION_PIN_ICON_PATH = "icons/map-pin-white.png" # Changed to white version
LOCATION_PIN_SIZE = 135 # Increased from 115
LOCATION_TEXT_SPACING = 40 # Increased from 35
PHONE_ICON_PATH = "icons/phone-call-white.png" # Changed to white version
PHONE_ICON_SIZE = 105 # Increased from 90
PHONE_TEXT_SPACING = 40 # Increased from 35
DETAIL_LINE_SPACING = 65 # Increased from 55
TEXT_NUDGE_Y = -30 # Adjusted from -25
PHONE_NUDGE_X = -35 # Adjusted from -30

# --- Card 2 (Check-in/out) Constants ---
CARD2_CORNER_RADIUS = 18
CARD2_VPADDING = 85 # Increased from 70
CARD2_HPADDING = 115 # Increased from 100
CARD2_MIN_WIDTH = 900 # Increased min width slightly
CARD2_MAX_WIDTH_RATIO = 0.75 # Increased max width ratio slightly
CARD2_BLUR_RADIUS = 30 # Match blur or adjust
LABEL_DATE_SPACING = 30 # Increased from 25
DATE_TIME_SPACING = 25  # Increased from 20
CARD2_COLUMN_SPACING = 160 # Increased from 140

# --- Inter-Card Spacing ---
CARD_SPACING = 350 # Vertical space between Card 1 and Card 2 (Increased significantly)

# --- Amenities Card Constants ---
CARD_AMENITIES_CORNER_RADIUS = 18
CARD_AMENITIES_VPADDING = 70
CARD_AMENITIES_HPADDING = 95
CARD_AMENITIES_MIN_WIDTH = 900 # Similar to checkin card
CARD_AMENITIES_MAX_WIDTH_RATIO = 0.75 # Similar to checkin card
CARD_AMENITIES_BLUR_RADIUS = 45 # Increased from 30
INTER_CARD_SPACING_AMENITIES = 60 # Space between check-in card and amenities card (fallback)
AMENITIES_BOTTOM_PAGE_PADDING = 450 # Increased from 70 to move card further up
MIN_SPACING_BELOW_CHECKIN_FOR_AMENITIES_FOOTER = 40 # Min space if amenities card is at footer

AMENITY_ICON_SIZE = 95 # Increased from 65
AMENITY_ICON_LABEL_SPACING = 25
AMENITY_ITEM_HPADDING = 30
AMENITY_GRID_COLUMNS = 3
AMENITY_GRID_ROW_SPACING = 40
AMENITY_GRID_COL_SPACING = 40
ICON_BASE_PATH = "icons/" # Assuming icons like wifi.png, pool.png are here

def create_rounded_rectangle_mask(size, radius, *, inner_fill=255, outer_fill=0):
    """Creates a grayscale ('L') mask image for a rounded rectangle."""
    width, height = size
    mask = Image.new('L', size, outer_fill)
    draw = ImageDraw.Draw(mask)

    # Draw the main rectangle body
    draw.rectangle(
        (radius, 0, width - radius, height),
        fill=inner_fill
    )
    draw.rectangle(
        (0, radius, width, height - radius),
        fill=inner_fill
    )

    # Draw the four corner pieslices (arcs)
    # Top-left corner
    draw.pieslice(
        (0, 0, 2 * radius, 2 * radius),
        start=180, end=270, fill=inner_fill
    )
    # Top-right corner
    draw.pieslice(
        (width - 2 * radius, 0, width, 2 * radius),
        start=270, end=360, fill=inner_fill
    )
    # Bottom-left corner
    draw.pieslice(
        (0, height - 2 * radius, 2 * radius, height),
        start=90, end=180, fill=inner_fill
    )
    # Bottom-right corner
    draw.pieslice(
        (width - 2 * radius, height - 2 * radius, width, height),
        start=0, end=90, fill=inner_fill
    )

    return mask

def draw_main_info_card(img: Image.Image, hotel_info: dict, fonts: dict, page_dims: tuple) -> tuple:
    """Draws Card 1: Name, Stars, Address, Phone (Centered). Returns bounding box.""" # Renamed & updated docstring
    page_width, page_height = page_dims
    draw = ImageDraw.Draw(img)

    # --- 1. Extract Data & Prepare Text/Icons ---
    name = hotel_info.get("name", "Hotel Name N/A")
    stars_count = hotel_info.get("stars", 0)
    try: stars_count = int(stars_count)
    except (ValueError, TypeError): stars_count = 0
    address = hotel_info.get("short_address", "Address N/A")
    phone = hotel_info.get("phone_number", "Phone N/A")

    font_huge_name = fonts['playfair_huge']
    font_detail_label = fonts['inter_xl_detail'] # Use XL detail font
    font_small_detail = fonts['inter_small'] # For NA text

    # Load Icons (Star, Location, Phone)
    star_icon = None
    star_icon_w, star_icon_h = STAR_ICON_SIZE, STAR_ICON_SIZE
    try:
        if os.path.exists(STAR_ICON_PATH):
            star_icon = Image.open(STAR_ICON_PATH).convert("RGBA")
            star_icon = star_icon.resize((STAR_ICON_SIZE, STAR_ICON_SIZE), Image.Resampling.LANCZOS)
            star_icon_w, star_icon_h = star_icon.size
        else: print(f"Warning: Star icon not found at '{STAR_ICON_PATH}'.")
    except Exception as e: print(f"Error loading star icon '{STAR_ICON_PATH}': {e}")

    loc_pin_icon = None
    loc_pin_w, loc_pin_h = LOCATION_PIN_SIZE, LOCATION_PIN_SIZE
    try:
        if os.path.exists(LOCATION_PIN_ICON_PATH):
            loc_pin_icon = Image.open(LOCATION_PIN_ICON_PATH).convert("RGBA")
            loc_pin_icon = loc_pin_icon.resize((LOCATION_PIN_SIZE, LOCATION_PIN_SIZE), Image.Resampling.LANCZOS)
            loc_pin_w, loc_pin_h = loc_pin_icon.size
        else: print(f"Warning: Location pin icon not found at '{LOCATION_PIN_ICON_PATH}'.")
    except Exception as e: print(f"Error loading location pin icon '{LOCATION_PIN_ICON_PATH}': {e}")

    phone_icon = None
    phone_icon_w, phone_icon_h = PHONE_ICON_SIZE, PHONE_ICON_SIZE
    try:
        if os.path.exists(PHONE_ICON_PATH):
            phone_icon = Image.open(PHONE_ICON_PATH).convert("RGBA")
            phone_icon = phone_icon.resize((PHONE_ICON_SIZE, PHONE_ICON_SIZE), Image.Resampling.LANCZOS)
            phone_icon_w, phone_icon_h = phone_icon.size
        else: print(f"Warning: Phone icon not found at '{PHONE_ICON_PATH}'.")
    except Exception as e: print(f"Error loading phone icon '{PHONE_ICON_PATH}': {e}")


    # --- 2. Calculate Text Dimensions & Card Geometry ---
    try: # Use textbbox
        name_box = draw.textbbox((0,0), name, font=font_huge_name)
        addr_box = draw.textbbox((0,0), address, font=font_detail_label) # Use XL font
        phone_box = draw.textbbox((0,0), phone, font=font_detail_label) # Use XL font
        name_w, name_h = name_box[2] - name_box[0], name_box[3] - name_box[1]
        addr_w, addr_h = addr_box[2] - addr_box[0], addr_box[3] - addr_box[1]
        phone_w, phone_h = phone_box[2] - phone_box[0], phone_box[3] - phone_box[1]
    except AttributeError: # Fallback
        print("Warning: textbbox not available, using textlength (less accurate).")
        name_w, name_h = draw.textlength(name, font=font_huge_name), font_huge_name.getbbox(name)[3]
        addr_w, addr_h = draw.textlength(address, font=font_detail_label), font_detail_label.getbbox(address)[3] # Use XL font
        phone_w, phone_h = draw.textlength(phone, font=font_detail_label), font_detail_label.getbbox(phone)[3] # Use XL font


    # Star row dimensions
    stars_row_w = (star_icon_w * stars_count) + (max(0, stars_count - 1) * STAR_SPACING) if stars_count > 0 else 0
    stars_row_h = star_icon_h if stars_count > 0 else 0
    if stars_count == 0:
        na_text = "Rating N/A"
        na_box = draw.textbbox((0,0), na_text, font=font_small_detail)
        stars_row_w = na_box[2]-na_box[0]
        stars_row_h = na_box[3]-na_box[1]

    # Detail block dimensions (icon + space + text)
    detail_addr_line_w = (loc_pin_w + LOCATION_TEXT_SPACING + addr_w) if loc_pin_icon else addr_w
    detail_addr_line_h = max(loc_pin_h, addr_h) if loc_pin_icon else addr_h
    detail_phone_line_w = (phone_icon_w + PHONE_TEXT_SPACING + phone_w) if phone_icon else phone_w
    detail_phone_line_h = max(phone_icon_h, phone_h) if phone_icon else phone_h

    # Calculate overall content size
    max_detail_line_width = max(detail_addr_line_w, detail_phone_line_w) # Width for centering details
    max_content_width = max(name_w, stars_row_w, max_detail_line_width)
    total_content_height = (name_h +
                            NAME_STAR_SPACING +
                            stars_row_h +
                            STAR_DETAIL_SPACING +
                            detail_addr_line_h +
                            DETAIL_LINE_SPACING +
                            detail_phone_line_h)

    # Calculate card size
    content_width_padded = max_content_width + 2 * CARD1_HPADDING
    card_width = max(CARD1_MIN_WIDTH, content_width_padded)
    card_width = min(card_width, int(page_width * CARD1_MAX_WIDTH_RATIO))
    card_height = total_content_height + 2 * CARD1_VPADDING

    # Calculate card position
    card_x = (page_width - card_width) // 2
    card_y = int(page_height * CARD1_TOP_POS_RATIO)
    card_box = (card_x, card_y, card_x + card_width, card_y + card_height)

    # --- 3. Apply Frosted Glass Effect ---
    background_crop = img.crop(card_box)
    blurred_crop = background_crop.filter(ImageFilter.GaussianBlur(CARD1_BLUR_RADIUS))
    mask = create_rounded_rectangle_mask((card_width, card_height), CARD1_CORNER_RADIUS)
    if blurred_crop.mode != 'RGBA': blurred_crop = blurred_crop.convert('RGBA')
    img.paste(blurred_crop, (card_x, card_y), mask)

    # --- 3.5 Add Consistent Glassy Border (Matches other cards) ---
    draw = ImageDraw.Draw(img)
    border_color = (220, 220, 220, 200) # Consistent with other cards
    border_thickness = 3               # Consistent with other cards

    draw.rounded_rectangle(
        card_box, 
        radius=CARD1_CORNER_RADIUS, 
        outline=border_color, 
        width=border_thickness
    )

    # --- 4. Draw Text & Icons ---
    draw = ImageDraw.Draw(img)
    current_y = card_y + CARD1_VPADDING

    # Hotel Name (HUGE, Centered, with Shadow)
    text_x_name = card_x + (card_width - name_w) // 2
    # Draw shadow
    draw.text(
        (text_x_name + TEXT_SHADOW_OFFSET_CARD[0], current_y + TEXT_SHADOW_OFFSET_CARD[1]),
        name,
        fill=TEXT_SHADOW_COLOR_CARD,
        font=font_huge_name
    )
    # Draw main text
    draw.text((text_x_name, current_y), name, fill=TEXT_LIGHT, font=font_huge_name)
    current_y += name_h + NAME_STAR_SPACING

    # Stars (Icons or Text, Centered)
    if star_icon and stars_count > 0:
        star_row_start_x = card_x + (card_width - stars_row_w) // 2
        star_y = current_y
        current_star_x = star_row_start_x
        for _ in range(stars_count):
            img.paste(star_icon, (current_star_x, star_y), star_icon)
            current_star_x += star_icon_w + STAR_SPACING
    elif stars_count == 0:
        na_text = "Rating N/A"
        text_x = card_x + (card_width - stars_row_w) // 2
        draw.text((text_x, current_y), na_text, fill=TEXT_DARK, font=font_small_detail)
    current_y += stars_row_h + STAR_DETAIL_SPACING # Use increased spacing

    # -- Centered Detail Block --
    # Calculate the starting X for the whole block based on the widest line
    detail_block_start_x = card_x + (card_width - max_detail_line_width) // 2

    # Address (Large Text, Vertically Centered with Icon)
    current_x_addr_icon = detail_block_start_x
    current_x_addr_text = detail_block_start_x # Start text at same point initially
    icon_y_addr = current_y + (detail_addr_line_h - loc_pin_h) // 2 # Center icon in line height

    if loc_pin_icon:
        # For light text, icon should ideally also be light or have good contrast
        img.paste(loc_pin_icon, (current_x_addr_icon, icon_y_addr), loc_pin_icon)
        current_x_addr_text += loc_pin_w + LOCATION_TEXT_SPACING # Adjust text start after icon
        icon_center_y = icon_y_addr + loc_pin_h / 2
        text_y_addr = icon_center_y - (addr_h / 2) # Align text center to icon center
        text_y_addr += TEXT_NUDGE_Y # Apply manual vertical nudge
    else:
        text_y_addr = current_y + (detail_addr_line_h - addr_h) // 2

    # Draw shadow for address
    draw.text(
        (current_x_addr_text + TEXT_SHADOW_OFFSET_CARD[0], text_y_addr + TEXT_SHADOW_OFFSET_CARD[1]),
        address,
        fill=TEXT_SHADOW_COLOR_CARD,
        font=font_detail_label
    )
    # Draw address text
    draw.text((current_x_addr_text, text_y_addr), address, fill=TEXT_LIGHT, font=font_detail_label) # Changed to TEXT_LIGHT
    current_y += detail_addr_line_h + DETAIL_LINE_SPACING

    # Phone (Large Text, Vertically Centered with Icon, Nudged Right)
    phone_line_start_x = card_x + (card_width - detail_phone_line_w) // 2
    phone_line_start_x += PHONE_NUDGE_X # Apply horizontal nudge

    current_x_phone_icon = phone_line_start_x
    current_x_phone_text = phone_line_start_x # Start text relative to nudged position
    icon_y_phone = current_y + (detail_phone_line_h - phone_icon_h) // 2 # Center icon in line height

    if phone_icon:
        # For light text, icon should ideally also be light
        img.paste(phone_icon, (current_x_phone_icon, icon_y_phone), phone_icon)
        current_x_phone_text += phone_icon_w + PHONE_TEXT_SPACING # Adjust text start after icon
        icon_center_y = icon_y_phone + phone_icon_h / 2
        text_y_phone = icon_center_y - (phone_h / 2) # Align text center to icon center
        text_y_phone += TEXT_NUDGE_Y # Apply manual vertical nudge
    else:
        text_y_phone = current_y + (detail_phone_line_h - phone_h) // 2

    # Draw shadow for phone
    draw.text(
        (current_x_phone_text + TEXT_SHADOW_OFFSET_CARD[0], text_y_phone + TEXT_SHADOW_OFFSET_CARD[1]),
        phone,
        fill=TEXT_SHADOW_COLOR_CARD,
        font=font_detail_label
    )
    # Draw phone text
    draw.text((current_x_phone_text, text_y_phone), phone, fill=TEXT_LIGHT, font=font_detail_label) # Changed to TEXT_LIGHT

    print(f"  -> Drawn Main Info Card at ({card_x}, {card_y}) size {card_width}x{card_height}") # Updated print
    return card_box # Return bounding box


# --- Robust Date/Time Formatting Helper ---
def format_datetime_new(dt_str):
    if not isinstance(dt_str, str): return "N/A", "N/A"

    possible_formats = [
        "%dth %B %I%p",   # 15th June 3PM
        "%d %b %H:%M",    # 18 Jun 15:00
        "%d %B %H:%M",    # 18 June 15:00
        "%d %b %I:%M%p",  # 18 Jun 03:00PM
        "%d %B %I:%M%p",  # 18 June 03:00PM
        "%d %b %I%p",     # 18 Jun 3PM
        # Add more formats if needed
    ]
    dt_obj = None
    # Clean up 'th', 'st', 'nd', 'rd' and handle potential missing space before AM/PM
    cleaned_str = dt_str.upper().replace('TH','').replace('ST','').replace('ND','').replace('RD','')
    if "AM" in cleaned_str and not " AM" in cleaned_str:
       cleaned_str = cleaned_str.replace("AM", " AM")
    if "PM" in cleaned_str and not " PM" in cleaned_str:
       cleaned_str = cleaned_str.replace("PM", " PM")

    for fmt in possible_formats:
        try:
            dt_obj = datetime.strptime(cleaned_str, fmt)
            break # Stop if format matches
        except ValueError:
            continue

    if dt_obj:
        date_part = dt_obj.strftime("%d %B").upper() # Changed format to DD MONTHNAME (e.g., 15 JUNE)
        time_part = dt_obj.strftime("%I %p")      # Changed format to H AM/PM (e.g., 03 PM)
        # Handle potential leading zero in hour (e.g., 03 PM -> 3 PM)
        if time_part.startswith('0'):
            time_part = time_part[1:]
        return date_part, time_part
    else:
        # Basic fallback if parsing fails
        print(f"Warning: Could not parse datetime string '{dt_str}' with known formats.")
        parts = dt_str.split()
        if len(parts) >= 2:
            return parts[0].upper(), " ".join(parts[1:]).upper()
        return dt_str.upper(), "" # Or return N/A, N/A


def draw_checkin_card(img: Image.Image, hotel_info: dict, fonts: dict, page_dims: tuple, card1_box: tuple):
    """Draws Card 2: Check-in / Check-out times, positioned below card1_box."""
    print("\n--- Inside draw_checkin_card --- ") # DEBUG PRINT
    page_width, page_height = page_dims
    draw = ImageDraw.Draw(img)

    # --- 1. Extract Data & Format ---
    checkin_time_str = hotel_info.get("check_in_time", "N/A")
    checkout_time_str = hotel_info.get("check_out_time", "N/A")
    checkin_label = "CHECK-IN"
    checkout_label = "CHECK-OUT"

    # Use the new robust formatter
    checkin_date_formatted, checkin_time_formatted = format_datetime_new(checkin_time_str)
    checkout_date_formatted, checkout_time_formatted = format_datetime_new(checkout_time_str)

    print(f"  Formatted Check-in: {checkin_date_formatted} / {checkin_time_formatted}") # DEBUG PRINT
    print(f"  Formatted Check-out: {checkout_date_formatted} / {checkout_time_formatted}") # DEBUG PRINT


    # --- Font Selection ---
    font_label = fonts.get('playfair_regular', fonts['inter_large_detail']) # Use Playfair for label, fallback
    font_date = fonts.get('playfair_regular', fonts['inter_xl_detail'])   # Use Playfair for date, fallback
    font_time = fonts.get('playfair_italic', fonts['inter_xl_detail'])    # Use Playfair Italic for time, fallback


    # --- 2. Calculate Text Dimensions & Card Geometry ---
    try: # Use textbbox
        cin_label_box = draw.textbbox((0,0), checkin_label, font=font_label)
        cout_label_box = draw.textbbox((0,0), checkout_label, font=font_label)
        cin_date_box = draw.textbbox((0,0), checkin_date_formatted, font=font_date)
        cout_date_box = draw.textbbox((0,0), checkout_date_formatted, font=font_date)
        cin_time_box = draw.textbbox((0,0), checkin_time_formatted, font=font_time)
        cout_time_box = draw.textbbox((0,0), checkout_time_formatted, font=font_time)

        cin_label_w, cin_label_h = cin_label_box[2] - cin_label_box[0], cin_label_box[3] - cin_label_box[1]
        cout_label_w, cout_label_h = cout_label_box[2] - cout_label_box[0], cout_label_box[3] - cout_label_box[1]
        cin_date_w, cin_date_h = cin_date_box[2] - cin_date_box[0], cin_date_box[3] - cin_date_box[1]
        cout_date_w, cout_date_h = cout_date_box[2] - cout_date_box[0], cout_date_box[3] - cout_date_box[1]
        cin_time_w, cin_time_h = cin_time_box[2] - cin_time_box[0], cin_time_box[3] - cin_time_box[1]
        cout_time_w, cout_time_h = cout_time_box[2] - cout_time_box[0], cout_time_box[3] - cout_time_box[1]

    except AttributeError: # Fallback
        print("Warning: textbbox not available for checkin card, using textlength.")
        # Simplified fallback, may not be accurate for multi-line layout
        cin_label_w, cin_label_h = draw.textlength(checkin_label, font=font_label), font_label.getbbox(checkin_label)[3]
        cout_label_w, cout_label_h = draw.textlength(checkout_label, font=font_label), font_label.getbbox(checkout_label)[3]
        cin_date_w, cin_date_h = draw.textlength(checkin_date_formatted, font=font_date), font_date.getbbox(checkin_date_formatted)[3]
        cout_date_w, cout_date_h = draw.textlength(checkout_date_formatted, font=font_date), font_date.getbbox(checkout_date_formatted)[3]
        cin_time_w, cin_time_h = draw.textlength(checkin_time_formatted, font=font_time), font_time.getbbox(checkin_time_formatted)[3]
        cout_time_w, cout_time_h = draw.textlength(checkout_time_formatted, font=font_time), font_time.getbbox(checkout_time_formatted)[3]


    # --- Layout calculations (Multi-line) ---
    label_h = max(cin_label_h, cout_label_h)
    date_h = max(cin_date_h, cout_date_h)
    time_h = max(cin_time_h, cout_time_h)

    # Column widths based on widest element (label, date, or time)
    col1_w = max(cin_label_w, cin_date_w, cin_time_w)
    col2_w = max(cout_label_w, cout_date_w, cout_time_w)

    total_content_width = col1_w + CARD2_COLUMN_SPACING + col2_w # Width based on columns + spacing
    total_content_height = label_h + LABEL_DATE_SPACING + date_h + DATE_TIME_SPACING + time_h # Vertical stacking

    # Calculate card size
    content_width_padded = total_content_width + 2 * CARD2_HPADDING
    card_width = max(CARD2_MIN_WIDTH, content_width_padded)
    card_width = min(card_width, int(page_width * CARD2_MAX_WIDTH_RATIO))
    card_height = total_content_height + 2 * CARD2_VPADDING

    # Calculate card position
    card_x = (page_width - card_width) // 2
    card1_bottom_y = card1_box[3]
    card_y = card1_bottom_y + CARD_SPACING
    print(f"  Card 1 Bottom: {card1_bottom_y}, Card 2 Top: {card_y}, Card 2 Height: {card_height}") # DEBUG PRINT
    if card_y + card_height > page_height:
        print("Warning: Calculated Checkin Card position extends below page boundary. Adjusting upwards.")
        card_y = page_height - card_height - 10 # Adjust margin
        print(f"  Adjusted Card 2 Top: {card_y}") # DEBUG PRINT
    card_box = (card_x, card_y, card_x + card_width, card_y + card_height)


    # --- 3. Apply Frosted Glass Effect ---
    background_crop = img.crop(card_box)
    blurred_crop = background_crop.filter(ImageFilter.GaussianBlur(CARD2_BLUR_RADIUS))
    mask = create_rounded_rectangle_mask((card_width, card_height), CARD2_CORNER_RADIUS)
    if blurred_crop.mode != 'RGBA': blurred_crop = blurred_crop.convert('RGBA')
    img.paste(blurred_crop, (card_x, card_y), mask)


    # --- 3.5 Add Updated Glassy Border (Matches Amenities Card) ---
    draw = ImageDraw.Draw(img)
    border_color = (220, 220, 220, 200) # Match amenities card: Brighter, more opaque white
    border_thickness = 3               # Match amenities card: Increased from 2
    
    draw.rounded_rectangle(
        card_box,
        radius=CARD2_CORNER_RADIUS,
        outline=border_color,
        width=border_thickness
    )


    # --- 4. Draw Text (Multi-line Layout, TEXT_LIGHT with Shadows) ---
    draw = ImageDraw.Draw(img) # Ensure draw context is active
    content_start_x = card_x + (card_width - total_content_width) // 2 # Center the whole content block

    # Vertical positions
    current_y = card_y + CARD2_VPADDING
    label_y = current_y
    date_y = label_y + label_h + LABEL_DATE_SPACING
    time_y = date_y + date_h + DATE_TIME_SPACING


    # -- Column 1 (Check-in) --
    col1_label_x = content_start_x + (col1_w - cin_label_w) // 2
    col1_date_x = content_start_x + (col1_w - cin_date_w) // 2
    col1_time_x = content_start_x + (col1_w - cin_time_w) // 2

    # Shadow for check-in label
    draw.text((col1_label_x + TEXT_SHADOW_OFFSET_CARD[0], label_y + TEXT_SHADOW_OFFSET_CARD[1]), checkin_label, fill=TEXT_SHADOW_COLOR_CARD, font=font_label)
    draw.text((col1_label_x, label_y), checkin_label, fill=TEXT_LIGHT, font=font_label)
    # Shadow for check-in date
    draw.text((col1_date_x + TEXT_SHADOW_OFFSET_CARD[0], date_y + TEXT_SHADOW_OFFSET_CARD[1]), checkin_date_formatted, fill=TEXT_SHADOW_COLOR_CARD, font=font_date)
    draw.text((col1_date_x, date_y), checkin_date_formatted, fill=TEXT_LIGHT, font=font_date)
    # Shadow for check-in time
    draw.text((col1_time_x + TEXT_SHADOW_OFFSET_CARD[0], time_y + TEXT_SHADOW_OFFSET_CARD[1]), checkin_time_formatted, fill=TEXT_SHADOW_COLOR_CARD, font=font_time)
    draw.text((col1_time_x, time_y), checkin_time_formatted, fill=TEXT_LIGHT, font=font_time)


    # -- Separator Line (Thicker, Opaque) --
    line_x = content_start_x + col1_w + CARD2_COLUMN_SPACING // 2 
    line_y_start = label_y - 10
    line_y_end = time_y + time_h + 10
    # For white text, a light separator might be better, or keep dark for contrast against blur.
    # Let's try a slightly less prominent dark line, or a light gray one.
    # For now, keeping it dark for definition against the potentially varied background blur.
    line_color = (0, 0, 0, 200) # Opaque Black, slightly less intense if needed (was 255 alpha)
    line_thickness = 3 # Adjusted thickness to match border aesthetic (was 4)
    draw.line([(line_x, line_y_start), (line_x, line_y_end)], fill=line_color, width=line_thickness)


    # -- Column 2 (Check-out) --
    col2_start_x = content_start_x + col1_w + CARD2_COLUMN_SPACING
    col2_label_x = col2_start_x + (col2_w - cout_label_w) // 2
    col2_date_x = col2_start_x + (col2_w - cout_date_w) // 2
    col2_time_x = col2_start_x + (col2_w - cout_time_w) // 2

    # Shadow for check-out label
    draw.text((col2_label_x + TEXT_SHADOW_OFFSET_CARD[0], label_y + TEXT_SHADOW_OFFSET_CARD[1]), checkout_label, fill=TEXT_SHADOW_COLOR_CARD, font=font_label)
    draw.text((col2_label_x, label_y), checkout_label, fill=TEXT_LIGHT, font=font_label)
    # Shadow for check-out date
    draw.text((col2_date_x + TEXT_SHADOW_OFFSET_CARD[0], date_y + TEXT_SHADOW_OFFSET_CARD[1]), checkout_date_formatted, fill=TEXT_SHADOW_COLOR_CARD, font=font_date)
    draw.text((col2_date_x, date_y), checkout_date_formatted, fill=TEXT_LIGHT, font=font_date)
    # Shadow for check-out time
    draw.text((col2_time_x + TEXT_SHADOW_OFFSET_CARD[0], time_y + TEXT_SHADOW_OFFSET_CARD[1]), checkout_time_formatted, fill=TEXT_SHADOW_COLOR_CARD, font=font_time)
    draw.text((col2_time_x, time_y), checkout_time_formatted, fill=TEXT_LIGHT, font=font_time)


    print(f"  -> Drawn Checkin Card at ({card_x}, {card_y}) size {card_width}x{card_height}")
    return card_box # Return the bounding box


# --- Removed draw_details_card function ---


# --- TODO: Add function for Card 2 (Check-in/out) ---

def draw_amenities_card(img: Image.Image, amenities_list: list, fonts: dict, page_dims: tuple, card_above_box: tuple):
    """Draws the Amenities Card below the card_above_box."""
    if not amenities_list:
        print("No amenities provided, skipping amenities card.")
        return

    print("\n--- Inside draw_amenities_card ---")
    page_width, page_height = page_dims
    draw = ImageDraw.Draw(img)

    font_label = fonts.get('inter_label', ImageFont.load_default(size=36))

    # --- 1. Prepare Amenity Items (Icons and Text) ---
    prepared_amenities = []
    max_item_width = 0
    max_item_height = 0

    amenity_icon_map = {
        "Oceanfront Pools": "swimmer.png",
        "Fitness Center": "dumbbell.png",
        "Multiple Restaurants": "room-service.png",
        "Hiking": "hiking.png",
                "Beach Access": "sun-umbrella.png", 

        "Water Sports": "scuba-diving.png",
        "Wifi": "wi-fi.png" # Retained from user's previous edit
    }

    for amenity_name in amenities_list:
        icon_filename = amenity_icon_map.get(amenity_name, amenity_name.lower().replace(" ", "_") + ".png")
        icon_path = os.path.join(ICON_BASE_PATH, icon_filename)
        icon_img = None # Initialize as None
        icon_w, icon_h = AMENITY_ICON_SIZE, AMENITY_ICON_SIZE # Use default size for spacing initially
        
        try:
            if os.path.exists(icon_path):
                # Attempt to open and resize the icon
                loaded_icon = Image.open(icon_path).convert("RGBA")
                loaded_icon = loaded_icon.resize((AMENITY_ICON_SIZE, AMENITY_ICON_SIZE), Image.Resampling.LANCZOS)
                icon_img = loaded_icon # Assign if successful
                icon_w, icon_h = icon_img.size # Get actual size after loading
            else:
                print(f"Warning: Amenity icon file not found: {icon_path}. Label only will be drawn.")
        except Exception as e:
            # This will catch errors from Image.open if it's an unsupported format like SVG, or other issues
            print(f"Error loading or processing amenity icon {icon_path}: {e}. Label only will be drawn.")
            icon_img = None # Ensure icon_img is None if there was an error
        
        try:
            text_box = draw.textbbox((0,0), amenity_name, font=font_label)
            text_w, text_h = text_box[2] - text_box[0], text_box[3] - text_box[1]
        except AttributeError:
            text_w, text_h = draw.textlength(amenity_name, font=font_label), font_label.getbbox(amenity_name)[3]
        
        item_w = max(icon_w, text_w) + 2 * AMENITY_ITEM_HPADDING
        item_h = icon_h + AMENITY_ICON_LABEL_SPACING + text_h
        
        prepared_amenities.append({
            "name": amenity_name, 
            "icon": icon_img,  # This might be None if loading failed
            "text_w": text_w, "text_h": text_h, 
            "icon_w": icon_w, "icon_h": icon_h, # These will be default if icon failed, for spacing
            "item_w": item_w, "item_h": item_h
        })
        max_item_width = max(max_item_width, item_w)
        max_item_height = max(max_item_height, item_h)

    if not prepared_amenities:
        return

    # --- 2. Calculate Card Geometry based on Grid ---
    num_items = len(prepared_amenities)
    num_cols = min(AMENITY_GRID_COLUMNS, num_items)
    num_rows = (num_items + num_cols - 1) // num_cols

    total_content_width = (num_cols * max_item_width) + (max(0, num_cols - 1) * AMENITY_GRID_COL_SPACING)
    total_content_height = (num_rows * max_item_height) + (max(0, num_rows - 1) * AMENITY_GRID_ROW_SPACING)

    content_width_padded = total_content_width + 2 * CARD_AMENITIES_HPADDING
    card_width = max(CARD_AMENITIES_MIN_WIDTH, content_width_padded)
    card_width = min(card_width, int(page_width * CARD_AMENITIES_MAX_WIDTH_RATIO))
    card_height = total_content_height + 2 * CARD_AMENITIES_VPADDING

    # --- Calculate card position (move to bottom) ---
    card_x = (page_width - card_width) // 2
    desired_card_y_from_bottom = page_height - card_height - AMENITIES_BOTTOM_PAGE_PADDING

    card_above_bottom_y = card_above_box[3]

    # Check if placing at bottom overlaps or is too close to the card above
    if desired_card_y_from_bottom < card_above_bottom_y + MIN_SPACING_BELOW_CHECKIN_FOR_AMENITIES_FOOTER:
        print(f"Warning: Amenities card at bottom ({desired_card_y_from_bottom}) would be too close to card above (ends at {card_above_bottom_y}). Placing it relative to card above.")
        card_y = card_above_bottom_y + INTER_CARD_SPACING_AMENITIES # Fallback to position below previous card
    else:
        card_y = desired_card_y_from_bottom
        print(f"Amenities card placed at bottom: y={card_y}")

    # Final check to ensure it's not pushed off-page upwards if checkin card is very low and amenities card is tall
    if card_y < card_above_bottom_y + 20 and card_y != desired_card_y_from_bottom: # Check if fallback was used and still too high
        print(f"Warning: Amenities card fallback position still too high. Adjusting to minimal spacing.")
        card_y = card_above_bottom_y + 20 # Minimal spacing to prevent visual crush
    
    # Ensure card doesn't go above page top (e.g. if page is too short for all cards)
    card_y = max(card_y, CARD_AMENITIES_VPADDING) # Ensure it doesn't go off the top of the page

    if card_y + card_height > page_height - 10: # Final boundary check
        print("Warning: Amenities card still extends too close to page bottom. Height might be an issue.")
        # Potentially adjust height or log more critically

    card_box = (card_x, card_y, card_x + card_width, card_y + card_height)

    # --- 3. Apply Frosted Glass Effect & Border ---
    if card_height <= 0 or card_width <=0:
        print("Error: Invalid card dimensions for amenities card. Skipping.")
        return
        
    background_crop = img.crop(card_box)
    blurred_crop = background_crop.filter(ImageFilter.GaussianBlur(CARD_AMENITIES_BLUR_RADIUS))
    mask = create_rounded_rectangle_mask((card_width, card_height), CARD_AMENITIES_CORNER_RADIUS)
    if blurred_crop.mode != 'RGBA': blurred_crop = blurred_crop.convert('RGBA')
    img.paste(blurred_crop, (card_x, card_y), mask)

    draw = ImageDraw.Draw(img) # Re-init after paste
    border_color = (220, 220, 220, 200) # Brighter, more opaque white border
    border_thickness = 3 # Increased from 2
    draw.rounded_rectangle(card_box, radius=CARD_AMENITIES_CORNER_RADIUS, outline=border_color, width=border_thickness)

    # --- 4. Draw Amenities in a Grid ---
    current_col = 0
    current_row = 0
    base_x = card_x + CARD_AMENITIES_HPADDING + (total_content_width - ((num_cols * max_item_width) + (max(0, num_cols - 1) * AMENITY_GRID_COL_SPACING))) // 2
    base_y = card_y + CARD_AMENITIES_VPADDING + (total_content_height - ((num_rows * max_item_height) + (max(0, num_rows - 1) * AMENITY_GRID_ROW_SPACING))) // 2

    for i, amenity in enumerate(prepared_amenities):
        col_idx = i % num_cols
        row_idx = i // num_cols

        # Position for the current item cell (top-left of cell)
        item_cell_x = base_x + col_idx * (max_item_width + AMENITY_GRID_COL_SPACING)
        item_cell_y = base_y + row_idx * (max_item_height + AMENITY_GRID_ROW_SPACING)

        # Center icon in its part of the cell
        icon_x = item_cell_x + (max_item_width - amenity["icon_w"]) // 2
        icon_y = item_cell_y
        # Ensure icon is pasted if it exists and is an Image object
        if amenity["icon"] and isinstance(amenity["icon"], Image.Image):
            img.paste(amenity["icon"], (int(icon_x), int(icon_y)), amenity["icon"]) 
        # else: No explicit placeholder, just skip if icon is None or not an image
            # print(f"Skipping icon for {amenity['name']} as it is not a valid image object or is None.") # Already handled by load warning

        # Center text below the icon, with shadow
        label_x = item_cell_x + (max_item_width - amenity["text_w"]) // 2
        label_y = icon_y + amenity["icon_h"] + AMENITY_ICON_LABEL_SPACING
        # Draw shadow
        draw.text(
            (int(label_x) + TEXT_SHADOW_OFFSET_CARD[0], int(label_y) + TEXT_SHADOW_OFFSET_CARD[1]),
            amenity["name"],
            fill=TEXT_SHADOW_COLOR_CARD,
            font=font_label
        )
        # Draw main text
        draw.text((int(label_x), int(label_y)), amenity["name"], fill=TEXT_LIGHT, font=font_label)

    print(f"  -> Drawn Amenities Card at ({card_x}, {card_y}) size {card_width}x{card_height}")

# --- TODO: Add function for Card 2 (Check-in/out) ---
# def draw_checkin_card(img: Image.Image, hotel_info: dict, fonts: dict, page_dims: tuple, card1_bottom_y: int):
#    ... implementation ... 