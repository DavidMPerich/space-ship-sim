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
STAR_TURN_SPREAD = 0.6    # how far past the edge wrapped stars are scattered (smaller = fuller sky in turns)
STAR_FOCAL = 640          # pixels; higher = more zoomed in
STAR_RATE = 0.035         # star depth per unit of distance flown, so stars and moon share one speed
STAR_STOP_RATE = 1.5      # how eagerly the stars come to rest after arrival
STAR_FADE_DEPTH = 0.4     # stars reach full brightness after travelling this far
STAR_MAX_SIZE = 10        # pixels, for the nearest stars
STAR_COLORS = [(255, 255, 255), (255, 253, 245), (255, 250, 230), (255, 246, 214)]  # white to soft yellow

# Turning back toward the moon
RETURN_RATE = 0.8         # how eagerly the ship turns back when the stick is released (above 1 overshoots)
RETURN_MAX_STEER = 0.8    # strongest automatic turn, as a share of full steering
# Near the end, turning away gets gently limited so the moon is always in view at arrival
APPROACH_START = 0.6      # progress where the limit starts closing in
APPROACH_END = 0.95       # progress where it is tightest
APPROACH_HEADING = 0.2    # tightest limit, radians
APPROACH_SOFTNESS = 0.3   # radians over which steering hands over to the automatic turn

# Moon
MOON_IMAGE = "assets/images/moon.png"  # drawn instead if this file is missing
MOON_MIN_SIZE = 28        # pixels across at launch (even); smaller = more of the growth comes near the end
MOON_MAX_SIZE = 560       # pixels across at arrival (even number)
MOON_CACHE_SIZE = 8       # how many scaled moons to keep
MOON_COLOR = (238, 234, 214)
MOON_CRATER_COLOR = (208, 203, 182)
MOON_CRATERS = [          # x, y, radius as shares of the moon's width
    (0.34, 0.30, 0.10), (0.66, 0.40, 0.07), (0.45, 0.66, 0.12),
    (0.74, 0.68, 0.06), (0.20, 0.55, 0.05), (0.56, 0.17, 0.045),
]

# Progress indicator
INDICATOR_MARGIN = 160        # pixels from the screen sides to the ends of the track
INDICATOR_BOTTOM = 60         # pixels from the bottom of the screen
INDICATOR_ICON_SIZE = 72
INDICATOR_DOTS = 21
INDICATOR_DOT_RADIUS = 5
EARTH_OCEAN_COLOR = (50, 130, 230)
EARTH_LAND_COLOR = (95, 175, 85)
EARTH_SHADOW = 0.72           # brightness at the shaded edge (1 = no shading)
EARTH_LAND = [                # outlines, as shares of the Earth's width
    [(0.20, 0.26), (0.22, 0.18), (0.34, 0.10), (0.50, 0.08), (0.62, 0.13), (0.66, 0.20), (0.57, 0.23),
     (0.66, 0.28), (0.60, 0.34), (0.54, 0.40), (0.53, 0.47), (0.49, 0.42), (0.43, 0.43), (0.42, 0.48),
     (0.47, 0.52), (0.52, 0.57), (0.44, 0.55), (0.36, 0.47), (0.31, 0.38), (0.25, 0.32)],      # North America
    [(0.48, 0.55), (0.58, 0.53), (0.66, 0.58), (0.76, 0.64), (0.71, 0.72), (0.66, 0.76), (0.62, 0.84),
     (0.57, 0.94), (0.53, 0.92), (0.55, 0.80), (0.52, 0.71), (0.46, 0.64)],                    # South America
    [(0.64, 0.05), (0.74, 0.08), (0.76, 0.15), (0.69, 0.19), (0.64, 0.12)],                    # Greenland
    [(0.90, 0.38), (1.00, 0.32), (1.00, 0.62), (0.94, 0.56), (0.87, 0.48)],                    # Africa
]
EARTH_ICE = [(0.34, -0.05, 0.36, 0.11), (0.32, 0.94, 0.36, 0.11)]       # x, y, width, height
EARTH_CLOUDS = [                                                        # x, y, width, height
    (0.10, 0.42, 0.22, 0.045), (0.16, 0.46, 0.26, 0.04), (0.56, 0.42, 0.28, 0.045), (0.64, 0.46, 0.24, 0.035),
    (0.14, 0.72, 0.28, 0.05), (0.24, 0.77, 0.20, 0.035), (0.68, 0.24, 0.20, 0.04), (0.64, 0.80, 0.22, 0.04),
]
INDICATOR_DONE_COLOR = (255, 220, 120)
INDICATOR_TODO_COLOR = (90, 90, 140)
