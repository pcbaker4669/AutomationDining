import pygame
import random
import math
from config import (
    W, H, PANEL_W, BLINK_PERIOD,
    CLIENT_SIZE, CLIENT_SPEED, CLIENT_SPAWN_X, CLIENT_SPAWN_Y_JITTER,
    PRICE_PER_CLIENT, INITIAL_CLIENTS, HUNGER_PROB, CIRCLE_RADIUS,
    IDLE_GAP, HUNGRY_COLOR, IDLE_COLOR, VALUE_OF_TIME_PER_MIN,
    DWELL_MEAN_SEC, DWELL_SD_SEC,
)

class Client:
    def __init__(self, x, y):
        self.rect = pygame.Rect(0, 0, CLIENT_SIZE, CLIENT_SIZE)
        self.rect.center = (x, y)
        self.state = "idle"  # "idle" or "going"
        self.t_hungry = None  # simulation time when agent became hungry
        self.dwell_remaining = 0.0  # seconds; when > 0, client is "dwell"

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
        # idle = bluish; going = white
        return IDLE_COLOR if self.state == "idle" else HUNGRY_COLOR

class Sim:
    """Minimal simulation state: run/stop/reset + blinking square."""
    def __init__(self):
        self.square_size = 80
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

    def avg_time_spent_min(self):
        if self.time_spent_n == 0:
            return 0.0
        return self.time_spent_sum / self.time_spent_n

    def avg_time_cost_dollars(self):
        return self.avg_time_spent_min() * VALUE_OF_TIME_PER_MIN

    def avg_gp_dollars(self):
        # generalized price = money price + time cost
        # (uses your global PRICE_PER_CLIENT)
        return PRICE_PER_CLIENT + self.avg_time_cost_dollars()

    def seed_clients(self, n):
        self.clients = []
        for _ in range(n):
            x, y = self._random_point_in_circle(self.idle_center, self.idle_radius)
            c = Client(x, y)
            c.state = "idle"
            self.clients.append(c)

    def reset(self):
        self.running = False
        self.elapsed = 0.0
        self._blink_accum = 0.0
        self.visible = True
        self.blinks = 0
        self.square_pos = self.center_square()

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

    def spawn_client(self):
        cy = H // 2 + random.randint(-CLIENT_SPAWN_Y_JITTER, CLIENT_SPAWN_Y_JITTER)
        self.clients.append(Client(CLIENT_SPAWN_X, cy))

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
        self.elapsed += dt

        self._blink_accum += dt

        if self._blink_accum >= BLINK_PERIOD:
            # self.visible = not self.visible
            self._blink_accum = 0.0
            self.blinks += 1
            for c in self.clients:
                if c.state == "idle" and random.random() < HUNGER_PROB:
                    c.state = "going"
                    c.t_hungry = self.elapsed  # seconds since start

        # move clients
        self.update_clients(dt)

    def money_str(self):
        return f"${self.money_collected:,.2f}"

    def elapsed_mmss(self):
        m = int(self.elapsed // 60)
        s = int(self.elapsed % 60)
        return f"{m:02d}:{s:02d}"

    def update_clients(self, dt):
        target = self.square_pos.center
        served_now = 0
        for c in self.clients:
            if c.state == "going":
                c.step_toward(dt, target)
                if self.square_pos.colliderect(c.rect):
                    served_now += 1
                    # start dwell instead of teleporting immediately
                    # sample a positive dwell time ~ Normal(mean, sd), clamped to at least 5s
                    dwell = max(2.0, random.gauss(DWELL_MEAN_SEC, DWELL_SD_SEC))
                    c.dwell_remaining = dwell
                    c.state = "dwell"
                    # NOTE: do NOT compute time cost yet; we now include dwell,
                    # so we'll finalize the metric when dwell finishes.

        # handle dwellers: count time from hungry->end-of-dwell, then return to idle circle
        for c in self.clients:
            if c.state == "dwell":
                c.dwell_remaining -= dt
                if c.dwell_remaining <= 0.0:
                    # now we finalize time cost INCLUDING dwell
                    if c.t_hungry is not None:
                        delta_min = max(0.0, (self.elapsed - c.t_hungry) / 60.0)
                        self.time_spent_sum += delta_min
                        self.time_spent_n += 1
                        c.t_hungry = None
                    # send back to idle pool
                    c.rect.center = self._random_point_in_circle(self.idle_center, self.idle_radius)
                    c.state = "idle"
                    c.dwell_remaining = 0.0

        if served_now:
            self.customers_served += served_now
            self.money_collected += PRICE_PER_CLIENT * served_now