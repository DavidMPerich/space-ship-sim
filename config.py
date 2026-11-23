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
STEER_EASE_RATE = 4.0     # how eagerly turning follows the stick (higher = snappier)
TURN_RATE = 0.5           # radians per second at full steering (0.5 is a full circle in about 13 s)
MAX_FRAME_TIME = 0.1      # seconds; longer frames (hiccups) are treated as this long

# Starfield (depth runs from STAR_FAR, where stars fade in, to STAR_NEAR, where they pass the camera)
STAR_COUNT = 400
STAR_FAR = 1.0
STAR_NEAR = 0.03
STAR_MIN_RADIUS = 0.08    # closest a new star starts to the flight path
STAR_MAX_RADIUS = 1.2
STAR_MIN_HEIGHT = 0.018   # gap above/below; big enough that stars leave the screen before recycling
STAR_TURN_EDGE = 1.05     # x/z just off screen, where stars wrap to the other side while turning
STAR_FOCAL = 640          # pixels; higher = more zoomed in
STAR_SLOW_RATE = 0.15     # depth per second at MIN_SPEED
STAR_FAST_RATE = 0.5      # depth per second at MAX_SPEED
STAR_FADE_DEPTH = 0.4     # stars reach full brightness after travelling this far
STAR_MAX_SIZE = 10        # pixels, for the nearest stars
STAR_COLORS = [(255, 255, 255), (255, 253, 245), (255, 250, 230), (255, 246, 214)]  # white to soft yellow
