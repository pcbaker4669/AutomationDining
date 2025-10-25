import sys
import pygame
from config import (
    W, H, PANEL_W, FPS,
    BG, PANEL_BG, SIM_BG,
    WHITE, GREY, GREEN, RED, YELLOW, SIM_SPEED
)
from widgets import Button
from sim import Sim

class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("ABM UI Shell — Start Small")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 18)
        self.font_small = pygame.font.SysFont("consolas", 14)
        self.sim = Sim()

        # Buttons in the left panel
        x = 24
        y0 = 90
        w = PANEL_W - 48
        h = 50
        gap = 16
        self.btn_run = Button((x, y0, w, h), "Run", GREEN)
        self.btn_stop = Button((x, y0 + (h + gap), w, h), "Stop", RED)
        self.btn_reset = Button((x, y0 + 2 * (h + gap), w, h), "Reset", YELLOW)
        self.buttons = [self.btn_run, self.btn_stop, self.btn_reset]

    def draw_panel(self):
        pygame.draw.rect(self.screen, PANEL_BG, (0, 0, PANEL_W, H))
        title = self.font.render("Components", True, WHITE)
        self.screen.blit(title, (24, 24))
        subtitle = self.font_small.render("(Start small — add later)", True, GREY)
        self.screen.blit(subtitle, (24, 48))
        for b in self.buttons:
            b.draw(self.screen, self.font)

    def draw_sim(self):
        pygame.draw.rect(self.screen, SIM_BG, (PANEL_W, 0, W - PANEL_W, H))
        hdr = self.font.render("Simulation", True, WHITE)
        self.screen.blit(hdr, (PANEL_W + 20, 20))
        status = "RUNNING" if self.sim.running else "STOPPED"
        status_color = GREEN if self.sim.running else GREY
        st = self.font_small.render(f"Status: {status}", True, status_color)
        self.screen.blit(st, (PANEL_W + 20, 48))

        # ---- Status ticker ----
        elapsed = self.sim.elapsed_mmss()
        ticks = self.sim.blinks
        t1 = self.font_small.render(f"Elapsed: {elapsed}", True, WHITE)
        t2 = self.font_small.render(f"Ticks: {ticks}", True, WHITE)
        self.screen.blit(t1, (PANEL_W+160, 48))
        self.screen.blit(t2, (PANEL_W+300, 48))

        # metrics line directly below status line (served and money)
        served = self.sim.customers_served
        money = self.sim.money_str()
        t3 = self.font_small.render(f"Served: {served}", True, WHITE)
        t4 = self.font_small.render(f"Money: {money}", True, WHITE)
        self.screen.blit(t3, (PANEL_W + 20, 68))
        self.screen.blit(t4, (PANEL_W + 160, 68))

        active = len(self.sim.clients)
        t_active = self.font_small.render(f"Active: {active}", True, WHITE)
        self.screen.blit(t_active, (PANEL_W + 300, 68))

        # Time cost HUD (opportunity cost)
        avg_min = self.sim.avg_time_spent_min()
        avg_tc = self.sim.avg_time_cost_dollars()
        avg_gp = self.sim.avg_gp_dollars()

        # ATS - Average Time Spent, ATC - Average Time Cost, AGP - Average Global Price (Price+Time)
        t_time = self.font_small.render(f"ATS: {avg_min:.2f} min", True, WHITE)
        t_cost = self.font_small.render(f"ATC: ${avg_tc:.2f}", True, WHITE)
        t_gp = self.font_small.render(f"AGP: ${avg_gp:.2f}", True, WHITE)

        # place these a bit lower than your existing metrics; adjust Y offsets if needed
        self.screen.blit(t_time, (PANEL_W + 20, 88))
        self.screen.blit(t_cost, (PANEL_W + 160, 88))
        self.screen.blit(t_gp, (PANEL_W + 300, 88))

        speed_lbl = self.font_small.render("Speed: x{:.1f}".format(SIM_SPEED), True, WHITE)
        self.screen.blit(speed_lbl, (PANEL_W + 420, 48))

        # Draw a faint idle circle
        # pygame.draw.circle(self.screen, GREY, self.sim.idle_center, self.sim.idle_radius, width=1)

        # draw clients (little squares) marching toward the restaurant
        for c in self.sim.clients:
            pygame.draw.rect(self.screen, c.color(), c.rect, border_radius=2)

        if self.sim.visible:
            pygame.draw.rect(self.screen, WHITE, self.sim.square_pos, border_radius=8)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

            # Buttons
            if self.btn_run.handle(event):
                self.sim.start()
            if self.btn_stop.handle(event):
                self.sim.stop()
            if self.btn_reset.handle(event):
                self.sim.reset()

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.sim.step(dt)

            self.screen.fill(BG)
            self.draw_panel()
            self.draw_sim()
            pygame.display.flip()