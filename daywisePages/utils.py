from PIL import Image # Only Image needed here
import random

# ================= Helper Functions =================

def center_x(panel_x: int, panel_w: int, text_w: int) -> int:
    """Calculate X coordinate to center text within a panel."""
    return panel_x + (panel_w - text_w) // 2

def split_title_into_lines(title: str, num_lines: int) -> list[str]:
    """Splits a title string into a specified number of lines, balancing word count."""
    words = title.split()
    if not words:
        return []

    total_words = len(words)
    # Ensure num_lines is reasonable
    num_lines = max(1, min(num_lines, total_words))

    avg_len = total_words / num_lines
    lines = []
    start_idx = 0
    for i in range(num_lines):
        # Calculate ideal end index based on average length
        ideal_end_idx = round(avg_len * (i + 1))
        # Ensure the end index doesn't exceed total words
        end_idx = min(ideal_end_idx, total_words)

        # Make sure the last line includes all remaining words
        if i == num_lines - 1:
            end_idx = total_words

        # Prevent creating empty lines if splitting causes gaps
        if start_idx >= total_words:
            break
        # Handle cases where rounding might skip words, ensure at least one word per line if possible
        if start_idx == end_idx and i < num_lines - 1:
             end_idx = start_idx + 1

        # Append the line segment
        if start_idx < end_idx:
            lines.append(" ".join(words[start_idx:end_idx]))

        # Update start index for the next iteration
        start_idx = end_idx

    # Filter out any potentially empty strings just in case
    return [line for line in lines if line]

def generate_jagged_path(start_x: int, y_start: int, y_end: int, jag_config: dict) -> list[tuple[int, int]]:
    """Generates a list of points representing a jagged vertical line."""
    
    # Extract values from the config dictionary with defaults
    amplitude = jag_config.get("JAG_AMPLITUDE", 10)
    segment_len = jag_config.get("SEGMENT_LENGTH", 20)
    
    points = [(start_x, y_start)]
    current_y = y_start
    last_offset_x = start_x # Track the x of the last point

    while current_y < y_end:
        # Determine the height of the current segment
        segment_h = min(segment_len, y_end - current_y)
        # Calculate a random horizontal step
        step = random.randint(-amplitude, amplitude) # Widen range slightly for more jaggedness
        # Calculate the new x-coordinate, clamping it within bounds
        current_offset_x = max(start_x - amplitude, min(start_x + amplitude, last_offset_x + step))

        # Add points for the segment (consider simplifying if zig-zag isn't crucial)
        # Mid-point can create a sharper look
        # points.extend([
        #     (current_offset_x, current_y + segment_h / 2),
        #     (current_offset_x, current_y + segment_h)
        # ])
        # Simpler: just move to the next point
        points.append((current_offset_x, current_y + segment_h))

        last_offset_x = current_offset_x
        current_y += segment_h

    # Ensure the final point is exactly at y_end if needed (might not be necessary depending on usage)
    # if points and points[-1][1] < y_end:
    #     points.append((points[-1][0], y_end))
    # Or adjust the last point
    if points and points[-1][1] != y_end:
         points[-1] = (points[-1][0], y_end)

    return points

def to_ampm(t24: str) -> str:
    """Convert 'HH:MM' (24-hour) to 'H:MM AM/PM' format."""
    try:
        h, m = map(int, t24.split(":"))
        suffix = "AM" if 0 <= h < 12 else "PM"
        h = h % 12 # Get 12-hour format
        if h == 0: # Adjust 0 hour to 12
            h = 12
        return f"{h}:{m:02d} {suffix}"
    except ValueError:
        # Handle potential invalid time format gracefully
        print(f"Warning: Invalid time format encountered: {t24}")
        return t24 # Return original string or a placeholder

def get_dominant_color(img: Image.Image) -> tuple[int, int, int]:
    """Find dominant color by resizing image to 1x1 pixel."""
    # Ensure image is RGB before resizing
    img_rgb = img.convert("RGB")
    # Use NEAREST for speed, as exact color isn't critical for 1x1 average
    img_1x1 = img_rgb.resize((1, 1), Image.Resampling.NEAREST)
    return img_1x1.getpixel((0, 0))

def blend_colors(color1: tuple, color2: tuple, alpha: float = 0.5) -> tuple:
    """Blend two RGB colors using a specified alpha."""
    # Ensure alpha is clamped between 0 and 1
    alpha = max(0.0, min(1.0, alpha))
    return tuple(int(c1 * (1 - alpha) + c2 * alpha) for c1, c2 in zip(color1, color2))

def adjust_color_brightness(color: tuple, factor: float) -> tuple:
    """Adjust color brightness. Factor > 1 makes it brighter, < 1 darker."""
    return tuple(max(0, min(255, int(c * factor))) for c in color)

def wrap_text(draw_obj, text: str, font, max_width: int) -> list[str]:
    """Wrap text to fit within max_width using the provided draw object and font."""
    lines = []
    words = text.split()
    if not words:
        return []

    current_line = words[0]
    for word in words[1:]:
        test_line = f"{current_line} {word}"
        try:
            # Use textbbox for more accurate width calculation if available
            left, top, right, bottom = draw_obj.textbbox((0, 0), test_line, font=font)
            w = right - left
        except AttributeError:
            # Fallback for older Pillow versions
            w, _ = draw_obj.textsize(test_line, font=font)

        if w <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    lines.append(current_line) # Add the last formed line
    return lines 