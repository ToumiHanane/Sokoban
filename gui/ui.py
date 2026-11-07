"""
ui.py  --  briques visuelles : couleurs, sprites pixel-art, particules, boutons, panneaux
Thème : pixel rose / princesse.
"""
import math
import os
import random

import pygame

# ----------------------------------------------------------------------
# Couleurs
# ----------------------------------------------------------------------
BG_TOP = (255, 226, 240)
BG_BOTTOM = (236, 224, 252)
PURPLE = (124, 114, 145)
DARK_PURPLE = (92, 76, 120)
HOT_PINK = (240, 120, 170)
PINK = (255, 192, 220)
PINK_HOVER = (255, 214, 232)
LAVENDER = (205, 188, 238)
WHITE = (255, 255, 255)
GREY = (200, 195, 208)
GOLD = (255, 214, 102)
MINT = (170, 228, 200)
PANEL_FILL = (255, 250, 253)

# ----------------------------------------------------------------------
# Sprites pixel-art (chaque lettre = un pixel, '.' = transparent)
# ----------------------------------------------------------------------
SPRITES = {
    "heart": (["..RR..RR..",
               ".RHRRRRRR.",
               ".RRRRRRRR.",
               "..RRRRRR..",
               "...RRRR...",
               "....RR...."],
              {"R": (255, 120, 175), "H": (255, 228, 240)}),
    "star": (["....Y....",
              "...YYY...",
              "YYYYHYYYY",
              ".YYYHYYY.",
              "..YYYYY..",
              ".YYY.YYY.",
              ".YY...YY."],
             {"Y": (255, 214, 102), "H": (255, 245, 205)}),
    "sparkle": (["..W..",
                 "..W..",
                 "WWWWW",
                 "..W..",
                 "..W.."],
                {"W": (255, 255, 255)}),
    "crown": (["Y...Y...Y",
               "YY.YYY.YY",
               "YYYYYYYYY",
               "YPYYBYYPY",
               "YYYYYYYYY",
               "DDDDDDDDD"],
              {"Y": (255, 214, 102), "P": (255, 120, 175),
               "B": (160, 140, 230), "D": (214, 168, 70)}),
    "flower": (["..P..",
                ".PPP.",
                "PPYPP",
                ".PPP.",
                "..P.."],
               {"P": (255, 170, 205), "Y": (255, 230, 130)}),
}


class SpriteBank:
    """Fabrique et met en cache les sprites à la taille voulue."""

    def __init__(self):
        self.cache = {}

    def get(self, kind, px, tint=None, alpha=255):
        alpha = 255 if alpha >= 240 else max(0, int(alpha) // 16 * 16)
        key = (kind, px, tint, alpha)
        if key not in self.cache:
            rows, palette = SPRITES[kind]
            palette = dict(palette)
            if tint:                                   # remplace la 1re couleur de la palette
                palette[next(iter(palette))] = tint
            w, h = len(rows[0]), len(rows)
            surf = pygame.Surface((w * px, h * px), pygame.SRCALPHA)
            for y, row in enumerate(rows):
                for x, ch in enumerate(row):
                    color = palette.get(ch)
                    if color:
                        pygame.draw.rect(surf, color, (x * px, y * px, px, px))
            if alpha < 255:
                surf.set_alpha(alpha)
            self.cache[key] = surf
        return self.cache[key]


# ----------------------------------------------------------------------
# Particules
# ----------------------------------------------------------------------
CONFETTI_COLORS = [(255, 150, 200), (255, 214, 102), (170, 228, 200),
                   (205, 188, 238), (255, 255, 255), (255, 120, 175)]


class Particle:
    def __init__(self, x, y, vx, vy, life, kind, px, gravity=0.0, color=None):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life, self.age = life, 0.0
        self.kind, self.px, self.gravity, self.color = kind, px, gravity, color

    @property
    def alive(self):
        return self.age < self.life

    def update(self, dt):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt


class Particles:
    def __init__(self, sprites):
        self.sprites = sprites
        self.items = []

    def burst(self, x, y, n=16):
        """Petit feu d'artifice (une caisse arrive sur une cible)."""
        for _ in range(n):
            ang = random.uniform(0, math.tau)
            speed = random.uniform(80, 240)
            kind = random.choice(["sparkle", "star", "heart"])
            self.items.append(Particle(x, y, math.cos(ang) * speed, math.sin(ang) * speed - 60,
                                       random.uniform(0.6, 1.1), kind, random.choice([2, 3, 4]),
                                       gravity=260))

    def confetti(self, width, n=90):
        for _ in range(n):
            self.items.append(Particle(random.uniform(0, width), random.uniform(-200, -10),
                                       random.uniform(-30, 30), random.uniform(80, 220),
                                       random.uniform(3.0, 5.0), "rect", random.choice([6, 8, 10]),
                                       gravity=20, color=random.choice(CONFETTI_COLORS)))

    def update(self, dt):
        for p in self.items:
            p.update(dt)
        self.items = [p for p in self.items if p.alive]

    def draw(self, surface):
        for p in self.items:
            fade = 1.0 if p.age < p.life * 0.6 else max(0.0, (p.life - p.age) / (p.life * 0.4))
            if p.kind == "rect":
                pygame.draw.rect(surface, p.color, (int(p.x), int(p.y), p.px, p.px))
            else:
                img = self.sprites.get(p.kind, p.px, alpha=255 * fade)
                surface.blit(img, (int(p.x), int(p.y)))


class Ambient:
    """Petits coeurs / étoiles / étincelles qui flottent doucement en arrière-plan."""

    def __init__(self, sprites, width, height, n=26):
        self.sprites, self.w, self.h = sprites, width, height
        self.items = [self._new(random.uniform(0, height)) for _ in range(n)]

    def _new(self, y):
        return {"x": random.uniform(0, self.w), "y": y, "speed": random.uniform(14, 40),
                "phase": random.uniform(0, math.tau),
                "kind": random.choice(["heart", "star", "sparkle", "sparkle", "flower"]),
                "px": random.choice([2, 3, 3, 4])}

    def update(self, dt):
        for it in self.items:
            it["y"] -= it["speed"] * dt
            if it["y"] < -40:
                it.update(self._new(self.h + 20))

    def draw(self, surface, t):
        for it in self.items:
            x = it["x"] + math.sin(t / 900 + it["phase"]) * 14
            twinkle = 0.55 + 0.35 * math.sin(t / 400 + it["phase"] * 2)
            img = self.sprites.get(it["kind"], it["px"], alpha=255 * twinkle)
            surface.blit(img, (int(x), int(it["y"])))


# ----------------------------------------------------------------------
# Fond
# ----------------------------------------------------------------------
def make_background(width, height):
    """Dégradé rose -> lavande avec un motif de petits carrés façon pixel."""
    bg = pygame.Surface((width, height))
    for y in range(height):
        k = y / (height - 1)
        color = tuple(int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * k) for i in range(3))
        pygame.draw.line(bg, color, (0, y), (width, y))
    for row, y in enumerate(range(10, height, 40)):
        for x in range(10 + (row % 2) * 20, width, 40):
            pygame.draw.rect(bg, (255, 244, 250), (x, y, 6, 6))
    return bg


# ----------------------------------------------------------------------
# Police
# ----------------------------------------------------------------------
def load_font(asset_dir, size):
    path = os.path.join(asset_dir, "PressStart2P-Regular.ttf")
    if os.path.exists(path):
        return pygame.font.Font(path, size)
    return pygame.font.Font(None, int(size * 1.7))      # secours si la police manque


# ----------------------------------------------------------------------
# Texte
# ----------------------------------------------------------------------
def draw_text(surface, text, font, color, pos, anchor="center", shadow=None, offset=3):
    img = font.render(text, True, color)
    rect = img.get_rect()
    setattr(rect, anchor, pos)
    if shadow:
        sh = font.render(text, True, shadow)
        surface.blit(sh, rect.move(offset, offset))
    surface.blit(img, rect)
    return rect


def draw_text_wave(surface, text, font, color, center, t, amp=8, shadow=None, offset=5, speed=260):
    """Texte dont chaque lettre rebondit (titres animés)."""
    widths = [font.size(ch)[0] for ch in text]
    x = center[0] - sum(widths) // 2
    for i, ch in enumerate(text):
        y = center[1] + math.sin(t / speed + i * 0.6) * amp
        if ch != " ":
            draw_text(surface, ch, font, color, (x, y), anchor="midleft", shadow=shadow, offset=offset)
        x += widths[i]


# ----------------------------------------------------------------------
# Panneaux, boutons, barres
# ----------------------------------------------------------------------
def draw_panel(surface, rect, fill=PANEL_FILL, border=PURPLE, radius=18, shadow=True):
    if shadow:
        pygame.draw.rect(surface, LAVENDER, rect.move(6, 7), border_radius=radius)
    pygame.draw.rect(surface, border, rect, border_radius=radius)
    pygame.draw.rect(surface, fill, rect.inflate(-8, -8), border_radius=max(2, radius - 4))


def draw_button(surface, rect, text, font, hover=False, enabled=True, active=False):
    """Bouton pastel : ombre en relief, se soulève au survol, doré si 'active'."""
    lift = 3 if (hover and enabled) else 0
    r = rect.move(0, -lift)
    if enabled:
        border = PURPLE
        fill = (255, 226, 150) if active else (PINK_HOVER if hover else PINK)
        text_color, shadow = WHITE, PURPLE
    else:
        border, fill, text_color, shadow = GREY, (232, 228, 236), WHITE, GREY
    pygame.draw.rect(surface, border, rect.move(0, 5), border_radius=20)        # ombre
    pygame.draw.rect(surface, border, r, border_radius=20)
    inner = r.inflate(-8, -8)
    pygame.draw.rect(surface, fill, inner, border_radius=16)
    if enabled:
        top = pygame.Rect(inner.x + 8, inner.y + 3, inner.w - 16, max(4, inner.h // 7))
        pygame.draw.rect(surface, WHITE if active else LAVENDER, top, border_radius=4)
    draw_text(surface, text, font, text_color, r.center, shadow=shadow, offset=2)


def draw_progress(surface, rect, frac):
    frac = max(0.0, min(1.0, frac))
    pygame.draw.rect(surface, PURPLE, rect, border_radius=rect.h // 2)
    inner = rect.inflate(-6, -6)
    pygame.draw.rect(surface, (255, 240, 248), inner, border_radius=inner.h // 2)
    if frac > 0:
        fill = pygame.Rect(inner.x, inner.y, max(inner.h, int(inner.w * frac)), inner.h)
        pygame.draw.rect(surface, HOT_PINK, fill, border_radius=inner.h // 2)
        for x in range(fill.x + 6, fill.right - 4, 14):                      # rayures pixel
            pygame.draw.rect(surface, PINK, (x, fill.y + 3, 6, max(2, fill.h // 3)))
