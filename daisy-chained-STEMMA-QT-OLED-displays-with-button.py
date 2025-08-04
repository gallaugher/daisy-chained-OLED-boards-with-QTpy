# daisy-chained-STEMMA-QT-OLED-displays-with-button.py
# This code will run two displays off a QT Py RP2040
# A 1.5" OLED 128 x 128 & a 0.96" 128 x 64 OLED.
# The smaller one has to be daisy chained second since it only has
# one STEMMA-QT ports.
# Also, it seems that port order matters, and if you don't see power
# (green light) to second display, switch ports (in & out) on the first
# display.
# In order to prevent burn-in, the displays turn off after 60 seconds, but
# pressing the button attachedc to A0 on the QT Py will restart both displays
# and reset the 60 second clock. Time can be adjusted with DISPLAY_TIMEOUT_SECONDS
import time
import math
import time
import board
import displayio
import i2cdisplaybus
import terminalio
import digitalio
import gc
from adafruit_debouncer import Button
from adafruit_display_text import label

# Import display drivers
import adafruit_ssd1327
import adafruit_displayio_ssd1306

# === CONFIGURATION ===
DISPLAY_TIMEOUT_SECONDS = 60  # Change this to test with shorter times (e.g., 5 or 10)

# === Try to import bitmap fonts ===
try:
    from adafruit_bitmap_font import bitmap_font

    font = bitmap_font.load_font("/fonts/Arial_Bold_12.bdf")
    USING_CUSTOM_FONT = True
except (ImportError, OSError):
    font = terminalio.FONT
    USING_CUSTOM_FONT = False
    print("font unavailable, using terminalio.")


class DisplayManager:
    def __init__(self):
        self.i2c = None
        self.displays = []
        self.display_buses = []

    def setup_displays(self):
        global size
        global bitmap

        # Clear any existing display references first
        self.displays.clear()
        self.display_buses.clear()

        # === First setup the static 0.96" display ===
        print("Setting up 0.96\" display...")
        displayio.release_displays()
        self.i2c = board.STEMMA_I2C()
        oled_reset = board.D9

        # Initialize the 0.96" monochrome display
        display_bus_small = i2cdisplaybus.I2CDisplayBus(self.i2c, device_address=0x3C, reset=oled_reset)
        display_small = adafruit_displayio_ssd1306.SSD1306(
            display_bus_small, width=128, height=32, rotation=0
        )
        self.displays.append(display_small)
        self.display_buses.append(display_bus_small)

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
        display_bus_large = i2cdisplaybus.I2CDisplayBus(self.i2c, device_address=0x3D)
        display_large = adafruit_ssd1327.SSD1327(
            display_bus_large, width=128, height=128, rotation=0
        )
        self.displays.append(display_large)
        self.display_buses.append(display_bus_large)

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

    def shutdown_displays(self):
        """Properly shut down all displays and free resources"""
        print("Shutting down displays...")

        # Step 1: Clear the currently managed display (large one)
        for i, display in enumerate(self.displays):
            try:
                clear_group = displayio.Group()
                black_bitmap = displayio.Bitmap(display.width, display.height, 1)
                black_palette = displayio.Palette(1)
                black_palette[0] = 0x000000  # Black
                black_sprite = displayio.TileGrid(black_bitmap, pixel_shader=black_palette, x=0, y=0)
                clear_group.append(black_sprite)
                display.root_group = clear_group
                time.sleep(0.2)
                print(f"Large display cleared successfully")
            except Exception as e:
                print(f"Error clearing large display: {e}")

        # Step 2: Release displays and re-initialize the small display just to clear it
        displayio.release_displays()
        time.sleep(0.1)

        try:
            # Re-initialize the small display
            oled_reset = board.D9
            display_bus_small = i2cdisplaybus.I2CDisplayBus(self.i2c, device_address=0x3C, reset=oled_reset)
            display_small = adafruit_displayio_ssd1306.SSD1306(
                display_bus_small, width=128, height=32, rotation=0
            )

            # Clear it with black
            clear_group_small = displayio.Group()
            black_bitmap_small = displayio.Bitmap(128, 32, 1)
            black_palette_small = displayio.Palette(1)
            black_palette_small[0] = 0x000000  # Black
            black_sprite_small = displayio.TileGrid(black_bitmap_small, pixel_shader=black_palette_small, x=0, y=0)
            clear_group_small.append(black_sprite_small)
            display_small.root_group = clear_group_small
            time.sleep(0.5)  # Give time for clearing
            print("Small display cleared successfully")

        except Exception as e:
            print(f"Error clearing small display: {e}")

        # Step 3: Final cleanup
        if self.i2c:
            try:
                self.i2c.deinit()
            except Exception as e:
                print(f"Error deinitializing I2C: {e}")

        # Clear references
        self.displays.clear()
        self.display_buses.clear()
        self.i2c = None

        # Final release
        displayio.release_displays()
        gc.collect()
        print("All displays shut down and cleared")


size = 0  # placeholder
bitmap = 0  # placeholder

# Usage example
display_manager = DisplayManager()

# call setup_displays
display_manager.setup_displays()
displays_are_on = True
display_start_time = time.monotonic()  # Track when displays started

# === Animation loop for the 1.5" display ===
frame = 0

# configure display's on/off button
button_input = digitalio.DigitalInOut(board.A0)  # Wired to GP15
button_input.switch_to_input(digitalio.Pull.UP)  # Note: Pull.UP for external buttons
button = Button(button_input)  # NOTE: False for external buttons

while True:
    button.update()
    if button.pressed:
        print("Button pressed - restarting displays...")
        if displays_are_on:
            display_manager.shutdown_displays()
        display_manager.setup_displays()
        displays_are_on = True
        display_start_time = time.monotonic()  # Reset timer
        print(f"Displays restarted - will auto-shutdown in {DISPLAY_TIMEOUT_SECONDS} seconds")

    # Check for timeout
    if displays_are_on:
        elapsed = time.monotonic() - display_start_time
        if elapsed >= DISPLAY_TIMEOUT_SECONDS:
            print(f"Auto-shutdown: {DISPLAY_TIMEOUT_SECONDS} seconds elapsed")
            display_manager.shutdown_displays()
            displays_are_on = False

    if displays_are_on:
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