"""
sokoban_gui.py  -  task 3 of the Sokoban project (Pygame interface)

Screens:  MENU  ->  LEVEL SELECT  ->  GAME  ->  LEVEL COMPLETED

How to run:   python sokoban_gui.py        (needs:  pip install pygame)

How to plug in your teammates' solvers:  see register_solver() near the bottom
of the "SOLVERS" section.
"""

import os
import time
from collections import deque

import pygame

# ======================================================================
# 1. SETTINGS
# ======================================================================
WIDTH, HEIGHT = 960, 720
FPS = 60
ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
STEP_DELAY_MS = 350            # speed of the solution replay

# Colors (taken from your pastel assets)
BG_COLOR = (255, 238, 246)
PURPLE = (124, 114, 145)       # outlines / shadows
DARK_PURPLE = (92, 76, 120)    # normal text
PINK = (255, 192, 220)
PINK_HOVER = (255, 214, 232)
LAVENDER = (205, 188, 238)
WHITE = (255, 255, 255)
GREY = (200, 195, 208)
GOLD = (255, 214, 102)

# ======================================================================
# 2. LEVELS   (R=player  O=wall  ' '=empty  S=target  B=box  .=player on target  *=box on target)
#    thetre are 5 levels
# ======================================================================
LEVELS = [
    ["OOOOOO",
     "OS B O",
     "O OR O",
     "O    O",
     "O    O",
     "OOOOOO"],

    ["OOOOOOOO",
     "O      O",
     "O OOOO O",
     "O  S   O",
     "O B  R O",
     "O      O",
     "OOOOOOOO"],

    ["OOOOOOOO",
     "O  R   O",
     "O B  B O",
     "O  O   O",
     "O S  S O",
     "OOOOOOOO"],

    ["OOOOOOOOO",
     "O   S   O",
     "O  B*B  O",
     "O   R   O",
     "O  S    O",
     "OOOOOOOOO"],

    ["  OOOOOO  ",
     "OOO S  OO ",
     "O   B R  O",
     "O  OB OO O",
     "OOO  S  OO",
     " OO    OOO",
     "  OOOOOO  "],
]

# ======================================================================
# 3. GAME LOGIC  ( lists and tuples)
# ======================================================================
DIRECTIONS = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}


def normalize_action(action):
    """'UP' / 'up' / (-1, 0)  ->  (-1, 0)"""
    if isinstance(action, str):
        return DIRECTIONS[action.strip().upper()]
    return tuple(action)


def make_grid(lines):
    """list of strings -> list of lists (all rows padded to the same length)"""
    width = max(len(row) for row in lines)
    return [list(row.ljust(width)) for row in lines]


def grid_to_lines(grid):
    return ["".join(row) for row in grid]


def find_player(grid):
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell in ("R", "."):
                return r, c
    raise ValueError("No player on the board")


def apply_action(grid, action):
    """Returns (new_grid, moved).  moved is False if the move is illegal."""
    new = [row[:] for row in grid]                  # copy: old states stay intact
    dr, dc = normalize_action(action)
    r, c = find_player(new)
    nr, nc = r + dr, c + dc
    cell = new[nr][nc]

    if cell == "O":                                 # wall
        return grid, False

    if cell in ("B", "*"):                          # a box: try to push it
        br, bc = nr + dr, nc + dc
        if new[br][bc] in ("O", "B", "*"):          # blocked
            return grid, False
        new[br][bc] = "*" if new[br][bc] == "S" else "B"
        player_on_target = (cell == "*")
    else:                                           # ' ' or 'S'
        player_on_target = (cell == "S")

    new[nr][nc] = "." if player_on_target else "R"
    new[r][c] = "S" if new[r][c] == "." else " "
    return new, True


def is_won(grid):
    """All boxes are on targets  <=>  no plain 'B' left."""
    return not any("B" in row for row in grid)


def find_inside_cells(grid):
    """Cells reachable from the player without crossing a wall.
    We only draw floor there, so the blank padding around the maze stays empty."""
    start = find_player(grid)
    seen = {start}
    stack = [start]
    while stack:
        r, c = stack.pop()
        for dr, dc in DIRECTIONS.values():
            nr, nc = r + dr, c + dc
            if (0 <= nr < len(grid) and 0 <= nc < len(grid[0])
                    and (nr, nc) not in seen and grid[nr][nc] != "O"):
                seen.add((nr, nc))
                stack.append((nr, nc))
    return seen


# ======================================================================
# 4. SOLVERS  (the part you connect to your teammates' work)
# ======================================================================
# A solver is a function:   solver(lines) -> dict
#   lines  = the board as a list of strings (same format as LEVELS)
#   result = {"solution": ["UP", "RIGHT", ...]   (or None if no solution)
#             "cost": 12,          (optional)
#             "expanded": 340,     (optional, number of expanded nodes)
#             "time": 0.02}        (optional, seconds)
SOLVERS = {}


def register_solver(name, function):
    """Example (in your main file):
         from sokoban_gui import register_solver, run_game
         def my_bfs(lines):
             puzzle = SokobanPuzzle(lines)            # teammate's class
             node = bfs(puzzle)                       # teammate's BFS
             return {"solution": node.getSolution(), "cost": node.g}
         register_solver("BFS", my_bfs)
         run_game()
    """
    SOLVERS[name] = function


def placeholder_bfs(lines):
    """Small BFS so the interface works BEFORE the real solver exists.
    Replace it with your teammates' BFS using register_solver()."""
    start_time = time.time()
    grid = make_grid(lines)
    walls, targets, boxes, player = set(), set(), set(), None
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == "O":
                walls.add((r, c))
            if ch in "S.*":
                targets.add((r, c))
            if ch in "B*":
                boxes.add((r, c))
            if ch in "R.":
                player = (r, c)

    start = (player, frozenset(boxes))
    seen = {start}
    queue = deque([(start, [])])
    while queue:
        (pos, bxs), path = queue.popleft()
        if bxs == targets:
            return {"solution": path, "cost": len(path),
                    "expanded": len(seen), "time": time.time() - start_time}
        for name, (dr, dc) in DIRECTIONS.items():
            nxt = (pos[0] + dr, pos[1] + dc)
            if nxt in walls:
                continue
            new_boxes = bxs
            if nxt in bxs:
                beyond = (nxt[0] + dr, nxt[1] + dc)
                if beyond in walls or beyond in bxs:
                    continue
                new_boxes = (bxs - {nxt}) | {beyond}
            state = (nxt, new_boxes)
            if state not in seen:
                seen.add(state)
                queue.append((state, path + [name]))
    return {"solution": None, "expanded": len(seen), "time": time.time() - start_time}


# ======================================================================
# 5. ASSETS
# ======================================================================
class Assets:
    """Loads your images once and gives them back at the size we need."""

    def __init__(self):
        self.raw = {}
        for name in ("cursor", "button_menu", "player", "box", "wall", "floor", "drip"):
            path = os.path.join(ASSET_DIR, name + ".png")
            self.raw[name] = pygame.image.load(path).convert_alpha()
        self.cache = {}

    def exact(self, name, size):
        """Image stretched to exactly (w, h)."""
        key = (name, size, "exact")
        if key not in self.cache:
            self.cache[key] = pygame.transform.scale(self.raw[name], size)
        return self.cache[key]

    def fit(self, name, max_w, max_h=None):
        """Image scaled to fit in a max_w x max_h box, keeping its proportions."""
        max_h = max_h or max_w
        key = (name, max_w, max_h, "fit")
        if key not in self.cache:
            w, h = self.raw[name].get_size()
            ratio = min(max_w / w, max_h / h)
            self.cache[key] = pygame.transform.scale(
                self.raw[name], (max(1, int(w * ratio)), max(1, int(h * ratio))))
        return self.cache[key]


# ======================================================================
# 6. SMALL DRAWING HELPERS
# ======================================================================
def draw_text(surface, text, font, color, center, shadow=None, offset=3):
    if shadow:
        img = font.render(text, True, shadow)
        surface.blit(img, img.get_rect(center=(center[0] + offset, center[1] + offset)))
    img = font.render(text, True, color)
    surface.blit(img, img.get_rect(center=center))


def draw_button(surface, rect, text, font, hover=False, enabled=True):
    """Pastel button in the same style as your MENU image."""
    if enabled:
        fill = PINK_HOVER if hover else PINK
        border, text_color, shadow = PURPLE, WHITE, PURPLE
    else:
        fill, border, text_color, shadow = (232, 228, 236), GREY, WHITE, GREY
    pygame.draw.rect(surface, border, rect, border_radius=20)
    inner = rect.inflate(-8, -8)
    pygame.draw.rect(surface, fill, inner, border_radius=16)
    if enabled:   # lavender highlight on top, like the MENU image
        top = pygame.Rect(inner.x + 8, inner.y + 2, inner.w - 16, 8)
        pygame.draw.rect(surface, LAVENDER, top, border_radius=4)
    draw_text(surface, text, font, text_color, rect.center, shadow=shadow, offset=2)


def fit_tile(rows, cols, max_w, max_h, cap):
    return max(4, min(max_w // cols, max_h // rows, cap))


def draw_board(surface, grid, inside, assets, tile, origin):
    ox, oy = origin
    wall = assets.exact("wall", (tile, tile))
    floor = assets.exact("floor", (tile, tile))
    box = assets.fit("box", int(tile * 0.85))
    player = assets.fit("player", int(tile * 0.95))

    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            x, y = ox + c * tile, oy + r * tile
            if cell == "O":
                surface.blit(wall, (x, y))
                continue
            if (r, c) not in inside:
                continue
            surface.blit(floor, (x, y))
            center = (x + tile // 2, y + tile // 2)

            if cell in ("S", ".", "*"):                 # target mark
                if cell == "*":
                    pygame.draw.circle(surface, GOLD, center, int(tile * 0.46))
                else:
                    pygame.draw.circle(surface, (186, 146, 226), center,
                                       int(tile * 0.28), max(2, tile // 14))
                    pygame.draw.circle(surface, (255, 170, 205), center, max(2, tile // 10))
            if cell in ("B", "*"):
                surface.blit(box, box.get_rect(center=center))
            if cell in ("R", "."):
                surface.blit(player, player.get_rect(midbottom=(center[0], y + tile - 1)))


# ======================================================================
# 7. THE APPLICATION
# ======================================================================
# Layout (rectangles for clickable things)
START_RECT = pygame.Rect(WIDTH // 2 - 140, 330, 280, 84)
SELECT_RECT = pygame.Rect(WIDTH // 2 - 130, 628, 260, 70)
MENU_RECT = pygame.Rect(24, 636, 150, 64)
RESTART_RECT = pygame.Rect(WIDTH - 480, 636, 210, 64)
SOLVE_RECT = pygame.Rect(WIDTH - 250, 636, 226, 64)
LEVELS_RECT = pygame.Rect(WIDTH // 2 - 250, 590, 220, 70)
NEXT_RECT = pygame.Rect(WIDTH // 2 + 30, 590, 220, 70)

CARD_W, CARD_H, CARD_GAP = 172, 230, 16
CARDS_X = (WIDTH - (5 * CARD_W + 4 * CARD_GAP)) // 2
CARD_RECTS = [pygame.Rect(CARDS_X + i * (CARD_W + CARD_GAP), 180, CARD_W, CARD_H)
        for i in range(len(LEVELS))]

KEYS_TO_ACTION = {
    pygame.K_UP: "UP", pygame.K_w: "UP", pygame.K_z: "UP",          # z = AZERTY
    pygame.K_DOWN: "DOWN", pygame.K_s: "DOWN",
    pygame.K_LEFT: "LEFT", pygame.K_a: "LEFT", pygame.K_q: "LEFT",  # q = AZERTY
    pygame.K_RIGHT: "RIGHT", pygame.K_d: "RIGHT",
}


class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Sokoban Game")
        self.clock = pygame.time.Clock()
        pygame.mouse.set_visible(False)             # we draw our own cursor

        self.assets = Assets()
        pixel_font = os.path.join(ASSET_DIR, "PressStart2P-Regular.ttf")
        self.fonts = {
            "huge": pygame.font.Font(pixel_font, 40),
            "title": pygame.font.Font(pixel_font, 32),
            "big": pygame.font.Font(pixel_font, 24),
            "normal": pygame.font.Font(pixel_font, 16),
            "small": pygame.font.Font(pixel_font, 10),
        }
        self.cursor_img = self.assets.fit("cursor", 40, 40)
        self.cursor_hotspot = self.find_cursor_hotspot()

        if not SOLVERS:
            register_solver("BFS", placeholder_bfs)
        self.solver_names = list(SOLVERS.keys())
        self.solver_index = 0

        # Pre-compute level data (grid + inside cells)
        self.level_grids = [make_grid(lines) for lines in LEVELS]
        self.level_inside = [find_inside_cells(g) for g in self.level_grids]

        self.state = "menu"          # "menu" | "levels" | "game" | "done"
        self.selected = None         # level chosen on the selection screen
        self.running = True

        # game variables
        self.level_index = 0
        self.grid = None
        self.history = []
        self.moves = 0
        self.queue = []              # actions of the solver still to play
        self.autoplay = False
        self.last_step_time = 0
        self.solver_result = None
        self.win_time = None
        self.message = ""
        self.message_until = 0
        self.result = {}

    # ------------------------------------------------------------------
    def find_cursor_hotspot(self):
        """The tip of the arrow = the highest dark pixel of the cursor image."""
        w, h = self.cursor_img.get_size()
        for y in range(h):
            for x in range(w):
                r, g, b, a = self.cursor_img.get_at((x, y))
                if a > 200 and r + g + b < 200:
                    return x, y
        return 0, 0

    def go(self, state):
        self.state = state

    # ------------------------------------------------------------------
    # starting / resetting a level
    # ------------------------------------------------------------------
    def start_level(self, index):
        self.level_index = index
        self.reset_level()
        self.go("game")

    def reset_level(self):
        self.grid = [row[:] for row in self.level_grids[self.level_index]]
        self.history = []
        self.moves = 0
        self.queue = []
        self.autoplay = False
        self.solver_result = None
        self.win_time = None

    def play_action(self, action):
        new_grid, moved = apply_action(self.grid, action)
        if moved:
            self.history.append(self.grid)
            self.grid = new_grid
            self.moves += 1
            if is_won(self.grid):
                self.win_time = pygame.time.get_ticks()
                self.autoplay = False

    def undo(self):
        if self.history and not self.autoplay and self.win_time is None:
            self.grid = self.history.pop()
            self.moves -= 1

    def run_solver(self):
        name = self.solver_names[self.solver_index]
        result = SOLVERS[name](grid_to_lines(self.level_grids[self.level_index]))
        if not result or result.get("solution") is None:
            self.message = f"{name}: no solution found"
            self.message_until = pygame.time.get_ticks() + 2500
            return
        self.reset_level()
        self.queue = list(result["solution"])
        self.solver_result = dict(result, solver=name)
        self.autoplay = True
        self.last_step_time = pygame.time.get_ticks()

    def finish_level(self):
        if self.solver_result:                      # a solver played the solution
            res = self.solver_result
            n = len(res["solution"])
            self.result = {"cost": res.get("cost", n), "steps": n,
                    "solver": res["solver"],
                    "expanded": res.get("expanded"), "time": res.get("time")}
        else:                                       # the human player won
            self.result = {"cost": self.moves, "steps": self.moves}
        self.go("done")

    # ------------------------------------------------------------------
    # events
    # ------------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.handle_click(event.pos)
        elif event.type == pygame.KEYDOWN:
            self.handle_key(event.key)

    def handle_click(self, pos):
        if self.state == "menu":
            if START_RECT.collidepoint(pos):
                self.selected = None
                self.go("levels")

        elif self.state == "levels":
            for i, rect in enumerate(CARD_RECTS):
                if rect.collidepoint(pos):
                    self.selected = i
            if SELECT_RECT.collidepoint(pos) and self.selected is not None:
                self.start_level(self.selected)
            if MENU_RECT.collidepoint(pos):
                self.go("menu")

        elif self.state == "game":
            if MENU_RECT.collidepoint(pos):
                self.go("menu")
            elif RESTART_RECT.collidepoint(pos):
                self.reset_level()
            elif SOLVE_RECT.collidepoint(pos) and self.win_time is None:
                self.run_solver()

        elif self.state == "done":
            if MENU_RECT.collidepoint(pos):
                self.go("menu")
            elif self.levels_button_rect().collidepoint(pos):
                self.selected = None
                self.go("levels")
            elif NEXT_RECT.collidepoint(pos) and self.level_index < len(LEVELS) - 1:
                self.start_level(self.level_index + 1)

    def levels_button_rect(self):
        """On the last level there is no NEXT button, so LEVELS is centered."""
        if self.level_index == len(LEVELS) - 1:
            return LEVELS_RECT.move(140, 0)
        return LEVELS_RECT

    def handle_key(self, key):
        if key == pygame.K_ESCAPE:
            self.go("menu")
            return
        if self.state != "game":
            return
        if key in KEYS_TO_ACTION and not self.autoplay and self.win_time is None:
            self.play_action(KEYS_TO_ACTION[key])
        elif key == pygame.K_u or key == pygame.K_BACKSPACE:
            self.undo()
        elif key == pygame.K_r:
            self.reset_level()
        elif pygame.K_1 <= key <= pygame.K_9:        # choose the solver
            i = key - pygame.K_1
            if i < len(self.solver_names):
                self.solver_index = i

    # ------------------------------------------------------------------
    # update (animation timers)
    # ------------------------------------------------------------------
    def update(self):
        now = pygame.time.get_ticks()
        if self.state != "game":
            return
        if self.autoplay and self.queue and now - self.last_step_time >= STEP_DELAY_MS:
            self.last_step_time = now
            self.play_action(self.queue.pop(0))
        if self.win_time is not None and now - self.win_time > 800:
            self.finish_level()

    # ------------------------------------------------------------------
    # drawing
    # ------------------------------------------------------------------
    def draw_background(self):
        self.screen.fill(BG_COLOR)
        self.screen.blit(self.assets.exact("drip", (WIDTH, WIDTH)), (0, 0))

    def draw_menu_button(self, mouse):
        img = self.assets.exact("button_menu", MENU_RECT.size)
        self.screen.blit(img, MENU_RECT)
        if MENU_RECT.collidepoint(mouse):
            pygame.draw.rect(self.screen, WHITE, MENU_RECT, 3, border_radius=18)

    def draw(self):
        mouse = pygame.mouse.get_pos()
        self.draw_background()
        getattr(self, "draw_" + self.state)(mouse)

        # custom cursor, always drawn last
        if pygame.mouse.get_focused():
            hx, hy = self.cursor_hotspot
            self.screen.blit(self.cursor_img, (mouse[0] - hx, mouse[1] - hy))

    # ---- MENU --------------------------------------------------------
    def draw_menu(self, mouse):
        f = self.fonts
        draw_text(self.screen, "Sokoban Game", f["huge"], (240, 120, 170),
                  (WIDTH // 2, 230), shadow=PURPLE, offset=5)
        draw_button(self.screen, START_RECT, "START", f["big"],
                    hover=START_RECT.collidepoint(mouse))
        # decoration
        girl = self.assets.fit("player", 300, 330)
        self.screen.blit(girl, girl.get_rect(midbottom=(170, 650)))
        cake = self.assets.fit("box", 170)
        self.screen.blit(cake, cake.get_rect(midbottom=(800, 620)))

    # ---- LEVEL SELECT ------------------------------------------------
    def draw_levels(self, mouse):
        f = self.fonts
        draw_text(self.screen, "Choose a level", f["title"], (240, 120, 170),
                  (WIDTH // 2, 80), shadow=PURPLE, offset=4)

        for i, rect in enumerate(CARD_RECTS):
            chosen = (i == self.selected)
            hover = rect.collidepoint(mouse)
            border = (240, 120, 170) if chosen else PURPLE
            pygame.draw.rect(self.screen, border, rect, border_radius=18)
            pygame.draw.rect(self.screen, (255, 250, 253) if not hover else WHITE,
                             rect.inflate(-8 if not chosen else -12,
                                          -8 if not chosen else -12), border_radius=14)
            # mini preview of the level
            grid, inside = self.level_grids[i], self.level_inside[i]
            rows, cols = len(grid), len(grid[0])
            tile = fit_tile(rows, cols, CARD_W - 28, 140, 36)
            ox = rect.centerx - cols * tile // 2
            oy = rect.y + 20 + (140 - rows * tile) // 2
            draw_board(self.screen, grid, inside, self.assets, tile, (ox, oy))
            draw_text(self.screen, f"Level {i + 1}", f["normal"], DARK_PURPLE,
                      (rect.centerx, rect.bottom - 34))

        draw_button(self.screen, SELECT_RECT, "SELECT", f["big"],
                    hover=SELECT_RECT.collidepoint(mouse),
                    enabled=self.selected is not None)
        self.draw_menu_button(mouse)

    # ---- GAME --------------------------------------------------------
    def draw_game(self, mouse):
        f = self.fonts
        draw_text(self.screen, f"Level {self.level_index + 1}", f["title"],
                  (240, 120, 170), (WIDTH // 2, 70), shadow=PURPLE, offset=4)

        grid, inside = self.grid, self.level_inside[self.level_index]
        rows, cols = len(grid), len(grid[0])
        tile = fit_tile(rows, cols, 880, 410, 80)
        ox = (WIDTH - cols * tile) // 2
        oy = 150 + (410 - rows * tile) // 2
        draw_board(self.screen, grid, inside, self.assets, tile, (ox, oy))

        # info line
        now = pygame.time.get_ticks()
        if self.message and now < self.message_until:
            info, color = self.message, (200, 60, 90)
        else:
            solver = self.solver_names[self.solver_index]
            info = f"Moves: {self.moves}      Cost: {self.moves}      Solver: {solver}"
            color = DARK_PURPLE
        draw_text(self.screen, info, f["normal"], color, (WIDTH // 2, 582))
        hint = "Arrows / ZQSD: move   |   U: undo   |   R: restart"
        if len(self.solver_names) > 1:
            hint += "   |   1-9: choose solver"
        draw_text(self.screen, hint, f["small"], PURPLE, (WIDTH // 2, 612))

        self.draw_menu_button(mouse)
        draw_button(self.screen, RESTART_RECT, "RESTART", f["normal"],
                    hover=RESTART_RECT.collidepoint(mouse))
        draw_button(self.screen, SOLVE_RECT, "SOLVE", f["normal"],
                    hover=SOLVE_RECT.collidepoint(mouse),
                    enabled=not self.autoplay and self.win_time is None)

    # ---- LEVEL COMPLETED --------------------------------------------
    def draw_done(self, mouse):
        f = self.fonts
        draw_text(self.screen, "Level completed!", f["huge"], (240, 120, 170),
                  (WIDTH // 2, 200), shadow=PURPLE, offset=5)

        res = self.result
        lines = [f"Step cost: {res['cost']}", f"Number of steps: {res['steps']}"]
        if res.get("solver"):
            lines.append(f"Solved by: {res['solver']}")
            if res.get("expanded") is not None:
                lines.append(f"Nodes expanded: {res['expanded']}")
            if res.get("time") is not None:
                lines.append(f"Time: {res['time']:.3f} s")
        y = 320
        for text in lines:
            draw_text(self.screen, text, f["big"], DARK_PURPLE, (WIDTH // 2, y))
            y += 52

        last = self.level_index == len(LEVELS) - 1
        levels_rect = self.levels_button_rect()
        draw_button(self.screen, levels_rect, "LEVELS", f["big"],
                    hover=levels_rect.collidepoint(mouse))
        if not last:
            draw_button(self.screen, NEXT_RECT, "NEXT", f["big"],
                        hover=NEXT_RECT.collidepoint(mouse))
        self.draw_menu_button(mouse)

    # ------------------------------------------------------------------
    def run(self):
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()


def run_game():
    App().run()


def run_with_team_solver():
    from solvers import team_bfs            # BFS of the team (solvers.py)
    register_solver("BFS", team_bfs)
    run_game()


if __name__ == "__main__":
    run_with_team_solver()
