"""From Home Assistant."""

from .const import COLORS, RGBColor


def color_name_to_rgb(color_name: str) -> RGBColor:
    """Convert color name to RGB hex value."""
    # COLORS map has no spaces in it, so make the color_name have no
    # spaces in it as well for matching purposes
    hex_value = COLORS.get(color_name.replace(" ", "").lower())
    if not hex_value:
        raise ValueError("Unknown color")

    return hex_value
