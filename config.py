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

# Starfield (depth runs from STAR_FAR, where stars fade in, to STAR_NEAR, where they pass the camera)
STAR_COUNT = 400
STAR_FAR = 1.0
STAR_NEAR = 0.03
STAR_MIN_RADIUS = 0.08    # distance from the flight path; big enough that stars leave the screen before recycling
STAR_MAX_RADIUS = 1.2
STAR_FOCAL = 640          # pixels; higher = more zoomed in
STAR_SLOW_RATE = 0.15     # depth per second at MIN_SPEED
STAR_FAST_RATE = 0.5      # depth per second at MAX_SPEED
STREAK_SLOW = 0.02        # streak length at MIN_SPEED, as a share of the star's depth
STREAK_FAST = 0.3         # streak length at MAX_SPEED, as a share of the star's depth
STAR_FADE_DEPTH = 0.4     # stars reach full brightness after travelling this far
STAR_MAX_SIZE = 10        # pixels, for the nearest stars
STAR_COLORS = [(255, 255, 255), (255, 240, 170), (170, 215, 255), (255, 190, 220)]
STEER_SHIFT = 250         # pixels the view slides at full steering
