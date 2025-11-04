# Window & layout
W, H = 900, 520
PANEL_W = 260 # left components panel width

# Timing
TICK_PERIOD = 0.5 # seconds per toggle when running
FPS = 60

# ---- Reproducibility ----
SEED = 12345   # set to an int for deterministic runs; set to None for random

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




# ABM population + behavior
INITIAL_CLIENTS = 75     # number of clients present at start
HUNGER_PROB = 0.001       # per-blink probability an idle client becomes hungry
CIRCLE_RADIUS = 140      # radius (px) of idle area to the left of the restaurant

# Shift the whole simulation scene horizontally (fraction of sim panel width)
# Negative = shift left, Positive = shift right. Ex: -0.25 = move left by 25%.
SCENE_SHIFT_X = 0.25

IDLE_GAP = 100  # extra horizontal space between the restaurant and the circle

# Service time after arrival (seconds)
# (How long food preparation/service takes once you're being served)
DWELL_MEAN_SEC = 240    # average time
DWELL_SD_SEC   = 120     # +/- variation (clamped >= 5s)

# Simulation speed (1.0 = real time). Increase to make the sim run faster than wall-clock.
SIM_SPEED = 60.0

# Fixed thresholds (people at the restaurant: queue + in_service)
CROWD_YELLOW_N = 8
CROWD_RED_N    = 16

# Restaurant fill colors by crowding
REST_GREEN  = (80, 200, 120)
REST_YELLOW = (230, 200, 80)
REST_RED    = (220, 90, 90)

# -------- Demand wave (simple, optional) --------
PRICE_PER_CLIENT = 12.00 # $ collected per served client
DEMAND_WAVE_ON = True        # toggle the wave on/off
DEMAND_PERIOD_SEC = 900.0    # one full cycle in simulated seconds (e.g., 10 min)
DEMAND_PEAK = 1.3            # multiplier at peak (e.g., org 1.6x baseline)
DEMAND_TROUGH = 0.01          # multiplier at trough (e.g., org 0.7x baseline)

MODE = "robot"           # "human" or "robot"

# == Human kitchen ==
N_SERVERS_H = 3 # number of orders that can be processed at once
DWELL_MEAN_SEC_H = 240
DWELL_SD_SEC_H   = 90
WAGE_PER_HOUR_H  = 18.0              # fully variable
MICRO_FAIL_RATE_H = 1/1800.0         # ~1 tiny hiccup per 30 min per server
MICRO_MTTR_SEC_H  = 10               # quick recoveries

# == Robotic kitchen ==
N_SERVERS_R = 2                       # 2 robotic "lanes"
DWELL_MEAN_SEC_R = 150                # faster & steadier
DWELL_SD_SEC_R   = 45
WAGE_PER_HOUR_R  = 10.0               # attendants/expediters
LEASE_PER_HOUR_R = 20.0               # fixed: lease/service plan
MAINT_PER_HOUR_R = 5.0                # fixed: cleaning/consumables
MTBF_SEC_R       = 3600.0             # mean time between failures (~1/hr)
MTTR_SEC_R       = 300.0              # mean time to repair (~5 min)
SHOCK_PROB_R     = 0.02               # rare “bad day” multiplier on MTTR
SHOCK_MTTR_MULT  = 3.0                # bad repair takes ~3× longer


# Start phase so we begin off-peak (0..1 across the cycle).
# For a cosine wave (max at phase 0), trough is at phase 0.5:
DEMAND_START_PHASE = 0.5

# -------- Run cutoff --------
# Stop the simulation after this much *simulated* time.
MAX_SIM_MINUTES = 60        # e.g., 120 for 2 hours of sim time
MAX_SIM_SECONDS = MAX_SIM_MINUTES * 60

# --- Food quality (per visit), 0..1 scale ---
QUALITY_MEAN = 0.70   # average quality
QUALITY_SD   = 0.12   # visit-to-visit variation
QUALITY_MIN  = 0.10   # hard floor
QUALITY_MAX  = 1.00   # hard ceiling

# ---- Logging ----
LOGGING_ON = True
LOG_DIR = "logs"

# --- Labor economics (human mode) ---
EMP_WAGE_PER_HOUR = 18.0

# Crowding → dwell stretch (max extra fraction at RED crowd)
CROWD_DWELL_ALPHA = 0.35   # e.g., up to +50% dwell at red-level load



