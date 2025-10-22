import pygame
from config import WHITE

class Button:
    def __init__(self, rect, label, bg, fg=WHITE):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.bg = bg
        self.fg = fg
        self.hover = False

    def draw(self, surf, font):
        color = tuple(min(255, c + 20) for c in self.bg) if self.hover else self.bg
        pygame.draw.rect(surf, color, self.rect, border_radius=10)
        pygame.draw.rect(surf, (0, 0, 0), self.rect, width=1, border_radius=10)
        text = font.render(self.label, True, self.fg)
        surf.blit(text, text.get_rect(center=self.rect.center))


    def handle(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False