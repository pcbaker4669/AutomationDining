# Window & layout
W, H = 900, 520
PANEL_W = 260 # left components panel width

# Timing
BLINK_PERIOD = 0.5 # seconds per toggle when running
FPS = 60

# Colors (RGB)
BG = (22, 26, 30)
PANEL_BG = (28, 34, 40)
SIM_BG = (18, 20, 24)
WHITE = (235, 235, 235)
GREY = (140, 150, 160)
GREEN = (90, 200, 120)
RED = (220, 90, 90)
YELLOW = (230, 200, 80)

HUNGRY_COLOR = (255, 170, 0)   # amber for hungry/going
IDLE_COLOR   = (100, 160, 240) # blue for idle


# Clients (little squares that march to the restaurant)
CLIENT_SIZE = 12          # pixels
CLIENT_SPEED = 120.0      # pixels/second
CLIENT_SPAWN_X = PANEL_W + 20     # just inside the simulation panel, left edge
CLIENT_SPAWN_Y_JITTER = 40        # +/- vertical jitter around midline

# Economics
PRICE_PER_CLIENT = 5.00 # $ collected per served client


# ABM population + behavior
INITIAL_CLIENTS = 50     # number of clients present at start
HUNGER_PROB = 0.1       # per-blink probability an idle client becomes hungry
CIRCLE_RADIUS = 140      # radius (px) of idle area to the left of the restaurant

# Shift the whole simulation scene horizontally (fraction of sim panel width)
# Negative = shift left, Positive = shift right. Ex: -0.25 = move left by 25%.
SCENE_SHIFT_X = 0.25

IDLE_GAP = 100  # extra horizontal space between the restaurant and the circle

# Opportunity cost (dollars per minute) for the consumers
VALUE_OF_TIME_PER_MIN = 0.25  # = $15/hour

# Eating (dwell) time after arrival (seconds)
DWELL_MEAN_SEC = 5    # average time
DWELL_SD_SEC   = 2     # +/- variation (clamped >= 5s)
