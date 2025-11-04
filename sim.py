import pygame
import random
import math
from logger import RunLogger
from config import (
    W, H, PANEL_W, TICK_PERIOD,
    CLIENT_SIZE, CLIENT_SPEED, CLIENT_SPAWN_X, CLIENT_SPAWN_Y_JITTER,
    PRICE_PER_CLIENT, INITIAL_CLIENTS, HUNGER_PROB, CIRCLE_RADIUS,
    IDLE_GAP, HUNGRY_COLOR, IDLE_COLOR, DWELL_MEAN_SEC_R, DWELL_SD_SEC_R,
    DWELL_MEAN_SEC_H, DWELL_SD_SEC_H, SIM_SPEED, CROWD_YELLOW_N, CROWD_RED_N,
    REST_GREEN, REST_YELLOW, REST_RED, DEMAND_WAVE_ON, DEMAND_PERIOD_SEC,
    DEMAND_PEAK, DEMAND_TROUGH, DEMAND_START_PHASE, MAX_SIM_SECONDS,
    QUALITY_MEAN, QUALITY_SD, QUALITY_MIN, QUALITY_MAX, LOGGING_ON, LOG_DIR,
    WAGE_PER_HOUR_H, WAGE_PER_HOUR_R, CROWD_DWELL_ALPHA, SEED, N_SERVERS_H, N_SERVERS_R, MODE,
    LEASE_PER_HOUR_R, MAINT_PER_HOUR_R
)

if SEED is not None:
    random.seed(SEED)

class Client:
    def __init__(self, x, y, cid):
        self.rect = pygame.Rect(0, 0, CLIENT_SIZE, CLIENT_SIZE)
        self.rect.center = (x, y)
        self.state = "idle"  # "idle" or "going"
        self.t_hungry = None  # simulation time when agent became hungry
        self.dwell_remaining = 0.0  # seconds; when > 0, client is "dwell"
        self.quality = None  # set at start of dwell; cleared after dwell ends
        self.return_target = None  # (x, y) point in the pool to walk back to
        self.cid = cid
        self.queue_start = None  # sim time when they reached the restaurant
        self.service_end = None  # sim time when their order completes

    def step_toward(self, dt, target_xy):
        # (leave your existing movement code as-is)
        tx, ty = target_xy
        cx, cy = self.rect.center
        dx, dy = tx - cx, ty - cy
        dist = math.hypot(dx, dy)
        if dist <= 1e-6:
            return
        ux, uy = dx / dist, dy / dist
        step = CLIENT_SPEED * dt
        if step >= dist:
            self.rect.center = (tx, ty)
        else:
            self.rect.center = (cx + ux * step, cy + uy * step)

    def color(self):
        # returning uses the idle color
        if self.state in ("idle", "returning"):
            return IDLE_COLOR
        # going or dwell = hungry/active color
        return HUNGRY_COLOR

class Sim:
    """Minimal simulation state: run/stop/reset + blinking square."""
    def __init__(self):
        self.square_size = 80
        self.mode = MODE  # remember the chosen kitchen
        self.fixed_cost = 0.0
        if self.mode == "human":
            self.n_servers = N_SERVERS_H
            self.dwell_mean = DWELL_MEAN_SEC_H
            self.dwell_sd = DWELL_SD_SEC_H
        else:
            self.n_servers = N_SERVERS_R
            self.dwell_mean = DWELL_MEAN_SEC_R
            self.dwell_sd = DWELL_SD_SEC_R
        self.reset()


    def center_square(self):
        # Base center of the simulation panel (to the right of the components panel)
        sim_w = W - PANEL_W
        cx = PANEL_W + sim_w // 2
        cy = H // 2

        # Apply horizontal scene shift (in pixels)
        from config import SCENE_SHIFT_X
        cx += int(sim_w * SCENE_SHIFT_X)

        # Keep the square fully inside the sim panel (clamp)
        half = self.square_size // 2
        min_x = PANEL_W + half
        max_x = PANEL_W + sim_w - half
        cx = max(min_x, min(max_x, cx))

        return pygame.Rect(0, 0, self.square_size, self.square_size).move(
            cx - half,
            cy - half
        )

    def _circle_center_left_of_restaurant(self):
        # Place idle circle to the left of the restaurant, inside the sim panel
        cx, cy = self.square_pos.center
        center_x = cx - (self.square_size // 2) - self.idle_radius - IDLE_GAP
        # keep inside the sim panel
        center_x = max(PANEL_W + self.idle_radius + 4, center_x)
        return (center_x, cy)

    def diners_in_restaurant(self) -> int:
        # include both waiting (queue) and being served (in_service)
        return len(self.queue) + len(self.in_service)

    def restaurant_color(self):
        load = self.diners_in_restaurant()  # now queue + service
        yellow, red = self._crowd_thresholds()
        if load >= red:
            return REST_RED
        if load >= yellow:
            return REST_YELLOW
        return REST_GREEN

    def _crowd_thresholds(self):
        n = max(1, len(self.clients))  # current population (agents recycle, so usually constant)
        yellow = max(1, int(CROWD_YELLOW_N))
        red = max(yellow + 1, int(CROWD_RED_N))  # ensure red > yellow
        return yellow, red

    def avg_time_spent_min(self):
        if self.time_spent_n == 0:
            return 0.0
        return self.time_spent_sum / self.time_spent_n

    def seed_clients(self, n):
        self.clients = []
        for _ in range(n):
            x, y = self._random_point_in_circle(self.idle_center, self.idle_radius)
            c = Client(x, y, self.cid_seq)
            self.cid_seq += 1
            c.state = "idle"
            self.clients.append(c)

    def reset(self):
        random.seed(SEED)
        self.running = False
        self.elapsed = 0.0
        self._tick_accum = 0.0
        self.visible = True
        self.ticks = 0
        self.square_pos = self.center_square()
        self.quality_sum = 0.0
        self.quality_n = 0
        self.cid_seq = 1

        # metrics
        self.customers_served = 0
        self.money_collected = 0.0

        # time-cost metrics (hungry -> served)
        self.time_spent_sum = 0.0  # minutes
        self.time_spent_n = 0

        # Idle circle geometry
        self.idle_radius = CIRCLE_RADIUS
        self.idle_center = self._circle_center_left_of_restaurant()

        # Seed fixed population
        self.seed_clients(INITIAL_CLIENTS)

        # Max run time
        self.stopped_reason = None

        self.quality_sum = 0.0
        self.quality_n = 0

        self.labor_cost = 0.0
        self.fixed_cost = 0.0

        self.queue = []  # FIFO of clients waiting to be served
        self.in_service = set()  # client IDs currently being served


        # create on first reset
        if not hasattr(self, "logger") or self.logger is None:
            self.logger = RunLogger(enabled=LOGGING_ON, log_dir=LOG_DIR)

        # (optional) summarize key params for provenance
        params = {
            "MODE": self.mode,
            "SIM_SPEED": SIM_SPEED,
            "TICK_PERIOD": TICK_PERIOD,
            "HUNGER_PROB": HUNGER_PROB,
            "DWELL_MEAN_SEC": self.dwell_mean,  # ← use instance values
            "DWELL_SD_SEC": self.dwell_sd,
            "QUALITY_MEAN": QUALITY_MEAN,
            "SEED": SEED,
            "N_SERVERS": self.n_servers,
            "LABOR_COST_POLICY": "per_server_fixed",
            "WAGE_PER_HOUR": (WAGE_PER_HOUR_R if self.mode == "robot" else WAGE_PER_HOUR_H),
            "LEASE_PER_HOUR": (LEASE_PER_HOUR_R if self.mode == "robot" else 0.0),
            "MAINT_PER_HOUR": (MAINT_PER_HOUR_R if self.mode == "robot" else 0.0),
        }
        self.logger.start_run(params)

    def spawn_client(self):
        cy = H // 2 + random.randint(-CLIENT_SPAWN_Y_JITTER, CLIENT_SPAWN_Y_JITTER)
        self.clients.append(Client(CLIENT_SPAWN_X, cy))

    def avg_quality(self):
        return (self.quality_sum / self.quality_n) if self.quality_n else 0.0

    def _random_point_in_circle(self, center, radius):
        # Uniform over disk
        u = random.random()
        r = radius * (u ** 0.5)
        theta = random.random() * 2 * math.pi
        x = center[0] + r * math.cos(theta)
        y = center[1] + r * math.sin(theta)
        return int(x), int(y)

    def start(self):
        self.running = True

    def stop(self):
        self.running = False
        self.visible = True # stay visible when stopped

    def step(self, dt):
        if not self.running:
            return
        sdt = dt * SIM_SPEED  # <— scaled simulation time
        self.elapsed += sdt  # (was dt)
        # ---- Fixed labor: pay per server (no utilization) ----
        if MODE == "human":
            self.labor_cost += (WAGE_PER_HOUR_H / 3600) * self.n_servers * sdt
        else:
            self.labor_cost += (WAGE_PER_HOUR_R / 3600) * self.n_servers * sdt
            self.fixed_cost += ((LEASE_PER_HOUR_R + MAINT_PER_HOUR_R) / 3600) * sdt

        # ---- time cutoff ----
        if self.elapsed >= MAX_SIM_SECONDS:
            self.running = False
            self.stopped_reason = f"Stopped at {int(MAX_SIM_SECONDS / 60)} min limit"
            if hasattr(self, "logger") and self.logger:
                self.logger.log_event(sim_time_s=self.elapsed, event_type="run_stop",
                                      severity="info", duration_s=0.0, note=self.stopped_reason)
            return

        self._tick_accum += sdt  # (was dt)

        # --- dispatcher: start service while capacity available ---
        yellow, red = self._crowd_thresholds()
        util = min(1.0, len(self.in_service) / float(self.n_servers))

        while len(self.in_service) < self.n_servers and self.queue:
            qc = self.queue.pop(0)
            if getattr(qc, 'state', None) != 'queue':
                continue

            base = max(2.0, random.gauss(self.dwell_mean, self.dwell_sd))
            dwell_s = base * (1.0 + CROWD_DWELL_ALPHA * util)
            qc.service_end = self.elapsed + dwell_s
            qc.dwell_remaining = dwell_s
            qc.last_dwell_sample = dwell_s  # <-- so we can log it later
            qc.state = 'dwell'
            self.in_service.add(qc.cid)

        if self._tick_accum >= TICK_PERIOD:
            # self.visible = not self.visible
            self._tick_accum = 0.0
            self.ticks += 1
            m = self.demand_multiplier()
            self.demand_current = m  # ← cache for logging & arrivals this tick
            p_eff = max(0.0, min(1.0, HUNGER_PROB * m))  # clamp for safety
            for c in self.clients:
                if c.state == "idle" and random.random() < p_eff:
                    c.state = "going"
                    c.t_hungry = self.elapsed

        # move clients
        self.update_clients(dt_move=dt, dt_time=sdt)

    def money_str(self):
        return f"${self.money_collected:,.2f}"

    def elapsed_mmss(self):
        m = int(self.elapsed // 60)
        s = int(self.elapsed % 60)
        return f"{m:02d}:{s:02d}"

    def update_clients(self, dt_move, dt_time):
        target = self.square_pos.center
        served_now = 0

        # 1) Move only "going" clients using UNscaled dt (visual speed constant)
        for c in self.clients:
            if c.state == "going":
                c.step_toward(dt_move, target)
                if self.square_pos.colliderect(c.rect):
                    # ARRIVAL → join queue; we’ll start service later if a server is free
                    c.state = "queue"
                    c.queue_start = self.elapsed
                    self.queue.append(c)

                    # sample per-visit food quality now (or you can defer to service start)
                    q = random.gauss(QUALITY_MEAN, QUALITY_SD)
                    c.quality = max(QUALITY_MIN, min(QUALITY_MAX, q))

        # 2) Process dwell using SCALED time so dwell finishes faster when SIM_SPEED>1
        for c in self.clients:
            if c.state == "dwell":
                c.dwell_remaining -= dt_time
                if c.dwell_remaining > 0.0:
                    continue  # still being served
                    # COMBINED WAIT TIME = arrival → food
                wait_time_s = max(0.0, self.elapsed - (c.queue_start or self.elapsed))

                self.customers_served += 1
                self.money_collected += PRICE_PER_CLIENT
                self.time_spent_sum += wait_time_s / 60.0
                self.time_spent_n += 1

                # Log ONLY wait time (rename schema in logger.py to wait_time_* when you’re ready)
                if self.logger:

                    self.logger.log_meal({
                        "sim_time_s": self.elapsed,
                        "sim_minutes": self.elapsed / 60.0,
                        "customer_id": c.cid,

                        # minutes only
                        "wait_time_min": wait_time_s / 60.0,

                        "price": PRICE_PER_CLIENT,
                        "quality": (c.quality if c.quality is not None else ""),
                        "mode": getattr(self, "mode", "human"),
                        "demand": getattr(self, "demand_current", self.demand_multiplier()),
                        # capacity + cumulative tallies
                        "n_servers": getattr(self, "n_servers", None),
                        "money_cum": self.money_collected,  # ← running total after this serve
                        "labor_cum": self.labor_cost,  # ← running total at this moment
                        "fixed_cum": self.fixed_cost,
                        "profit": self.money_collected - self.labor_cost - self.fixed_cost,
                    })

                # cleanup & recycle
                if c.cid in self.in_service:
                    self.in_service.remove(c.cid)
                if c.quality is not None:
                    self.quality_sum += c.quality
                    self.quality_n += 1
                    c.quality = None
                c.queue_start = None
                c.service_end = None
                c.dwell_remaining = 0.0
                c.state = "returning"
                c.return_target = self._random_point_in_circle(self.idle_center, self.idle_radius)

        # 3. after handling "going"
        for c in self.clients:
            if c.state == "returning":
                c.step_toward(dt_move, c.return_target)
                # arrived?
                if c.rect.center == c.return_target:
                    c.state = "idle"
                    c.return_target = None



    def demand_multiplier(self):
        """Piecewise cosine between DEMAND_TROUGH and DEMAND_PEAK over DEMAND_PERIOD_SEC."""
        if not DEMAND_WAVE_ON or DEMAND_PERIOD_SEC <= 0:
            return 1.0
        # cosine: 1 at phase 0; -1 at phase 0.5

        mid = 0.5 * (DEMAND_PEAK + DEMAND_TROUGH)
        amp = 0.5 * (DEMAND_PEAK - DEMAND_TROUGH)
        # start phase shifts us to off-peak at t=0
        t = (self.elapsed + DEMAND_START_PHASE * DEMAND_PERIOD_SEC) % DEMAND_PERIOD_SEC
        phase = t / DEMAND_PERIOD_SEC
        return mid + amp * math.cos(2 * math.pi * phase)


    def avg_quality(self):
        return (self.quality_sum / self.quality_n) if self.quality_n else 0.0