import os
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
import textwrap

# --- Constants ---
WIDTH = 2480  # Standard A4 width @ 300 DPI
HEIGHT = 3508

# Page Split and Panel Dimensions
LEFT_IMAGE_WIDTH_RATIO = 0.40 # Left image takes 40% of the page width
RIGHT_PANEL_MARGIN_TOP = 150    # Margin from page top for the right panel
RIGHT_PANEL_MARGIN_BOTTOM = 150 # Margin from page bottom
RIGHT_PANEL_MARGIN_RIGHT = 90   # Margin from page right edge
RIGHT_PANEL_MARGIN_LEFT_GAP = 50 # Gap between left image area and right panel
RIGHT_PANEL_RADIUS = 30
RIGHT_PANEL_BLUR_RADIUS = 40 
# Overlay for the right panel (darker to make light text pop, as in reference)
RIGHT_PANEL_OVERLAY_COLOR = (0, 0, 0, 100) # Semi-transparent black

# Text Colors for Right Panel (assuming light text on darkish panel)
TEXT_COLOR_LIGHT = (240, 240, 240)
TEXT_COLOR_GOLD = (204, 153, 51) # For quote amount, similar to reference
TEXT_COLOR_SUBTLE = (200, 200, 200) # For secondary text like "PER COUPLE"

# Layout constants within the right panel
CONTENT_PADDING_PANEL = 70  # General padding inside the right panel
TITLE_FONT_SIZE_QUOTE = 80       # "YOUR PERSONAL QUOTE"
MAIN_QUOTE_FIGURE_SIZE = 180   # "₹1,35,000"
QUOTE_SUB_TEXT_SIZE = 60       # "PER COUPLE"
SECTION_TITLE_FONT_SIZE_QUOTE = 60 # "PAYMENT TERMS", "TERMS & CONDITIONS"
BODY_FONT_SIZE_QUOTE = 45
LINE_SPACING_FACTOR = 1.5

# Font Paths
FONT_TITLE_QUOTE_PATH = "fonts/PlayfairDisplay-Regular.ttf" # Example, adjust as needed
FONT_BODY_QUOTE_PATH = "fonts/PlayfairDisplay-Regular.ttf"         # Example, adjust as needed
FONT_BOLD_QUOTE_PATH = "fonts/PlayfairDisplay-Regular.ttf"            # Example, adjust as needed

DEFAULT_LEFT_BG_IMAGE_PATH = 'inputs/day3_hero.png'

# Gold Price Box constants
PRICE_BOX_VPADDING = 30
PRICE_BOX_HPADDING = 120
PRICE_BOX_RADIUS = 25
PRICE_BOX_BG_COLOR = (218, 173, 80) # Gold-ish color from reference
PRICE_BOX_TEXT_COLOR = (50, 40, 20) # Dark text for price box

def generate_quote_page(
    output_filename: str, 
    # font_path: str, # This will be replaced by specific font paths above
    base_output_dir: str, 
    quote: dict, 
    terms_conditions: list,
    left_bg_image_path: str = DEFAULT_LEFT_BG_IMAGE_PATH
):
    """Generates the quote page with a split UI similar to the reference."""
    output_path = os.path.join(base_output_dir, output_filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # --- Load Fonts ---
    try:
        font_page_title = ImageFont.truetype(FONT_TITLE_QUOTE_PATH, TITLE_FONT_SIZE_QUOTE)
    except IOError: font_page_title = ImageFont.load_default(size=TITLE_FONT_SIZE_QUOTE)
    try:
        font_quote_figure = ImageFont.truetype(FONT_BOLD_QUOTE_PATH, MAIN_QUOTE_FIGURE_SIZE) # Use a bold font for amount
    except IOError: font_quote_figure = ImageFont.load_default(size=MAIN_QUOTE_FIGURE_SIZE)
    try:
        font_quote_sub = ImageFont.truetype(FONT_BODY_QUOTE_PATH, QUOTE_SUB_TEXT_SIZE)
    except IOError: font_quote_sub = ImageFont.load_default(size=QUOTE_SUB_TEXT_SIZE)
    try:
        font_section_title = ImageFont.truetype(FONT_BOLD_QUOTE_PATH, SECTION_TITLE_FONT_SIZE_QUOTE)
    except IOError: font_section_title = ImageFont.load_default(size=SECTION_TITLE_FONT_SIZE_QUOTE)
    try:
        font_body = ImageFont.truetype(FONT_BODY_QUOTE_PATH, BODY_FONT_SIZE_QUOTE)
    except IOError: font_body = ImageFont.load_default(size=BODY_FONT_SIZE_QUOTE)

    # --- Main Page Background (using the left image as full page potentially) ---
    try:
        page_bg_full = Image.open(left_bg_image_path).convert("RGBA")
    except FileNotFoundError:
        print(f"Error: Background image '{left_bg_image_path}' not found. Creating plain background.")
        page_bg_full = Image.new('RGBA', (WIDTH, HEIGHT), (30, 30, 40, 255))

    # Scale page_bg_full to cover the entire page (WIDTH, HEIGHT)
    # This logic ensures the image covers the page, cropping if aspect ratios differ.
    img_aspect = page_bg_full.width / page_bg_full.height
    page_aspect = WIDTH / HEIGHT
    if img_aspect > page_aspect: # Image is wider than page
        new_height = HEIGHT
        new_width = int(new_height * img_aspect)
        resized_bg = page_bg_full.resize((new_width, new_height), Image.Resampling.LANCZOS)
        crop_x = (new_width - WIDTH) // 2
        final_page_bg = resized_bg.crop((crop_x, 0, crop_x + WIDTH, HEIGHT))
    else: # Image is taller than page or same aspect
        new_width = WIDTH
        new_height = int(new_width / img_aspect)
        resized_bg = page_bg_full.resize((new_width, new_height), Image.Resampling.LANCZOS)
        crop_y = (new_height - HEIGHT) // 2
        final_page_bg = resized_bg.crop((0, crop_y, WIDTH, crop_y + HEIGHT))
    if final_page_bg.size != (WIDTH, HEIGHT):
         final_page_bg = final_page_bg.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS) # Ensure exact size

    # Create main image canvas
    img = Image.new('RGBA', (WIDTH, HEIGHT))
    img.paste(final_page_bg, (0,0))
    draw = ImageDraw.Draw(img)

    # --- Define Right Panel Coordinates ---
    left_image_area_width = int(WIDTH * LEFT_IMAGE_WIDTH_RATIO)
    panel_x0 = left_image_area_width + RIGHT_PANEL_MARGIN_LEFT_GAP
    panel_y0 = RIGHT_PANEL_MARGIN_TOP
    panel_width = WIDTH - panel_x0 - RIGHT_PANEL_MARGIN_RIGHT
    panel_height = HEIGHT - panel_y0 - RIGHT_PANEL_MARGIN_BOTTOM
    panel_box = (panel_x0, panel_y0, panel_x0 + panel_width, panel_y0 + panel_height)

    # --- Create Frosted Glass Panel on the Right ---
    panel_background_crop = final_page_bg.crop(panel_box) # Crop from the final_page_bg
    panel_blurred_crop = panel_background_crop.filter(ImageFilter.GaussianBlur(RIGHT_PANEL_BLUR_RADIUS))
    
    panel_face = Image.new('RGBA', (panel_width, panel_height))
    panel_face.paste(panel_blurred_crop, (0,0))
    
    # --- Add vertical white gradient overlay for frosted effect ---
    gradient_overlay = Image.new('RGBA', (panel_width, panel_height), (255,255,255,0))
    for y in range(panel_height):
        # Top is more opaque, bottom is more transparent
        alpha = int(200 * (1 - y / panel_height))  # 200 at top, 0 at bottom
        for x in range(panel_width):
            gradient_overlay.putpixel((x, y), (255,255,255,alpha))
    panel_face = Image.alpha_composite(panel_face, gradient_overlay)

    panel_overlay = Image.new('RGBA', (panel_width, panel_height), RIGHT_PANEL_OVERLAY_COLOR)
    panel_face = Image.alpha_composite(panel_face, panel_overlay)

    panel_mask = Image.new('L', (panel_width, panel_height), 0)
    panel_mask_draw = ImageDraw.Draw(panel_mask)
    panel_mask_draw.rounded_rectangle([0, 0, panel_width, panel_height], radius=RIGHT_PANEL_RADIUS, fill=255)
    
    img.paste(panel_face, (panel_x0, panel_y0), panel_mask)

    # --- Draw Content onto the Right Panel ---
    current_y = panel_y0 + CONTENT_PADDING_PANEL
    content_area_x_start = panel_x0 + CONTENT_PADDING_PANEL
    content_area_width_panel = panel_width - 2 * CONTENT_PADDING_PANEL

    # Page Title "YOUR PERSONAL QUOTE"
    page_title_text = "YOUR PERSONAL QUOTE"
    title_w = draw.textlength(page_title_text, font=font_page_title)
    draw.text((panel_x0 + (panel_width - title_w) / 2, current_y), page_title_text, font=font_page_title, fill=TEXT_COLOR_LIGHT)
    current_y += TITLE_FONT_SIZE_QUOTE * LINE_SPACING_FACTOR + 40

    # --- Price Box --- 
    price_text_main = f"{quote.get('currency', '')} {quote.get('amount', 'N/A')}"
    price_text_sub = quote.get('details', 'PER PERSON') # Using details for "PER COUPLE" type info
    if "per person" in price_text_sub.lower() or "per couple" in price_text_sub.lower() or "total for" in price_text_sub.lower():
        pass # Use as is
    else: # Fallback if quote.details doesn't contain unit
        price_text_sub = "PER PERSON" 

    main_price_w = draw.textlength(price_text_main, font=font_quote_figure)
    sub_price_w = draw.textlength(price_text_sub, font=font_quote_sub)
    
    price_box_content_w = max(main_price_w, sub_price_w)
    price_box_w = price_box_content_w + 2 * PRICE_BOX_HPADDING
    price_box_h = MAIN_QUOTE_FIGURE_SIZE + QUOTE_SUB_TEXT_SIZE + PRICE_BOX_VPADDING * 2 + 10 # 10 for spacing
    price_box_x0 = panel_x0 + (panel_width - price_box_w) / 2
    price_box_y0 = current_y
    
    draw.rounded_rectangle(
        (price_box_x0, price_box_y0, price_box_x0 + price_box_w, price_box_y0 + price_box_h),
        radius=PRICE_BOX_RADIUS,
        fill=PRICE_BOX_BG_COLOR
    )
    # Price text
    draw.text(
        (price_box_x0 + (price_box_w - main_price_w) / 2, price_box_y0 + PRICE_BOX_VPADDING),
        price_text_main, 
        font=font_quote_figure, 
        fill=PRICE_BOX_TEXT_COLOR
    )
    # Sub text ("PER COUPLE")
    draw.text(
        (price_box_x0 + (price_box_w - sub_price_w) / 2, price_box_y0 + PRICE_BOX_VPADDING + MAIN_QUOTE_FIGURE_SIZE + 10),
        price_text_sub, 
        font=font_quote_sub, 
        fill=PRICE_BOX_TEXT_COLOR
    )
    current_y += price_box_h + 60

    # --- Payment Terms (Simplified for now) ---
    payment_title_text = "PAYMENT TERMS"
    section_title_w = draw.textlength(payment_title_text, font=font_section_title)
    draw.text((panel_x0 + (panel_width - section_title_w) / 2, current_y), payment_title_text, font=font_section_title, fill=TEXT_COLOR_SUBTLE)
    current_y += SECTION_TITLE_FONT_SIZE_QUOTE * LINE_SPACING_FACTOR + 20

    payment_terms_data = quote.get('payment_terms', {})
    deposit_text = f"Deposit: {payment_terms_data.get('deposit', 'N/A')}"
    balance_text = f"Balance {quote.get('balance_percentage', '90%')}: {payment_terms_data.get('balance_payment_time', 'N/A')}"
    # Simplified due/amount for now, actual layout needs more parsing of 'balance_details' from reference image.
    # This part needs careful data structure from the JSON.
    # Example items:
    items_payment = [
        (f"Deposit", payment_terms_data.get('deposit_due_date', 'Due'), f"{quote.get('currency','')} {payment_terms_data.get('deposit_amount', 'N/A')}"),
        (f"Balance {quote.get('balance_percentage', '90%')}", payment_terms_data.get('balance_due_date', 'Due'), f"{quote.get('currency','')} {payment_terms_data.get('balance_amount', 'N/A')}")
    ]
    col_width_payment = content_area_width_panel // 3
    for item_name, item_due, item_amount in items_payment:
        draw.text((content_area_x_start, current_y), item_name, font=font_body, fill=TEXT_COLOR_LIGHT)
        draw.text((content_area_x_start + col_width_payment, current_y), item_due, font=font_body, fill=TEXT_COLOR_SUBTLE, anchor="ma") # Middle align for due
        draw.text((content_area_x_start + content_area_width_panel - draw.textlength(item_amount, font=font_body), current_y), item_amount, font=font_body, fill=TEXT_COLOR_LIGHT) # Right align amount
        current_y += BODY_FONT_SIZE_QUOTE * LINE_SPACING_FACTOR * 1.2
    current_y += 40
    
    # Divider line (Placeholder, needs actual drawing if required by design)
    # draw.line([(content_area_x_start, current_y), (content_area_x_start + content_area_width_panel, current_y)], fill=TEXT_COLOR_SUBTLE, width=1)
    # current_y += 20

    # Quote ID & Valid Until
    quote_id_text = f"Quote ID: {quote.get('quote_id', 'Q230428')}" # Example if not in quote data
    valid_until_text = f"Valid until: {quote.get('valid_until', '15 May 2025')}"
    draw.text((content_area_x_start, current_y), quote_id_text, font=font_body, fill=TEXT_COLOR_SUBTLE)
    valid_w = draw.textlength(valid_until_text, font=font_body)
    draw.text((panel_x0 + panel_width - CONTENT_PADDING_PANEL - valid_w, current_y), valid_until_text, font=font_body, fill=TEXT_COLOR_SUBTLE)
    current_y += BODY_FONT_SIZE_QUOTE * LINE_SPACING_FACTOR + 60

    # --- Terms & Conditions ---
    terms_title_text = "TERMS & CONDITIONS"
    section_title_w_terms = draw.textlength(terms_title_text, font=font_section_title)
    draw.text((panel_x0 + (panel_width - section_title_w_terms) / 2, current_y), terms_title_text, font=font_section_title, fill=TEXT_COLOR_SUBTLE)
    current_y += SECTION_TITLE_FONT_SIZE_QUOTE * LINE_SPACING_FACTOR + 20

    avg_char_width_body = font_body.size * 0.45 
    wrap_chars_body = int(content_area_width_panel / avg_char_width_body) if avg_char_width_body > 0 else 40
    
    for term in terms_conditions:
        # Add bullet point styling if desired, e.g. by prepending "• "
        display_term = f"• {term}"
        for line in textwrap.wrap(display_term, width=wrap_chars_body):
            draw.text((content_area_x_start, current_y), line, font=font_body, fill=TEXT_COLOR_LIGHT)
            current_y += BODY_FONT_SIZE_QUOTE * LINE_SPACING_FACTOR
        current_y += (BODY_FONT_SIZE_QUOTE * LINE_SPACING_FACTOR) * 0.1 # Smaller gap between T&C items
    current_y += 60

    # --- Approve Button (Placeholder Look) ---
    button_text = "APPROVE & PAY VIA UPI"
    button_font_size = QUOTE_SUB_TEXT_SIZE
    button_font = ImageFont.truetype(FONT_BOLD_QUOTE_PATH, button_font_size) 
    button_text_w = draw.textlength(button_text, font=button_font)
    button_h_padding = 80
    button_v_padding = 30
    button_width = button_text_w + 2 * button_h_padding
    button_height = button_font_size + 2 * button_v_padding
    button_x0 = panel_x0 + (panel_width - button_width) / 2
    button_y0 = panel_y0 + panel_height - CONTENT_PADDING_PANEL - button_height # Position at bottom
    
    # Ensure button doesn't overflow if content is too much
    if button_y0 < current_y + 20: button_y0 = current_y + 20 

    draw.rounded_rectangle(
        (button_x0, button_y0, button_x0 + button_width, button_y0 + button_height),
        radius=button_height // 2, # Pill shape
        fill=PRICE_BOX_BG_COLOR # Use gold color for button
    )
    draw.text(
        (button_x0 + (button_width - button_text_w) / 2, button_y0 + button_v_padding),
        button_text,
        font=button_font,
        fill=PRICE_BOX_TEXT_COLOR
    )

    # --- Save Image ---
    try:
        img_rgb = img.convert('RGB')
        img_rgb.save(output_path, quality=95, dpi=(300,300))
        print(f"Successfully generated quote page: {output_path}")
    except Exception as e:
        print(f"Error saving image {output_path}: {e}")

# Example Usage (if run directly)
if __name__ == '__main__':
    print("Generating example quote page...")
    example_quote = {
        "amount": "1,35,000", 
        "currency": "₹", 
        "details": "PER COUPLE", # This is used for the sub-text in price box
        # New detailed payment structure for the reference image
        "payment_terms": {
            "deposit_due_date": "Due", "deposit_amount": "13,500",
            "balance_due_date": "Due", "balance_amount": "1,21,500"
        },
        "balance_percentage": "90%", # Example
        "quote_id": "Q230428",
        "valid_until": "15 May 2025"
    }
    example_terms = [
        "Booking confirmation subject to availability",
        "Cancellation charges per policy",
        "Travel insurance fires repslarisly with traveller", # Typo from reference?
        "Changes subject to availability and charges",
        "Standard T&Cs apply"
    ]
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.abspath(os.path.join(script_dir, '..'))

    # Use specific fonts defined in constants
    # primary_font = os.path.join(workspace_root, FONT_BODY_QUOTE_PATH)
    bg_image = os.path.join(workspace_root, DEFAULT_LEFT_BG_IMAGE_PATH)
    
    if not os.path.exists(bg_image):
        print(f"Warning: Default background '{DEFAULT_LEFT_BG_IMAGE_PATH}' not found for example. Page will have solid color.")

    generate_quote_page(
        output_filename="page_quote_preview_new.jpg",
        # font_path=primary_font, # Not needed as fonts are hardcoded within function now
        base_output_dir=os.path.join(workspace_root, "outputs"),
        quote=example_quote,
        terms_conditions=example_terms,
        left_bg_image_path=bg_image
    )
    print(f"Example quote page saved to outputs/page_quote_preview_new.jpg") 