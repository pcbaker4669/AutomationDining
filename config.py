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

# Clients (little squares that march to the restaurant)
CLIENT_SIZE = 12          # pixels
CLIENT_SPEED = 120.0      # pixels/second
CLIENT_SPAWN_X = PANEL_W + 20     # just inside the simulation panel, left edge
CLIENT_SPAWN_Y_JITTER = 40        # +/- vertical jitter around midline

# Economics
PRICE_PER_CLIENT = 5.00 # $ collected per served client