import os
import glob
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import textwrap # Import textwrap for potential long lines

# Import card drawing functions (Updated)
from .card_drawing import draw_main_info_card, draw_checkin_card

# --- Constants ---
A4_WIDTH_MM = 210
A4_HEIGHT_MM = 297
DPI = 300
MM_TO_INCH = 1 / 25.4

PAGE_WIDTH_PX = int(A4_WIDTH_MM * MM_TO_INCH * DPI)  # Approx 2480
PAGE_HEIGHT_PX = int(A4_HEIGHT_MM * MM_TO_INCH * DPI) # Approx 3508
SAFE_MARGIN_MM = 15
SAFE_MARGIN_PX = int(SAFE_MARGIN_MM * MM_TO_INCH * DPI) # Approx 177

TEXT_DARK = (33, 33, 33) # #212121
TEXT_LIGHT = (255, 255, 255) # #FFFFFF

# Font paths (assuming they are accessible)
# TODO: Update with actual paths or make them parameters
FONT_PATH_PLAYFAIR = "fonts/PlayfairDisplay-Bold.ttf" # Try loading bold variant
FONT_PATH_PLAYFAIR_ITALIC = "fonts/PlayfairDisplay-BoldItalic.ttf" # Try loading bold italic variant
FONT_PATH_INTER = "fonts/Inter-SemiBold.ttf"         # Try loading semibold variant
HERO_IMAGE_SEARCH_PATH = "inputs/hotel_bg.*"

def generate_hotels_page(output_filename: str, base_output_dir: str, hotel_details: dict): # Simplified input for now
    """Generates a premium hotel details page resembling a brochure."""

    output_path = os.path.join(base_output_dir, output_filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True) # Ensure dir exists

    # --- 1. Canvas Setup ---
    img = Image.new('RGBA', (PAGE_WIDTH_PX, PAGE_HEIGHT_PX), (0, 0, 0, 0)) # Use RGBA for compositing

    # --- 2. Hero Image (Layer 1) ---
    try:
        hero_image_path = None
        possible_files = glob.glob(HERO_IMAGE_SEARCH_PATH)
        if possible_files:
            hero_image_path = possible_files[0] # Take the first match
            print(f"Found hero image: {hero_image_path}")
        else:
             raise FileNotFoundError(f"Hero image not found at {HERO_IMAGE_SEARCH_PATH}")

        hero_img = Image.open(hero_image_path).convert("RGBA") # Convert to RGBA
        hero_w, hero_h = hero_img.size
        target_w, target_h = PAGE_WIDTH_PX, PAGE_HEIGHT_PX
        target_aspect = target_h / target_w
        hero_aspect = hero_h / hero_w

        # --- Corrected Scaling and Cropping Logic ---
        scale_factor = 1.0
        if hero_aspect < target_aspect: 
            # Hero is wider than target aspect ratio (e.g., landscape)
            # Scale based on height to ensure it fills vertically
            scale_factor = target_h / hero_h
            print(f"Hero wider than target. Scaling by height factor: {scale_factor:.4f}")
        else: 
            # Hero is taller than or same as target aspect ratio (e.g., portrait)
            # Scale based on width to ensure it fills horizontally
            scale_factor = target_w / hero_w
            print(f"Hero taller than/matches target. Scaling by width factor: {scale_factor:.4f}")

        # Resize maintaining aspect ratio
        new_w = int(hero_w * scale_factor)
        new_h = int(hero_h * scale_factor)
        hero_resized = hero_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        print(f"Resized hero to: {new_w}x{new_h}")

        # Center crop the resized image to target dimensions
        crop_x = (new_w - target_w) // 2
        crop_y = (new_h - target_h) // 2
        
        # Ensure crop coordinates are non-negative (can happen with float precision)
        crop_x = max(0, crop_x)
        crop_y = max(0, crop_y)
        
        crop_box = (crop_x, crop_y, crop_x + target_w, crop_y + target_h)
        print(f"Final crop box: {crop_box}")
        
        # Perform the final crop
        hero_final = hero_resized.crop(crop_box)
        
        # Sanity check final size
        if hero_final.size != (target_w, target_h):
             print(f"Warning: Final hero size {hero_final.size} doesn't match target {(target_w, target_h)}. Resizing again.")
             hero_final = hero_final.resize((target_w, target_h), Image.Resampling.LANCZOS)

        # --- Darken Hero Image ---
        enhancer = ImageEnhance.Brightness(hero_final)
        hero_final = enhancer.enhance(0.8) # Reduce brightness by 30%

        # Paste onto the main canvas
        img.paste(hero_final, (0, 0))

    except FileNotFoundError as e:
        print(f"Error: {e}. Cannot proceed without hero image.")
        # Optionally: draw a placeholder background
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0,0), (PAGE_WIDTH_PX, PAGE_HEIGHT_PX)], fill=(100,100,100), outline=None)
        draw.text((50,50), "Hero Image Not Found", fill=(255,0,0), font=ImageFont.load_default(size=50))
        # Early exit or continue with placeholder? Let's exit for now.
        return
    except Exception as e:
        print(f"Error processing hero image {hero_image_path}: {e}")
        # Draw placeholder and exit
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0,0), (PAGE_WIDTH_PX, PAGE_HEIGHT_PX)], fill=(100,100,100), outline=None)
        draw.text((50,50), "Error loading Hero Image", fill=(255,0,0), font=ImageFont.load_default(size=50))
        return

    # --- Font Loading ---
    fonts = {}
    # Moved font loading here, after potentially exiting early if hero fails
    try:
        # Increased font sizes (approx 10-15%)
        fonts['playfair_huge'] = ImageFont.truetype(FONT_PATH_PLAYFAIR, 270) # HUGE name font (Increased size)
        fonts['playfair_regular'] = ImageFont.truetype(FONT_PATH_PLAYFAIR, 70) # Increased size
        fonts['playfair_italic'] = ImageFont.truetype(FONT_PATH_PLAYFAIR_ITALIC, 70) # Increased size
        fonts['inter_star'] = ImageFont.truetype(FONT_PATH_INTER, 42) # Increased size
        fonts['inter_body'] = ImageFont.truetype(FONT_PATH_INTER, 42)     # Increased size
        fonts['inter_large_detail'] = ImageFont.truetype(FONT_PATH_INTER, 70) # Increased size
        fonts['inter_xl_detail'] = ImageFont.truetype(FONT_PATH_INTER, 90)    # Increased size
        fonts['inter_small'] = ImageFont.truetype(FONT_PATH_INTER, 32)    # Increased size
        fonts['inter_label'] = ImageFont.truetype(FONT_PATH_INTER, 36)    # Increased size
        # We might need more variations later (bold, etc.)
    except IOError as e:
        print(f"Warning: One or more font files not found ({e}). Using default fonts.")
        # Fallback to default fonts - Increased sizes here too
        fonts['playfair_huge'] = ImageFont.load_default(size=270) # Increased fallback size
        fonts['playfair_regular'] = ImageFont.load_default(size=70)
        fonts['playfair_italic'] = ImageFont.load_default(size=70)
        fonts['inter_star'] = ImageFont.load_default(size=42)
        fonts['inter_body'] = ImageFont.load_default(size=42)
        fonts['inter_large_detail'] = ImageFont.load_default(size=70) # Large detail font fallback
        fonts['inter_xl_detail'] = ImageFont.load_default(size=90)    # XL detail font fallback
        fonts['inter_small'] = ImageFont.load_default(size=32)
        fonts['inter_label'] = ImageFont.load_default(size=36)


    # --- Initialize Draw context ---
    # We'll re-initialize it when needed, especially after pasting images
    # draw = ImageDraw.Draw(img)


    # --- Layer 2: Frosted-Glass Info Card #1 – Main Info --- # Updated comment
    page_dims = (PAGE_WIDTH_PX, PAGE_HEIGHT_PX)
    hotel_info_to_draw = None
    if isinstance(hotel_details, list) and hotel_details:
        hotel_info_to_draw = hotel_details[0]
        if len(hotel_details) > 1:
            print(f"Warning: Multiple hotels found in input, drawing only the first: {hotel_info_to_draw.get('name')}")
    elif isinstance(hotel_details, dict):
        hotel_info_to_draw = hotel_details

    if hotel_info_to_draw:
        card1_bounding_box = None # Initialize
        try:
            # Call the main info card function and get its box
            card1_bounding_box = draw_main_info_card(img, hotel_info_to_draw, fonts, page_dims)
        except Exception as e:
            print(f"Error drawing Main Info card: {e}")

        # --- Layer 3: Frosted-Glass Info Card #2 – Check-in/out --- # Added new layer
        if card1_bounding_box: # Only draw if card 1 was drawn successfully
            print("Attempting to draw Checkin Card...") # DEBUG PRINT
            try:
                 # Call the check-in card function, passing card 1's box
                draw_checkin_card(img, hotel_info_to_draw, fonts, page_dims, card1_bounding_box)
                print("Call to draw_checkin_card completed.") # DEBUG PRINT
            except Exception as e:
                print(f"Error drawing Checkin card: {e}")
        else:
             print("Skipping Checkin card because Main Info card failed or was skipped.") # DEBUG PRINT
    else:
        print("Warning: No valid hotel details found to draw cards.")

    # --- Layer 4: Amenity Ribbon (Placeholder) --- # Renumbered layer
    # TODO: Implement gradient (optional), icon loading/placement, label drawing

    # --- Save Image ---
    try:
        # Ensure final image is RGB for JPEG saving if needed, or save RGBA PNG
        final_img = img.convert('RGB') # Convert before saving as JPEG
        final_img.save(output_path, quality=95, dpi=(DPI, DPI)) # Add quality and DPI
        print(f"Successfully generated initial hotels page: {output_path}")
    except Exception as e:
        print(f"Error saving image {output_path}: {e}")

# --- Helper Functions (Example: Rounded Rectangle Mask) ---
# Moved to card_drawing.py
# def create_rounded_rectangle_mask(size, radius, *, inner_fill=255, outer_fill=0):
#    ...


# Example Usage (if run directly)
if __name__ == '__main__':
    print("Generating example hotel page...")
    # Create dummy input folder/file if doesn't exist for testing
    if not os.path.exists("inputs"): os.makedirs("inputs")
    if not glob.glob("inputs/hotel_bg.*"):
        try:
            print("Creating dummy hero image 'inputs/hotel_bg.png'")
            dummy_img = Image.new('RGB', (3000, 2000), 'blue')
            dummy_draw = ImageDraw.Draw(dummy_img)
            dummy_draw.text((10,10), "Dummy Hero BG", fill="white")
            dummy_img.save("inputs/hotel_bg.png")
        except Exception as e:
            print(f"Could not create dummy hero image: {e}")

    # Define dummy hotel details
    dummy_hotel_data = {
        "name": "The Oberoi Bali (Example)",
        "stars": 5,
        "short_address": "Seminyak, Bali",
        "phone_number": "+62 361 730361",
        "email_id": "reservations@oberoibali.com",
        "check_in_time": "14 Jun 15:00", # Combined for example card 2 later
        "check_out_time": "18 Jun 12:00", # Combined for example card 2 later
        "amenities": ["Wi-Fi", "Restaurant", "Spa", "Gym", "Kids Club", "Parking"] # Example
    }

    generate_hotels_page(
        output_filename="hotel_page_preview.jpg",
        base_output_dir="output",
        hotel_details=dummy_hotel_data
    )
    print("Check 'output/hotel_page_preview.jpg'") 