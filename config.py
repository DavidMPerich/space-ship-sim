"""Tunable constants for the rocket simulator. Change numbers here, not in game code."""

# Display
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
WINDOW_TITLE = "Rocket to the Moon"

# Colors (R, G, B)
BACKGROUND_COLOR = (10, 10, 40)  # deep friendly blue, not pitch black
DEBUG_TEXT_COLOR = (255, 255, 120)

# Keyboard mapping (pygame key names, see pygame.key.key_code)
KEYS_STEER_LEFT = ["left", "a"]
KEYS_STEER_RIGHT = ["right", "d"]
KEYS_FASTER = ["up", "space", "w"]
KEYS_SLOWER = ["down", "s"]
KEYS_START = ["space", "return"]

# Rocket (distance in made-up "space units", speed in units per second)
# Trip time is TRIP_DISTANCE / speed: 150 s at MIN_SPEED, 100 s at START_SPEED, 75 s at MAX_SPEED.
TRIP_DISTANCE = 900.0
MIN_SPEED = 6.0
START_SPEED = 9.0
MAX_SPEED = 12.0
THROTTLE_RATE = 4.0       # how fast holding a button moves the target speed (units/s per second)
SPEED_EASE_RATE = 3.0     # how eagerly speed follows its target (higher = snappier)
MAX_SPEED_CHANGE = 4.0    # hard limit on speed change (units/s per second)
STEER_EASE_RATE = 4.0     # how eagerly the view follows the stick (higher = snappier)
MAX_FRAME_TIME = 0.1      # seconds; longer frames (hiccups) are treated as this long
