import pygame
import random
import math
from config import (W, H, PANEL_W, BLINK_PERIOD, CLIENT_SIZE, CLIENT_SPEED, CLIENT_SPAWN_X,
                    CLIENT_SPAWN_Y_JITTER, PRICE_PER_CLIENT, INITIAL_CLIENTS)

class Client:
    def __init__(self, x, y):
        self.rect = pygame.Rect(0, 0, CLIENT_SIZE, CLIENT_SIZE)
        self.rect.center = (x, y)

    def step_toward(self, dt, target_xy):
        """Move toward target at CLIENT_SPEED; dt is seconds."""
        tx, ty = target_xy
        cx, cy = self.rect.center
        dx, dy = tx - cx, ty - cy
        dist = math.hypot(dx, dy)
        if dist <= 1e-6:
            return
        ux, uy = dx / dist, dy / dist
        step = CLIENT_SPEED * dt
        if step >= dist:
            # Snap to target
            self.rect.center = (tx, ty)
        else:
            self.rect.center = (cx + ux * step, cy + uy * step)

class Sim:
    """Minimal simulation state: run/stop/reset + blinking square."""
    def __init__(self):
        self.square_size = 80
        self.reset()

    def center_square(self):
        cx = PANEL_W + (W - PANEL_W) // 2
        cy = H // 2
        return pygame.Rect(0, 0, self.square_size, self.square_size).move(
            cx - self.square_size // 2, cy - self.square_size // 2
        )

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

        # clear client list
        self.clients = []

        # seed a fixed population
        self.seed_clients(INITIAL_CLIENTS)

    def spawn_client(self):
        cy = H // 2 + random.randint(-CLIENT_SPAWN_Y_JITTER, CLIENT_SPAWN_Y_JITTER)
        self.clients.append(Client(CLIENT_SPAWN_X, cy))

    def seed_clients(self, n):
        """Create n clients along the left edge (small stagger to reduce overlap)."""
        self.clients = []
        midy = H // 2
        for i in range(n):
            y = midy + random.randint(-CLIENT_SPAWN_Y_JITTER, CLIENT_SPAWN_Y_JITTER)
            x = CLIENT_SPAWN_X - (i % 5)  # tiny x-stagger so they’re not identical
            self.clients.append(Client(x, y))

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

        # move clients each frame (running only)
        self.update_clients(dt)

    def money_str(self):
        return f"${self.money_collected:,.2f}"

    def elapsed_mmss(self):
        m = int(self.elapsed // 60)
        s = int(self.elapsed % 60)
        return f"{m:02d}:{s:02d}"

    def update_clients(self, dt):
        """Advance clients toward the restaurant center and remove upon arrival."""
        target = self.square_pos.center
        arrived = []
        for c in self.clients:
            c.step_toward(dt, target)
            # Consider 'arrived' if client enters the big square
            if self.square_pos.colliderect(c.rect):
                arrived.append(c)
        # remove arrived clients
        if arrived:
            self.customers_served += len(arrived)
            self.money_collected += PRICE_PER_CLIENT * len(arrived)
            self.clients = [c for c in self.clients if c not in arrived]
