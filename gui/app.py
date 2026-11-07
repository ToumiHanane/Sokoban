"""
app.py  --  interface Pygame du Sokoban (thème pixel rose / princesse)

Écrans : MENU -> LEVELS -> GAME -> DONE   (+ COMPARE accessible depuis GAME et DONE)

  * Les algorithmes tournent dans un thread (l'interface ne gèle jamais).
  * Bouton COMPARE : lance TOUS les algorithmes en arrière-plan et affiche
    la comparaison (coût + noeuds développés), sans avoir à les faire un par un.
  * Jeu à la main : flèches / WASD, U = annuler, R = recommencer, ESPACE = pause.
"""
import math
import os
import threading

import pygame

from sokoban.puzzle import SokobanPuzzle, BOX, BOX_ON_TARGET, TARGET, WALL
from sokoban.levels import LEVELS, LEVEL_NAMES
from sokoban.solvers import default_solvers
from . import ui
from .ui import (draw_text, draw_text_wave, draw_button, draw_panel, draw_progress,
                 HOT_PINK, PURPLE, DARK_PURPLE, PINK, WHITE, GOLD, LAVENDER, MINT)

# ======================================================================
# Réglages
# ======================================================================
WIDTH, HEIGHT = 1100, 740
FPS = 60
ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
BASE_STEP_MS = 350
SPEEDS = [0.5, 1, 2, 4]

DIRS8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
KEY_TO_ACTION = {pygame.K_UP: "UP", pygame.K_DOWN: "DOWN", pygame.K_LEFT: "LEFT",
                 pygame.K_RIGHT: "RIGHT", pygame.K_w: "UP", pygame.K_s: "DOWN",
                 pygame.K_a: "LEFT", pygame.K_d: "RIGHT"}


# ======================================================================
# Fonctions utilitaires sur la grille (la logique du jeu est dans sokoban/)
# ======================================================================
def find_inside_cells(grid, player):
    """Cases accessibles depuis le joueur sans traverser de mur."""
    seen, stack = {player}, [player]
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if (0 <= nr < len(grid) and 0 <= nc < len(grid[0])
                    and (nr, nc) not in seen and grid[nr][nc] != WALL):
                seen.add((nr, nc))
                stack.append((nr, nc))
    return seen


def visible_walls(grid, inside):
    """Murs voisins (8 directions) d'une case intérieure : on ne dessine pas le vide autour."""
    walls = set()
    for r, c in inside:
        for dr, dc in DIRS8:
            nr, nc = r + dr, c + dc
            if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and grid[nr][nc] == WALL:
                walls.add((nr, nc))
    return walls


def count_cells(grid, chars):
    return sum(row.count(ch) for row in grid for ch in chars)


def fit_tile(rows, cols, max_w, max_h, cap):
    return max(4, min(max_w // cols, max_h // rows, cap))


# ======================================================================
# Assets
# ======================================================================
class Assets:
    def __init__(self):
        self.raw = {}
        for name in ("cursor", "button_menu", "player", "box", "wall", "floor", "drip"):
            path = os.path.join(ASSET_DIR, name + ".png")
            self.raw[name] = pygame.image.load(path).convert_alpha()
        self.cache = {}

    def exact(self, name, size):
        key = (name, size, "exact")
        if key not in self.cache:
            self.cache[key] = pygame.transform.scale(self.raw[name], size)
        return self.cache[key]

    def fit(self, name, max_w, max_h=None):
        max_h = max_h or max_w
        key = (name, max_w, max_h, "fit")
        if key not in self.cache:
            w, h = self.raw[name].get_size()
            ratio = min(max_w / w, max_h / h)
            self.cache[key] = pygame.transform.scale(
                self.raw[name], (max(1, int(w * ratio)), max(1, int(h * ratio))))
        return self.cache[key]

    def checker(self, tile):
        """Voile blanc translucide pour faire un damier léger sur le sol."""
        key = ("checker", tile)
        if key not in self.cache:
            s = pygame.Surface((tile, tile), pygame.SRCALPHA)
            s.fill((255, 255, 255, 38))
            self.cache[key] = s
        return self.cache[key]


# ======================================================================
# Dessin du plateau
# ======================================================================
def draw_board(surface, grid, inside, walls, assets, sprites, tile, origin, t=None, hop=0):
    """t = temps en ms pour les animations (None = aperçu fixe, ex. cartes de niveaux)."""
    ox, oy = origin
    wall = assets.exact("wall", (tile, tile))
    floor = assets.exact("floor", (tile, tile))
    box = assets.fit("box", int(tile * 0.85))
    player = assets.fit("player", int(tile * 0.95))
    anim = t is not None
    pulse = 1 + 0.08 * math.sin(t / 250) if anim else 1

    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            x, y = ox + c * tile, oy + r * tile
            if cell == WALL:
                if (r, c) in walls:
                    surface.blit(wall, (x, y))
                continue
            if (r, c) not in inside:
                continue
            surface.blit(floor, (x, y))
            if (r + c) % 2:
                surface.blit(assets.checker(tile), (x, y))
            center = (x + tile // 2, y + tile // 2)

            if cell in ("S", ".", "*"):                  # marque de cible
                if cell == "*":
                    pygame.draw.circle(surface, GOLD, center, int(tile * 0.46 * pulse))
                else:
                    pygame.draw.circle(surface, (186, 146, 226), center,
                                       int(tile * 0.28 * pulse), max(2, tile // 14))
                    pygame.draw.circle(surface, (255, 170, 205), center, max(2, tile // 10))
            if cell in ("B", "*"):
                surface.blit(box, box.get_rect(center=center))
                if cell == "*" and anim and tile >= 24 and int(t / 450 + r * 3 + c) % 3 == 0:
                    sp = sprites.get("sparkle", max(2, tile // 14))
                    surface.blit(sp, (x + tile - sp.get_width() - 2, y + 2))
            if cell in ("R", "."):
                bob = int(math.sin(t / 300) * max(1, tile // 40)) if anim else 0
                surface.blit(player, player.get_rect(
                    midbottom=(center[0], y + tile - 1 - hop + bob)))


# ======================================================================
# Application
# ======================================================================
class App:
    def __init__(self, solvers=None):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Sokoban Game")
        self.clock = pygame.time.Clock()
        pygame.mouse.set_visible(False)

        self.assets = Assets()
        self.sprites = ui.SpriteBank()
        self.particles = ui.Particles(self.sprites)
        self.ambient = ui.Ambient(self.sprites, WIDTH, HEIGHT)
        self.bg = ui.make_background(WIDTH, HEIGHT)
        self.fonts = {"huge": ui.load_font(ASSET_DIR, 40), "title": ui.load_font(ASSET_DIR, 30),
                      "big": ui.load_font(ASSET_DIR, 24), "normal": ui.load_font(ASSET_DIR, 16),
                      "small": ui.load_font(ASSET_DIR, 10)}
        self.cursor_img = self.assets.fit("cursor", 40, 40)
        self.cursor_hotspot = self.find_cursor_hotspot()

        # --- solveurs
        self.solvers = solvers or default_solvers()
        self.names = list(self.solvers)
        self.results = {}          # (niveau, nom) -> résultat
        self.jobs = {}             # (niveau, nom) -> {"done": bool, "result": dict}
        self.result_time = {}      # (niveau, nom) -> ms (pour animer les barres)
        self.pending = None        # (niveau, nom) à rejouer dès que le calcul est fini

        # --- niveaux
        self.starts = [SokobanPuzzle(lines) for lines in LEVELS]
        self.inside = [find_inside_cells(s.grid, s.player) for s in self.starts]
        self.walls = [visible_walls(s.grid, ins) for s, ins in zip(self.starts, self.inside)]

        # --- état de l'application
        self.scene = "menu"
        self.selected = None
        self.running = True
        self.t = 0
        self.dt = 0.0
        self.level = 0
        self.puzzle = None
        self.history = []
        self.moves = 0
        self.queue, self.qpos = [], 0
        self.autoplay, self.paused = False, False
        self.speed_i = 1
        self.last_step = 0
        self.last_move = -9999
        self.current = None        # résultat rejoué
        self.solver_name = None
        self.win_time = None
        self.toast_text, self.toast_until = "", 0
        self.bar_scene_entered = 0

        self.build_layout()

    # ------------------------------------------------------------------
    def build_layout(self):
        R = pygame.Rect
        self.MENU = R(20, 14, 150, 64)
        self.START = R(WIDTH // 2 - 150, 430, 300, 90)
        # niveaux : grille 4 x 2
        cw, ch, gap = 232, 200, 20
        x0 = (WIDTH - (4 * cw + 3 * gap)) // 2
        self.CARDS = [R(x0 + (i % 4) * (cw + gap), 120 + (i // 4) * (ch + gap), cw, ch)
                      for i in range(len(LEVELS))]
        self.SELECT = R(WIDTH // 2 - 150, 600, 300, 72)
        # jeu
        self.BOARD_PANEL = R(40, 96, 690, 452)
        self.HUD = R(750, 96, 310, 452)
        n, g = len(self.names), 14
        w = (1020 - g * (n - 1)) // n
        self.ALGOS = [R(40 + i * (w + g), 572, w, 64) for i in range(n)]
        self.ACTIONS = {name: R(40 + i * 260, 656, 240, 64)
                        for i, name in enumerate(["RESET", "UNDO", "COMPARE", "PAUSE"])}
        self.SPEED_MINUS = R(self.HUD.x + 24, self.HUD.bottom - 74, 60, 46)
        self.SPEED_PLUS = R(self.HUD.right - 84, self.HUD.bottom - 74, 60, 46)
        # fin de niveau
        self.DONE = {name: R(100 + i * 230, 610, 210, 70)
                     for i, name in enumerate(["LEVELS", "AGAIN", "COMPARE", "NEXT"])}
        # comparaison
        self.CMP_PANEL = R(60, 110, 980, 480)
        self.CMP_BACK = R(WIDTH // 2 - 330, 630, 300, 70)
        self.CMP_LEVELS = R(WIDTH // 2 + 30, 630, 300, 70)

    def find_cursor_hotspot(self):
        w, h = self.cursor_img.get_size()
        for y in range(h):
            for x in range(w):
                r, g, b, a = self.cursor_img.get_at((x, y))
                if a > 200 and r + g + b < 200:
                    return x, y
        return 0, 0

    def go(self, scene):
        self.scene = scene
        self.bar_scene_entered = self.t

    def toast(self, text, ms=2600):
        self.toast_text, self.toast_until = text, self.t + ms

    # ------------------------------------------------------------------
    # Niveau / actions du joueur
    # ------------------------------------------------------------------
    def start_level(self, index):
        self.level = index
        self.reset_level()
        self.go("game")

    def reset_level(self):
        self.puzzle = self.starts[self.level]
        self.history, self.moves = [], 0
        self.queue, self.qpos = [], 0
        self.autoplay, self.paused = False, False
        self.current, self.win_time = None, None
        self.pending = None

    def board_geometry(self):
        grid = self.puzzle.grid
        area = self.BOARD_PANEL.inflate(-40, -40)
        tile = fit_tile(len(grid), len(grid[0]), area.w, area.h, 80)
        ox = area.centerx - len(grid[0]) * tile // 2
        oy = area.centery - len(grid) * tile // 2
        return tile, ox, oy

    def play_action(self, action):
        successors = dict(self.puzzle.successorFunction())
        if action not in successors:
            return False
        new = successors[action]
        gained = [(r, c) for r, row in enumerate(new.grid) for c, ch in enumerate(row)
                  if ch == BOX_ON_TARGET and self.puzzle.grid[r][c] != BOX_ON_TARGET]
        self.history.append(self.puzzle)
        self.puzzle = new
        self.moves += 1
        self.last_move = self.t
        if gained:                                       # une caisse vient d'arriver sur une cible
            tile, ox, oy = self.board_geometry()
            r, c = gained[0]
            self.particles.burst(ox + c * tile + tile // 2, oy + r * tile + tile // 2)
        if self.puzzle.isGoal():
            self.win_time = self.t
            self.autoplay = False
        return True

    def undo(self):
        if self.history and not self.autoplay and self.win_time is None:
            self.puzzle = self.history.pop()
            self.moves -= 1

    # ------------------------------------------------------------------
    # Solveurs en arrière-plan
    # ------------------------------------------------------------------
    def start_job(self, key):
        if key in self.results or key in self.jobs:
            return
        level, name = key
        job = {"done": False, "result": None}
        self.jobs[key] = job
        lines = list(LEVELS[level])

        def work():
            try:
                job["result"] = self.solvers[name](lines)
            except Exception as exc:                    # ne jamais tuer l'interface
                job["result"] = {"solution": None, "error": str(exc)}
            job["done"] = True

        threading.Thread(target=work, daemon=True).start()

    def request_solve(self, name):
        key = (self.level, name)
        self.reset_level()
        self.solver_name = name
        if key in self.results:
            self.begin_replay(key)
        else:
            self.pending = key
            self.start_job(key)

    def begin_replay(self, key):
        res = self.results[key]
        if res.get("solution") is None:
            self.toast(f"{key[1]}: no solution found")
            return
        self.reset_level()
        self.solver_name = key[1]
        self.queue, self.qpos = list(res["solution"]), 0
        self.current = dict(res, solver=key[1])
        self.autoplay, self.paused = True, False
        self.last_step = self.t

    def start_compare(self):
        for name in self.names:
            self.start_job((self.level, name))
        self.go("compare")

    def thinking(self):
        return self.pending is not None and self.pending in self.jobs

    # ------------------------------------------------------------------
    # Événements
    # ------------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.handle_click(event.pos)
        elif event.type == pygame.KEYDOWN:
            self.handle_key(event.key)

    def handle_click(self, pos):
        hit = lambda rect: rect.collidepoint(pos)
        if self.scene != "menu" and hit(self.MENU):
            self.go("menu")
            return

        if self.scene == "menu":
            if hit(self.START):
                self.selected = None
                self.go("levels")

        elif self.scene == "levels":
            for i, rect in enumerate(self.CARDS):
                if hit(rect):
                    self.selected = i
            if hit(self.SELECT) and self.selected is not None:
                self.start_level(self.selected)

        elif self.scene == "game":
            busy = self.autoplay or self.thinking()
            if hit(self.ACTIONS["COMPARE"]):
                self.start_compare()
            elif hit(self.ACTIONS["RESET"]):
                self.reset_level()
            elif hit(self.ACTIONS["UNDO"]):
                self.undo()
            elif hit(self.ACTIONS["PAUSE"]) and self.autoplay:
                self.paused = not self.paused
            elif hit(self.SPEED_MINUS):
                self.speed_i = max(0, self.speed_i - 1)
            elif hit(self.SPEED_PLUS):
                self.speed_i = min(len(SPEEDS) - 1, self.speed_i + 1)
            elif not busy and self.win_time is None:
                for name, rect in zip(self.names, self.ALGOS):
                    if hit(rect):
                        self.request_solve(name)

        elif self.scene == "done":
            if hit(self.DONE["LEVELS"]):
                self.selected = None
                self.go("levels")
            elif hit(self.DONE["AGAIN"]):
                self.reset_level()
                self.go("game")
            elif hit(self.DONE["COMPARE"]):
                self.start_compare()
            elif hit(self.DONE["NEXT"]) and self.level < len(LEVELS) - 1:
                self.start_level(self.level + 1)

        elif self.scene == "compare":
            if hit(self.CMP_BACK):
                if self.win_time is not None:
                    self.reset_level()
                self.go("game")
            elif hit(self.CMP_LEVELS):
                self.selected = None
                self.go("levels")

    def handle_key(self, key):
        if key == pygame.K_ESCAPE:
            self.go("menu")
        elif self.scene == "game":
            if key in KEY_TO_ACTION and not self.autoplay and not self.thinking() \
                    and self.win_time is None:
                self.play_action(KEY_TO_ACTION[key])
            elif key == pygame.K_u:
                self.undo()
            elif key == pygame.K_r:
                self.reset_level()
            elif key == pygame.K_SPACE and self.autoplay:
                self.paused = not self.paused

    # ------------------------------------------------------------------
    # Mise à jour
    # ------------------------------------------------------------------
    def update(self):
        self.ambient.update(self.dt)
        self.particles.update(self.dt)

        for key, job in list(self.jobs.items()):             # calculs terminés ?
            if job["done"]:
                self.results[key] = job["result"]
                self.result_time[key] = self.t
                del self.jobs[key]
                if job["result"].get("error"):
                    self.toast(f"{key[1]}: error ({job['result']['error'][:30]})")
                if self.pending == key:
                    self.pending = None
                    if self.scene == "game" and key[0] == self.level:
                        self.begin_replay(key)

        if self.scene != "game":
            return
        delay = BASE_STEP_MS / SPEEDS[self.speed_i]
        if self.autoplay and not self.paused and self.qpos < len(self.queue) \
                and self.t - self.last_step >= delay:
            self.last_step = self.t
            self.play_action(self.queue[self.qpos])
            self.qpos += 1
            if self.qpos >= len(self.queue) and self.win_time is None:
                self.autoplay = False
        if self.win_time is not None and self.t - self.win_time > 1000:
            self.particles.confetti(WIDTH)
            self.go("done")

    # ------------------------------------------------------------------
    # Dessin
    # ------------------------------------------------------------------
    def draw(self):
        mouse = pygame.mouse.get_pos()
        self.screen.blit(self.bg, (0, 0))
        self.screen.blit(self.assets.exact("drip", (WIDTH, WIDTH)), (0, 0))
        self.ambient.draw(self.screen, self.t)
        getattr(self, "draw_" + self.scene)(mouse)
        self.particles.draw(self.screen)
        if pygame.mouse.get_focused():
            hx, hy = self.cursor_hotspot
            self.screen.blit(self.cursor_img, (mouse[0] - hx, mouse[1] - hy))

    def draw_menu_button(self, mouse):
        self.screen.blit(self.assets.exact("button_menu", self.MENU.size), self.MENU)
        if self.MENU.collidepoint(mouse):
            pygame.draw.rect(self.screen, WHITE, self.MENU, 3, border_radius=18)

    def title(self, text, y, font="title", amp=6):
        draw_text_wave(self.screen, text, self.fonts[font], HOT_PINK, (WIDTH // 2, y),
                       self.t, amp=amp, shadow=PURPLE, offset=4)

    def twinkle(self, x, y, phase, px=3):
        a = 120 + 135 * (0.5 + 0.5 * math.sin(self.t / 300 + phase))
        img = self.sprites.get("sparkle", px, alpha=a)
        self.screen.blit(img, img.get_rect(center=(x, y)))

    # ---- MENU --------------------------------------------------------
    def draw_menu(self, mouse):
        f, t = self.fonts, self.t
        crown = self.sprites.get("crown", 7)
        self.screen.blit(crown, crown.get_rect(center=(WIDTH // 2, 168 + math.sin(t / 400) * 5)))
        self.title("Sokoban Game", 270, font="huge", amp=9)
        draw_text(self.screen, "~ pixel princess edition ~", f["normal"], DARK_PURPLE,
                  (WIDTH // 2, 340))
        draw_text(self.screen, "Push every cake onto a star!", f["small"], PURPLE,
                  (WIDTH // 2, 385))
        for i, (x, y) in enumerate([(300, 215), (800, 215), (230, 300), (870, 310), (360, 400)]):
            self.twinkle(x, y, i * 1.3, px=3 + i % 2)

        pulse = int(math.sin(t / 300) * 4)
        start = self.START.inflate(pulse * 2, pulse)
        draw_button(self.screen, start, "START", f["big"], hover=self.START.collidepoint(mouse))
        for i in range(3):                                # coeurs sous le bouton
            h = self.sprites.get("heart", 4)
            self.screen.blit(h, h.get_rect(center=(WIDTH // 2 + (i - 1) * 46,
                                                   575 + math.sin(t / 250 + i) * 5)))

        girl = self.assets.fit("player", 300, 330)
        self.screen.blit(girl, girl.get_rect(midbottom=(170, 660 + math.sin(t / 500) * 8)))
        cake = self.assets.fit("box", 170)
        self.screen.blit(cake, cake.get_rect(midbottom=(900, 640 + math.sin(t / 420 + 1) * 8)))

    # ---- LEVELS ------------------------------------------------------
    def draw_levels(self, mouse):
        f = self.fonts
        self.title("Choose a level", 62)
        for i, rect in enumerate(self.CARDS):
            chosen, hover = i == self.selected, rect.collidepoint(mouse)
            r = rect.move(0, -6 if hover or chosen else 0)
            draw_panel(self.screen, r, fill=WHITE if hover else ui.PANEL_FILL,
                       border=HOT_PINK if chosen else PURPLE)
            grid = self.starts[i].grid
            tile = fit_tile(len(grid), len(grid[0]), r.w - 40, 110, 36)
            ox = r.centerx - len(grid[0]) * tile // 2
            oy = r.y + 18 + (110 - len(grid) * tile) // 2
            draw_board(self.screen, grid, self.inside[i], self.walls[i], self.assets,
                       self.sprites, tile, (ox, oy))
            draw_text(self.screen, LEVEL_NAMES[i], f["normal"], DARK_PURPLE,
                      (r.centerx, r.bottom - 52))
            boxes = count_cells(grid, "B*")
            draw_text(self.screen, f"{boxes} cake{'s' if boxes > 1 else ''}", f["small"],
                      PURPLE, (r.centerx, r.bottom - 26))
            if chosen:
                star = self.sprites.get("star", 4)
                self.screen.blit(star, star.get_rect(center=(r.right - 22, r.y + 22
                                                              + math.sin(self.t / 200) * 3)))
        draw_button(self.screen, self.SELECT, "SELECT", f["big"],
                    hover=self.SELECT.collidepoint(mouse), enabled=self.selected is not None)
        self.draw_menu_button(mouse)

    # ---- GAME --------------------------------------------------------
    def draw_game(self, mouse):
        f, s = self.fonts, self.screen
        self.title(LEVEL_NAMES[self.level], 52)
        draw_panel(s, self.BOARD_PANEL)

        tile, ox, oy = self.board_geometry()
        since = self.t - self.last_move
        hop = int(math.sin(min(1.0, since / 220) * math.pi) * tile * 0.14) if since < 220 else 0
        draw_board(s, self.puzzle.grid, self.inside[self.level], self.walls[self.level],
                   self.assets, self.sprites, tile, (ox, oy), t=self.t, hop=hop)

        # cakes restants
        left = count_cells(self.puzzle.grid, "B")
        h = self.sprites.get("heart", 3)
        s.blit(h, (self.BOARD_PANEL.x + 22, self.BOARD_PANEL.y + 18))
        draw_text(s, f"Cakes left: {left}", f["small"], DARK_PURPLE,
                  (self.BOARD_PANEL.x + 62, self.BOARD_PANEL.y + 22), anchor="midleft")

        if self.thinking():
            self.draw_thinking(self.BOARD_PANEL, f"{self.pending[1]} is thinking")
        if self.toast_text and self.t < self.toast_until:
            draw_text(s, self.toast_text, f["normal"], (200, 60, 90),
                      (WIDTH // 2, 558), shadow=WHITE, offset=2)

        self.draw_hud()

        # boutons
        busy = self.autoplay or self.thinking()
        for name, rect in zip(self.names, self.ALGOS):
            draw_button(s, rect, name, f["normal"], hover=rect.collidepoint(mouse),
                        enabled=not busy and self.win_time is None,
                        active=(name == self.solver_name and (self.autoplay or self.thinking())))
        for name, rect in self.ACTIONS.items():
            label, enabled = name, True
            if name == "PAUSE":
                label = "PLAY" if self.paused else "PAUSE"
                enabled = self.autoplay
            elif name == "UNDO":
                enabled = bool(self.history) and not busy
            draw_button(s, rect, label, f["normal"], hover=rect.collidepoint(mouse), enabled=enabled)
        self.draw_menu_button(mouse)

    def draw_thinking(self, rect, text):
        veil = pygame.Surface(rect.size, pygame.SRCALPHA)
        veil.fill((255, 245, 250, 170))
        self.screen.blit(veil, rect.topleft)
        cx, cy = rect.center
        for i in range(8):                                  # anneau d'étincelles qui tourne
            ang = self.t / 350 + i * math.tau / 8
            glow = 0.3 + 0.7 * ((math.sin(self.t / 200 - i * 0.8) + 1) / 2)
            img = self.sprites.get("sparkle" if i % 2 else "heart", 4, alpha=255 * glow)
            self.screen.blit(img, img.get_rect(center=(cx + math.cos(ang) * 46,
                                                       cy - 20 + math.sin(ang) * 46)))
        dots = "." * (1 + int(self.t / 400) % 3)
        draw_text(self.screen, text + dots, self.fonts["normal"], DARK_PURPLE,
                  (cx, cy + 62), shadow=WHITE, offset=2)

    def draw_hud(self):
        f, s, H = self.fonts, self.screen, self.HUD
        draw_panel(s, H)
        res = self.current
        total = len(self.queue)
        rows = [
            ("ALGORITHM", self.solver_name if (res or self.thinking()) else "by hand"),
            ("STEPS", f"{self.qpos} / {total}" if total else str(self.moves)),
            ("COST", str(res["cost"]) if res else str(self.moves)),
            ("NODES EXPANDED", str(res.get("expanded", "-")) if res else "-"),
        ]
        y = H.y + 34
        for label, value in rows:
            draw_text(s, label, f["small"], PURPLE, (H.x + 24, y), anchor="midleft")
            draw_text(s, value, f["normal"], DARK_PURPLE, (H.x + 24, y + 28), anchor="midleft")
            y += 68
        draw_progress(s, pygame.Rect(H.x + 24, y - 6, H.w - 48, 24),
                      (self.qpos / total) if total else 0)
        draw_text(s, "Arrows: play by hand", f["small"], PURPLE, (H.centerx, y + 26))
        # vitesse
        small = self.fonts["big"]
        mouse = pygame.mouse.get_pos()
        draw_button(s, self.SPEED_MINUS, "-", small, hover=self.SPEED_MINUS.collidepoint(mouse),
                    enabled=self.speed_i > 0)
        draw_button(s, self.SPEED_PLUS, "+", small, hover=self.SPEED_PLUS.collidepoint(mouse),
                    enabled=self.speed_i < len(SPEEDS) - 1)
        label = f"x{SPEEDS[self.speed_i]:g}"
        draw_text(s, label, f["normal"], DARK_PURPLE, (H.centerx, self.SPEED_MINUS.centery))
        draw_text(s, "SPEED", f["small"], PURPLE, (H.centerx, self.SPEED_MINUS.y - 12))

    # ---- LEVEL COMPLETED --------------------------------------------
    def draw_done(self, mouse):
        f, s = self.fonts, self.screen
        crown = self.sprites.get("crown", 6)
        s.blit(crown, crown.get_rect(center=(WIDTH // 2, 118 + math.sin(self.t / 350) * 6)))
        self.title("Level completed!", 200, font="huge", amp=9)
        for i, (x, y) in enumerate([(210, 150), (890, 160), (150, 260), (950, 250)]):
            self.twinkle(x, y, i, px=4)

        panel = pygame.Rect(WIDTH // 2 - 320, 280, 640, 270)
        draw_panel(s, panel)
        res = self.current
        lines = [("Solved by", res["solver"] if res else "your own paws!"),
                 ("Steps", str(self.moves)),
                 ("Cost", str(res["cost"]) if res else str(self.moves)),
                 ("Nodes expanded", str(res.get("expanded", "-")) if res else "-")]
        y = panel.y + 52
        for label, value in lines:
            draw_text(s, label, f["normal"], PURPLE, (panel.x + 50, y), anchor="midleft")
            draw_text(s, value, f["normal"], HOT_PINK, (panel.right - 50, y), anchor="midright")
            y += 56

        last = self.level == len(LEVELS) - 1
        for name, rect in self.DONE.items():
            draw_button(s, rect, name, f["normal"], hover=rect.collidepoint(mouse),
                        enabled=not (name == "NEXT" and last))
        self.draw_menu_button(mouse)

    # ---- COMPARISON --------------------------------------------------
    def draw_compare(self, mouse):
        f, s, P = self.fonts, self.screen, self.CMP_PANEL
        self.title("Comparison", 52)
        draw_text(s, LEVEL_NAMES[self.level], f["normal"], DARK_PURPLE, (WIDTH // 2, 96))
        draw_panel(s, P)

        draw_text(s, "ALGORITHM", f["small"], PURPLE, (P.x + 80, P.y + 34), anchor="midleft")
        draw_text(s, "COST", f["small"], PURPLE, (P.x + 330, P.y + 34))
        draw_text(s, "NODES EXPANDED", f["small"], PURPLE, (P.x + 470, P.y + 34), anchor="midleft")

        keys = [(self.level, n) for n in self.names]
        done = {k: self.results[k] for k in keys
                if k in self.results and self.results[k].get("solution") is not None}
        expanded = {k: r["expanded"] for k, r in done.items()}
        best = min(expanded, key=expanded.get) if len(done) > 1 else None
        biggest = max(expanded.values()) if expanded else 1
        bfs_key = (self.level, "BFS")
        bar_x, bar_w = P.x + 470, 420

        y = P.y + 92
        for key in keys:
            name = key[1]
            draw_text(s, name, f["normal"], DARK_PURPLE, (P.x + 80, y), anchor="midleft")
            if key in done:
                res = done[key]
                grow = min(1.0, (self.t - self.result_time.get(key, 0)) / 700)
                draw_text(s, str(res["cost"]), f["normal"], DARK_PURPLE, (P.x + 330, y))
                w = max(10, int(bar_w * 0.8 * res["expanded"] / biggest * grow))
                bar = pygame.Rect(bar_x, y - 15, w, 30)
                is_best = key == best
                pygame.draw.rect(s, PURPLE, bar.inflate(6, 6), border_radius=10)
                pygame.draw.rect(s, GOLD if is_best else PINK, bar, border_radius=8)
                pygame.draw.rect(s, WHITE, (bar.x + 6, bar.y + 4, max(0, bar.w - 12), 5),
                                 border_radius=2)
                label = str(res["expanded"])
                if key != bfs_key and bfs_key in done and done[bfs_key]["expanded"] > 0:
                    pct = (res["expanded"] / done[bfs_key]["expanded"] - 1) * 100
                    label += f"  ({pct:+.0f}%)"
                draw_text(s, label, f["small"], DARK_PURPLE, (bar.right + 14, y), anchor="midleft")
                if is_best:
                    crown = self.sprites.get("crown", 3)
                    s.blit(crown, crown.get_rect(center=(P.x + 46, y)))
            elif key in self.jobs:
                for i in range(3):
                    ang = self.t / 300 + i * 2.1
                    sp = self.sprites.get("sparkle", 3)
                    s.blit(sp, sp.get_rect(center=(P.x + 330 + math.cos(ang) * 14,
                                                   y + math.sin(ang) * 14)))
                draw_text(s, "thinking" + "." * (1 + int(self.t / 400) % 3), f["small"], PURPLE,
                          (bar_x, y), anchor="midleft")
            elif key in self.results:
                draw_text(s, "no solution", f["small"], (200, 60, 90), (bar_x, y), anchor="midleft")
            y += 66

        if best:
            line = f"Fewest nodes: {best[1]}"
            if bfs_key in done and best != bfs_key:
                ratio = done[bfs_key]["expanded"] / max(1, expanded[best])
                line += f"  (x{ratio:.1f} fewer than BFS)"
            draw_text(s, line, f["normal"], HOT_PINK, (WIDTH // 2, P.bottom - 38), shadow=WHITE,
                      offset=2)
        elif any(k in self.jobs for k in keys):
            draw_text(s, "Running all algorithms in the background...", f["small"], PURPLE,
                      (WIDTH // 2, P.bottom - 38))

        draw_button(s, self.CMP_BACK, "BACK", f["big"], hover=self.CMP_BACK.collidepoint(mouse))
        draw_button(s, self.CMP_LEVELS, "LEVELS", f["big"],
                    hover=self.CMP_LEVELS.collidepoint(mouse))
        self.draw_menu_button(mouse)

    # ------------------------------------------------------------------
    def run(self):
        while self.running:
            self.dt = self.clock.tick(FPS) / 1000
            self.t = pygame.time.get_ticks()
            for event in pygame.event.get():
                self.handle_event(event)
            self.update()
            self.draw()
            pygame.display.flip()
        pygame.quit()


def run_game(solvers=None):
    App(solvers).run()
