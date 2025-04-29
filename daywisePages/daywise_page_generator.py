#!/usr/bin/env python3
# Generates a portrait itinerary page with 1 or 2 days

import os
from PIL import Image, ImageDraw

# Import drawing functions from the 'page2' subdirectory
# We assume this import works correctly
# from page2 import drawing # Old import
from . import drawing # Updated relative import

# ================= Main Execution =================

# Modified to accept a list of day data dictionaries (max 2) and config data
# def generate_page2(days_data: list[dict], config_data: dict, output_filename: str): # Old name
def generate_daywise_page(days_data: list[dict], config_data: dict, output_filename: str):
    """Generates an itinerary page with up to two days from provided data and config."""
    output_dir_name = config_data.get("OUT_DIR_NAME", "outputs")
    os.makedirs(output_dir_name, exist_ok=True)
    
    page_w = config_data.get("PAGE_W", 2480)
    page_h = config_data.get("PAGE_H", 3508)
    bg_color = tuple(config_data.get("PAGE_BG_COLOR", [246, 235, 215]))
    
    page = Image.new("RGB", (page_w, page_h), bg_color)
    draw = ImageDraw.Draw(page)

    input_dir_name = config_data.get("INPUTS_DIR_NAME", "inputs")
    
    for idx, day_data in enumerate(days_data):
        hero_image_path = day_data.get('hero_image')
        if hero_image_path and not os.path.isabs(hero_image_path) and not hero_image_path.startswith(('http://', 'https://')):
             day_data['hero_image'] = os.path.join(input_dir_name, hero_image_path)
        elif not hero_image_path:
            print(f"Warning: 'hero_image' missing for day {day_data.get('day', f'#{idx+1}')}")
            day_data['hero_image'] = None

        try:
            drawing.draw_hero_section(page, draw, day_data, idx, config_data)
        except TypeError as e:
            print(f"Error calling draw_hero_section (check signature?): {e}")
        except Exception as e:
            print(f"Error drawing hero section for Day {day_data.get('day', f'#{idx+1}')}: {e}")

    if len(days_data) >= 1:
        try:
            drawing.draw_activities(draw, days_data[0], 0, config_data)
        except TypeError as e:
            print(f"Error calling draw_activities (check signature?): {e}")
        except Exception as e:
            print(f"Error drawing activities for Day {days_data[0].get('day', '#1')}: {e}")
            
    if len(days_data) == 2:
        try:
            drawing.draw_activities(draw, days_data[1], 1, config_data)
        except TypeError as e:
             print(f"Error calling draw_activities (check signature?): {e}")
        except Exception as e:
            print(f"Error drawing activities for Day {days_data[1].get('day', '#2')}: {e}")
    elif len(days_data) < 1:
        print("Warning: No day data provided to generate_daywise_page.")

    output_path = os.path.join(output_dir_name, output_filename)
    try:
        quality = config_data.get("OUTPUT_QUALITY", 95)
        dpi_tuple = tuple(config_data.get("OUTPUT_DPI", [300, 300]))
        page.save(output_path, "JPEG", quality=quality, dpi=dpi_tuple)
        print(f"Page saved: {output_path}")
    except Exception as e:
        print(f"Error saving page {output_path}: {e}")

# Example direct execution block (commented out)
# if __name__ == "__main__":
#     # Load test data (e.g., from a JSON or a dedicated data module)
#     # test_config = {...}
#     # test_days_data = [{...}, {...}]
#     # test_output_filename = "daywise_test.jpg"
#     # generate_daywise_page(test_days_data, test_config, test_output_filename)
#     pass
