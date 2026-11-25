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
MOON_COLOR = (252, 250, 242)
MOON_SHADOW = 0.72        # brightness at the shaded edge (1 = no shading)
MOON_SEED = 7             # different numbers give different craters
MOON_CRATER_COUNT = 420
MOON_CRATER_MIN = 0.008   # crater radius as a share of the moon's radius
MOON_CRATER_MAX = 0.055
MOON_RAY_CENTER = (0.46, 0.83)  # bright young crater, as shares of the moon's width
MOON_RAY_COUNT = 22
MOON_MARIA_COLOR = (150, 149, 150)
MOON_MARIA_STRENGTH = 0.5  # how visible the dark plains are (0 = none, 1 = solid)
MOON_MARIA = [            # dark plains: x, y, half width, half height as shares of the moon's width
    (0.36, 0.28, 0.14, 0.12), (0.58, 0.31, 0.08, 0.08), (0.67, 0.42, 0.11, 0.09), (0.84, 0.35, 0.04, 0.055),
    (0.79, 0.53, 0.06, 0.09), (0.69, 0.58, 0.05, 0.05), (0.18, 0.42, 0.10, 0.18), (0.25, 0.65, 0.06, 0.06),
    (0.40, 0.64, 0.10, 0.07), (0.32, 0.52, 0.09, 0.08), (0.47, 0.13, 0.17, 0.025),
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

# Scenes (times in seconds)
AUTO_START_DELAY = 2.0        # the roof opens by itself after waiting this long for a button
COUNTDOWN_STEP = 1.0          # how long each number shows
COUNTDOWN_WORDS = ["5", "4", "3", "2", "1"]
BLAST_OFF_TEXT = "BLAST OFF!"
BLAST_OFF_TIME = 2.0          # shown while the flight begins
BLAST_OFF_FADE = 0.6          # the last part of that, fading away
ARRIVAL_TEXT = "You made it to the Moon!"
ARRIVAL_PAUSE = 12.0          # celebration length before starting over
SCENE_FADE = 1.0              # gentle fade between trips
LAUNCH_RATE = 1.0             # how eagerly the stars get moving at launch

# Text
TEXT_COLOR = (255, 225, 110)
TEXT_OUTLINE_COLOR = (35, 30, 90)
TEXT_OUTLINE = 6              # pixels
TEXT_MAX_WIDTH = 0.85         # share of the screen width; longer text is made smaller to fit
COUNTDOWN_SIZE = 420          # font sizes
BLAST_OFF_SIZE = 240
ARRIVAL_SIZE = 130
ARRIVAL_TEXT_Y = 95
POP_SIZE = 0.15               # how much bigger numbers are when they appear
ARRIVAL_POP = 0.1             # how much the arrival text bounces for a button press
POP_PRESS = 0.6               # share of that for a button press
POP_RATE = 5.0                # how quickly they settle
BOB_HEIGHT = 10               # pixels of gentle up and down
BOB_SPEED = 2.5               # radians per second
LEAN_DISTANCE = 80            # pixels the countdown numbers follow the stick
LEAN_RATE = 5.0               # how eagerly they follow it

# Sound (volumes from 0 to 1; replace any file in the folder with your own .wav of the same name)
SOUND_FOLDER = "assets/sounds"
MAX_VOLUME = 0.6              # nothing ever plays louder than this
SOUND_RATE = 44100
SOUND_BUFFER = 1024           # smaller = quicker beeps, but may crackle on a slow Pi
SOUND_CHANNELS = 14           # how many sounds can play at once
SOUND_EASE_RATE = 8.0         # how quickly steady sounds change volume
SOUND_VOLUMES = {"button": 0.22, "count": 0.45, "roof_stop": 0.4, "touchdown": 0.55, "jingle": 0.45}
ROOF_VOLUME = 0.35
THRUSTER_VOLUME = 0.6         # at the strongest moment of liftoff
LANDING_THRUST_VOLUME = 0.35
LANDING_THRUST_RISE = 2.5     # seconds
LANDING_THRUST_FALL = 1.5     # seconds
ENGINE_SLOW_VOLUME = 0.12
ENGINE_FAST_VOLUME = 0.28
JINGLE_DELAY = 1.0            # seconds after touchdown

# Landing
LANDING_TIME = 7.0            # seconds from the end of the flight to touchdown
LANDING_SIZE = 5200           # pixels across the moon has grown to at touchdown
LANDING_HORIZON = 430         # screen height of the horizon after landing
GROUND_FADE = (0.68, 0.96)    # shares of the landing over which the detailed ground appears
GROUND_COLOR = (205, 204, 202)
GROUND_EXTRA = 130            # extra ground below the screen, seen while the horizon settles
GROUND_CRATERS = 90
GROUND_ROCKS = 90
DUST_COLOR = (200, 198, 194)
DUST_COUNT = 14
DUST_SIZE = 320               # pixels
DUST_RISE = 130               # pixels
DUST_LEAD = 1.2               # starts this long before touchdown
DUST_TIME = 4.0

# Launch: hangar roof (pixels are for the roof as first seen)
DOOR_TIME = 4.0               # seconds for the roof to open
HANGAR_HALF_WIDTH = 500
HANGAR_HALF_HEIGHT = 250
HANGAR_RISE = 8.0             # how quickly the opening passes by after liftoff
HANGAR_SLATS = 6              # panels per door
HANGAR_LAMPS = 8              # along the top
HANGAR_WALL_COLOR = (62, 72, 104)
HANGAR_RIM_COLOR = (150, 162, 190)
HANGAR_LINE_COLOR = (48, 56, 84)
HANGAR_DOOR_COLORS = [(128, 142, 172), (114, 128, 158)]
HANGAR_EDGE_COLOR = (245, 195, 70)
HANGAR_LAMP_OFF = (150, 130, 90)
HANGAR_LAMP_ON = (255, 235, 150)

# Launch: sky (altitude runs from 0 at the hangar to 1 in space)
ASCENT_DISTANCE = 150.0       # distance flown before the sky is fully dark
ASCENT_MAX_SHARE = 0.4        # but never more than this share of the trip
SKY_STOPS = [(0.0, (135, 203, 250)), (0.45, (95, 165, 235)), (0.7, (38, 75, 155))]  # then BACKGROUND_COLOR
STARS_APPEAR = 0.42           # altitude where stars start to show
CLOUD_COUNT = 22
CLOUD_KINDS = 4               # different cloud pictures
CLOUD_SEED = 5
CLOUD_PICTURE_SIZE = (400, 320)
CLOUD_AHEAD_HEIGHT = 0.46     # the big cloud the ship flies through: its altitude,
CLOUD_AHEAD_WIDTH = 0.28      # width (fills the screen as the mist arrives),
CLOUD_AHEAD_COVER = -0.06     # thickness (like CLOUD_COVER),
CLOUD_AHEAD_SIZE = (1000, 800)  # picture size,
CLOUD_AHEAD_SHIFT = 140       # most pixels steering can move it, so it can't be missed,
CLOUD_AHEAD_FADE = (0.39, 0.43)  # and the altitudes where it dissolves, hidden by the mist
CLOUD_DETAIL = 160            # size of the pattern clouds are made from (higher = finer, slower to start)
CLOUD_COVER = 0.39            # higher = smaller, wispier clouds
CLOUD_EDGE = 0.28             # how softly the edges thin out
CLOUD_LOW = 0.20              # altitudes of the lowest and highest clouds
CLOUD_HIGH = 0.50
CLOUD_SPREAD = 0.75           # how far from dead ahead clouds reach (smaller = more to fly through)
CLOUD_MIN_WIDTH = 0.09
CLOUD_MAX_WIDTH = 0.16
CLOUD_FADE_SIZE = 450         # pixels wide where a close cloud starts melting into mist
CLOUD_GONE_SIZE = 800
CLOUD_CACHE_SIZE = 30
CLOUD_COLOR = (248, 251, 255)
CLOUD_SHADE = (166, 182, 206)  # the thick, shadowed underside
MIST_START = 0.28             # altitudes where the mist begins, is thickest, and has cleared
MIST_MIDDLE = 0.40
MIST_END = 0.54
MIST_MAX = 0.9

# Launch: thruster glow
THRUST_LEAD = 2.0             # starts this long before liftoff
THRUST_PEAK = 1.5             # strongest this long after liftoff
THRUST_FADE = 8.0             # then fades away over this long
THRUST_INNER = 0.62           # the glow is an oval: where it begins, as a share of the way to the screen edge
THRUST_OUTER = 1.2            # where it is strongest (1 = middle of an edge, 1.41 = corners)
THRUST_MAX = 0.85
THRUST_COLORS = [(240, 45, 20), (255, 115, 20), (255, 205, 60)]  # inside to edge
