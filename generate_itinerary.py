import json
import os
import sys
from PIL import Image, ImageDraw, ImageFont
import glob

INPUT_JSON_PATH = "inputs/itinerary_data.json"
INPUT_DETAILS_PATH = "inputs/itinerary_details.json"

script_dir = os.path.dirname(os.path.abspath(__file__))

# --- Page Generator Imports ---
try:
    from page1.page1 import generate_page1
except ImportError as e:
    print(f"Error importing generate_page1 from page1/page1.py: {e}")
    print("Ensure page1/page1.py exists and page1/__init__.py exists.")
    sys.exit(1)

try:
    import daywisePages.daywise_page_generator as page2_module
    generate_daywise_page_func = page2_module.generate_daywise_page
except ImportError as e:
    print(f"Error importing daywise_page_generator.py from daywisePages: {e}")
    print("Ensure daywisePages/daywise_page_generator.py exists and daywisePages/__init__.py exists.")
    sys.exit(1)
except AttributeError as e:
     print(f"Error: Could not find 'generate_daywise_page' function in daywisePages/daywise_page_generator.py: {e}")
     sys.exit(1)

try:
    from hotels.hotels_page_generator import generate_hotels_page
except ImportError as e:
    print(f"Error importing generate_hotels_page from hotels/hotels_page_generator.py: {e}")
    sys.exit(1)

try:
    from inclusions_exclusions.inc_exc_page_generator import generate_inc_exc_page
except ImportError as e:
    print(f"Error importing generate_inc_exc_page from inclusions_exclusions/inc_exc_page_generator.py: {e}")
    sys.exit(1)

try:
    from quotes.quote_page_generator import generate_quote_page
except ImportError as e:
    print(f"Error importing generate_quote_page from quotes/quote_page_generator.py: {e}")
    sys.exit(1)

# --- Default Data (Fallback if not in JSON) ---
DEFAULT_INCLUSIONS = [
    "Example Inclusion 1: Specify in itinerary_data.json", 
    "Example Inclusion 2: Like flights, accommodation, etc."
]
DEFAULT_EXCLUSIONS = [
    "Example Exclusion 1: Specify in itinerary_data.json", 
    "Example Exclusion 2: Like visa fees, personal expenses, etc."
]
# Updated default hotel details structure
DEFAULT_HOTEL_DETAILS = [{
    "name": "Default Hotel", 
    "stars": 3, 
    "short_address": "123 Default St", 
    "phone_number": "N/A", 
    "email_id": "N/A", 
    "check_in_time": "14:00", 
    "check_out_time": "12:00", 
    "amenities": ["Specify in itinerary_details.json"]
}]
# Updated default quote structure
DEFAULT_QUOTE = {
    "amount": "N/A", 
    "currency": "Specify", 
    "details": "Quote details missing in itinerary_details.json",
    "total_cost_per_person": "N/A",
    "payment_terms": {
        "deposit": "N/A",
        "balance_payment_time": "N/A"
    }
}
DEFAULT_TERMS_CONDITIONS = ["Default Terms: Specify in itinerary_details.json"]

FONT_PATH = os.path.join(script_dir, "fonts", "times.ttf")
# Define specific font paths needed by inc_exc_page_generator
FONT_PATH_PLAYFAIR = os.path.join(script_dir, 'fonts', 'PlayfairDisplay-VariableFont_wght.ttf')
FONT_PATH_ITEM = os.path.join(script_dir, 'fonts', 'Chalkboard-Regular.ttf')
INCEXC_BG_PATH = os.path.join(script_dir, 'inputs', 'incexc_bg.jpg') # Background for Inc/Exc page

OUTPUTS_BASE_DIR = "outputs"

def main():
    # Load Config Data
    try:
        with open(INPUT_JSON_PATH, 'r') as f:
            config_data = json.load(f)
        print(f"Successfully loaded config data from: {INPUT_JSON_PATH}")
    except FileNotFoundError:
        print(f"Error: Config JSON file not found at '{INPUT_JSON_PATH}'")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing config JSON file '{INPUT_JSON_PATH}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred loading config JSON: {e}")
        sys.exit(1)

    # Load Itinerary Details Data
    try:
        with open(INPUT_DETAILS_PATH, 'r') as f:
            details_data = json.load(f)
        print(f"Successfully loaded itinerary details from: {INPUT_DETAILS_PATH}")
    except FileNotFoundError:
        print(f"Error: Itinerary details JSON file not found at '{INPUT_DETAILS_PATH}'")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing details JSON file '{INPUT_DETAILS_PATH}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred loading details JSON: {e}")
        sys.exit(1)
        
    # Extract Configs from config_data
    try:
        page1_config = config_data["page1_config"]
        daywise_config = config_data["daywise_config"]
    except KeyError as e:
        print(f"Error: Missing required config key in JSON ({INPUT_JSON_PATH}): {e}")
        print("Ensure 'page1_config' and 'daywise_config' exist.")
        sys.exit(1)
        
    # Extract Itinerary Details from details_data
    try:
        itinerary_details = details_data["itinerary_details"]
        # Extract data for new pages, using defaults if missing
        inclusions = itinerary_details.get("inclusions", DEFAULT_INCLUSIONS)
        exclusions = itinerary_details.get("exclusions", DEFAULT_EXCLUSIONS)
        hotel_details = itinerary_details.get("hotel_details", DEFAULT_HOTEL_DETAILS)
        quote = itinerary_details.get("quote", DEFAULT_QUOTE)
        terms_conditions = itinerary_details.get("terms_and_conditions", DEFAULT_TERMS_CONDITIONS) # Added terms extraction
    except KeyError as e:
        print(f"Error: Missing required 'itinerary_details' key in JSON ({INPUT_DETAILS_PATH}): {e}")
        sys.exit(1)

    page1_text_overrides = itinerary_details.get("page1_text")
    page1_output_filename = "page_1_cover.jpg"
    page1_output_path = os.path.join(OUTPUTS_BASE_DIR, page1_output_filename) # Define full path
    
    inputs_dir_name = daywise_config.get("INPUTS_DIR_NAME", "inputs")
    # Use the base outputs directory for consistency
    outputs_dir_name = OUTPUTS_BASE_DIR # Keep this assignment for clarity

    if page1_text_overrides:
        page1_config.get("text_content", {}).update(page1_text_overrides)

    print("\n--- Generating Page 1 ---")
    try:
        generate_page1(
            output_filename=page1_output_filename, # Pass filename only
            config_data=page1_config
        )
    except Exception as e:
        print(f"Error generating Page 1: {e}")
        sys.exit(1)

    print("\n--- Generating Itinerary Pages ---")
    
    days = itinerary_details.get("days", [])
    num_itinerary_pages = 0
    if not days:
        print("Warning: No 'days' data found. Skipping itinerary page generation.")
    else:
        num_days = len(days)
        # 2 days per page, ceiling division
        num_itinerary_pages = (num_days + 1) // 2 
        print(f"Found {num_days} days. Generating {num_itinerary_pages} itinerary page(s).")
        
        for i in range(num_itinerary_pages):
            page_number = i + 2
            start_index = i * 2
            end_index = start_index + 2
            
            current_page_days = days[start_index:end_index]
            output_filename = f"page_{page_number}_daywise.jpg"
            output_path = os.path.join(OUTPUTS_BASE_DIR, output_filename) # Define full path
            print(f"-- Generating {output_filename} (Days {start_index + 1}{f'-{end_index}' if end_index <= num_days else ''}) --")
            
            try:
                generate_daywise_page_func(
                    days_data=current_page_days,
                    config_data=daywise_config,
                    output_filename=output_filename # Pass filename only
                )
            except Exception as e:
                print(f"Error generating {output_filename}: {e}")

    # --- Generate Specific Content Pages ---
    print("\n--- Generating Content Pages ---")
    
    # Calculate the starting page number for content pages
    content_start_page = num_itinerary_pages + 2 

    # --- Generate Hotel Details page ---
    hotel_page_number = content_start_page
    hotel_filename_base = f"page_{hotel_page_number}_hotels.jpg"
    print(f"-- Generating {hotel_filename_base} --")
    try:
        generate_hotels_page(
            output_filename=hotel_filename_base,
            base_output_dir=OUTPUTS_BASE_DIR,
            hotel_details=hotel_details # Pass relevant data
        )
    except Exception as e:
        print(f"Error generating Hotel Details page: {e}")

    # --- Generate Inclusions/Exclusions page ---
    inc_exc_page_number = content_start_page + 1
    inc_exc_filename_base = f"page_{inc_exc_page_number}_inc_exc.jpg"
    print(f"-- Generating {inc_exc_filename_base} --")
    try:
        generate_inc_exc_page(
            output_filename=inc_exc_filename_base,
            font_path_title=FONT_PATH_PLAYFAIR,   # Pass title font
            font_path_item=FONT_PATH_ITEM,       # Pass item font
            bg_image_path=INCEXC_BG_PATH,        # Pass background image
            base_output_dir=OUTPUTS_BASE_DIR,
            inclusions_list=inclusions,
            exclusions_list=exclusions
        )
    except Exception as e:
        print(f"Error generating Inclusions/Exclusions page: {e}")

    # --- Generate Quote page ---
    quote_page_number = content_start_page + 2
    quote_filename_base = f"page_{quote_page_number}_quote.jpg"
    print(f"-- Generating {quote_filename_base} --")
    try:
        generate_quote_page(
            output_filename=quote_filename_base,
            font_path=FONT_PATH,
            base_output_dir=OUTPUTS_BASE_DIR,
            quote=quote,                 # Pass relevant data
            terms_conditions=terms_conditions # Pass relevant data
        )
    except Exception as e:
        print(f"Error generating Quote page: {e}")

    print("\n--- Itinerary Generation Complete ---")
    # Construct full paths here just for the final print statements
    page1_output_path = os.path.join(OUTPUTS_BASE_DIR, page1_output_filename)
    hotel_output_path = os.path.join(OUTPUTS_BASE_DIR, hotel_filename_base)
    inc_exc_output_path = os.path.join(OUTPUTS_BASE_DIR, inc_exc_filename_base)
    quote_output_path = os.path.join(OUTPUTS_BASE_DIR, quote_filename_base)

    print(f"Page 1 (Cover) saved to: {page1_output_path}")
    if num_itinerary_pages > 0:
        last_daywise_page = num_itinerary_pages + 1
        print(f"Daywise Pages (page_2 to page_{last_daywise_page}) saved in: {outputs_dir_name}/")
    else:
         last_daywise_page = 1
         
    print(f"Hotel Details page (page_{hotel_page_number}) saved to: {hotel_output_path}")
    print(f"Inclusions/Exclusions page (page_{inc_exc_page_number}) saved to: {inc_exc_output_path}")
    print(f"Quote page (page_{quote_page_number}) saved to: {quote_output_path}")

    # --- Combine JPGs into PDF ---
    print("\n--- Generating PDF ---")
    pdf_output_path = os.path.join(OUTPUTS_BASE_DIR, "itinerary_output.pdf")
    
    # Find all generated JPGs in the base output directory
    image_files = glob.glob(os.path.join(OUTPUTS_BASE_DIR, "page_*.jpg"))

    if not image_files:
        print("Error: No JPG page files found in output directory to create PDF.")
        return # Exit if no images found

    # Helper function to extract page number from filename like 'page_XX_...'
    def get_page_number(filename):
        try:
            # Extract the part between 'page_' and the next '_'
            basename = os.path.basename(filename)
            num_str = basename.split('_')[1]
            return int(num_str)
        except (IndexError, ValueError):
            # Handle cases where filename format is unexpected
            print(f"Warning: Could not extract page number from {filename}. Placing it last.")
            return float('inf') # Place unparsable files at the end

    # Sort files based on extracted page number
    image_files.sort(key=get_page_number)
    
    print(f"Found {len(image_files)} pages to combine:")
    for img_file in image_files:
        print(f" - {os.path.basename(img_file)}")

    try:
        images = [Image.open(f).convert("RGB") for f in image_files] # Convert to RGB for consistency
        
        if not images:
             print("Error: Failed to open any images for PDF creation.")
             return

        first_image = images[0]
        other_images = images[1:]

        first_image.save(
            pdf_output_path, 
            "PDF" ,
            resolution=100.0, 
            save_all=True, 
            append_images=other_images
        )
        print(f"Successfully generated PDF: {pdf_output_path}")

    except FileNotFoundError as e:
         print(f"Error: Could not find image file during PDF creation: {e}")
    except Exception as e:
        print(f"An error occurred during PDF creation: {e}")

if __name__ == "__main__":
    main()