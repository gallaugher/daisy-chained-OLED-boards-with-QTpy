# This code will run two displays off a QT Py RP2040
# A 1.5" OLED 128 x 128 & a 0.96" 128 x 64 OLED.
# The smaller one has to be daisy chained second since it only has
# one STEMMA-QT ports.
# Also, it seems that port order matters, and if you don't see power
# (green light) to second display, switch ports (in & out) on the first
# display.
import time
import math
import board
import displayio
import i2cdisplaybus
import terminalio
from adafruit_display_text import label

# Import display drivers
import adafruit_ssd1327
import adafruit_displayio_ssd1306

# === Try to import bitmap fonts ===
try:
    from adafruit_bitmap_font import bitmap_font

    font = bitmap_font.load_font("/fonts/Arial_Bold_12.bdf")
    USING_CUSTOM_FONT = True
except (ImportError, OSError):
    font = terminalio.FONT
    USING_CUSTOM_FONT = False

# === First setup the static 0.96" display ===
print("Setting up 0.96\" display...")
displayio.release_displays()
i2c = board.STEMMA_I2C()
oled_reset = board.D9

# Initialize the 0.96" monochrome display
display_bus_small = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C, reset=oled_reset)
display_small = adafruit_displayio_ssd1306.SSD1306(
    display_bus_small, width=128, height=32, rotation=0
)

# Create display group
main_group_small = displayio.Group()
display_small.root_group = main_group_small

# White background with black rectangle
BORDER = 5
color_bitmap = displayio.Bitmap(128, 32, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0xFFFFFF  # White

bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
main_group_small.append(bg_sprite)

inner_bitmap = displayio.Bitmap(128 - BORDER * 2, 32 - BORDER * 2, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0x000000  # Black
inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=BORDER, y=BORDER)
main_group_small.append(inner_sprite)

# Add text
text = "0.96\" 128x32"
text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF, x=28, y=32 // 2 - 1)
main_group_small.append(text_area)

# Give the display a moment to render
print("0.96\" display configured!")
time.sleep(1)

# === Now setup the 1.5" grayscale animated display ===
print("Setting up 1.5\" grayscale display...")
displayio.release_displays()
time.sleep(0.1)  # Brief pause to ensure release completes

# Initialize the 1.5" grayscale display
display_bus_large = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3D)
display_large = adafruit_ssd1327.SSD1327(
    display_bus_large, width=128, height=128, rotation=0
)

# Create main group
main_group_large = displayio.Group()
display_large.root_group = main_group_large

# Add text labels
header = label.Label(
    font,
    text="1.5\" 128x128",
    color=0xFFFFFF,
    scale=1,
    x=5,
    y=10,
)
main_group_large.append(header)

pro_label = label.Label(
    font,
    text="+ Easy setup",
    color=0xFFFFFF,
    scale=1,
    x=5,
    y=25,
)
main_group_large.append(pro_label)

con1_label = label.Label(
    font,
    text="- Slow (I2C)",
    color=0xFFFFFF,
    scale=1,
    x=5,
    y=40,
)
main_group_large.append(con1_label)

con2_label = label.Label(
    font,
    text="- Can't be left",
    color=0xFFFFFF,
    scale=1,
    x=5,
    y=55,
)
main_group_large.append(con2_label)

con3_label = label.Label(
    font,
    text="  on. No color.",
    color=0xFFFFFF,
    scale=1,
    x=5,
    y=70,
)
main_group_large.append(con3_label)

# Setup pulsing animation
size = 32
bitmap = displayio.Bitmap(size, size, 256)
palette = displayio.Palette(256)

for i in range(256):
    palette[i] = (i << 16) | (i << 8) | i

tile = displayio.TileGrid(
    bitmap,
    pixel_shader=palette,
    x=(128 - size) // 2,
    y=128 - size - 5
)
main_group_large.append(tile)

print("1.5\" display configured!")
print("Starting animation loop...")

# === Animation loop for the 1.5" display ===
frame = 0
while True:
    # Animate the pulsing effect
    for y in range(size):
        for x in range(size):
            dx = x - size // 2
            dy = y - size // 2
            dist = math.sqrt(dx * dx + dy * dy)
            brightness = int(127 + 127 * math.sin(dist / 3 - frame / 5)) % 256
            bitmap[x, y] = brightness

    frame += 2
    time.sleep(0.05)