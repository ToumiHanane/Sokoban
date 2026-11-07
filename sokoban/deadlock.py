"""
deadlock.py  --  Détection des deadlocks (partie D de l'énoncé)

Positions mortes statiques (ne dépendent que des murs et des cibles) :
  * corner deadlock : case non-cible entourée de 2 murs formant un coin ;
  * line deadlock   : entre deux coins morts alignés, si tout un côté de la
    ligne est fait de murs et qu'aucune cible n'est sur la ligne, toutes les
    cases de la ligne sont mortes (la caisse ne peut que glisser le long du mur).

Une caisse 'B' posée sur une de ces cases ne pourra plus jamais atteindre une cible.
(Une caisse déjà sur cible '*' n'est jamais en deadlock : les cibles sont exclues.)
"""
from .puzzle import WALL, TARGET, BOX, BOX_ON_TARGET, PLAYER_ON_TARGET


def _targets_and_floor(state):
    targets, floor = set(), set()
    for r, row in enumerate(state.grid):
        for c, ch in enumerate(row):
            if ch != WALL:
                floor.add((r, c))
            if ch in (TARGET, BOX_ON_TARGET, PLAYER_ON_TARGET):
                targets.add((r, c))
    return targets, floor


def corner_deadlocks(state):
    """Cases non-cibles qui forment un coin (2 murs adjacents perpendiculaires)."""
    targets, floor = _targets_and_floor(state)
    is_wall = lambda r, c: state.cell(r, c) == WALL
    corners = set()
    for (r, c) in floor - targets:
        vertical = is_wall(r - 1, c) or is_wall(r + 1, c)
        horizontal = is_wall(r, c - 1) or is_wall(r, c + 1)
        if vertical and horizontal:
            corners.add((r, c))
    return corners


def compute_dead_positions(state):
    """Ensemble des positions mortes (coins + lignes) du niveau de `state`.
    À calculer UNE seule fois par niveau, puis à réutiliser pour tous les états."""
    targets, floor = _targets_and_floor(state)
    corners = corner_deadlocks(state)
    dead = set(corners)
    is_wall = lambda r, c: state.cell(r, c) == WALL

    def segment_dead(cells, side_cells):
        # toutes les cases du segment sont libres et non-cibles ...
        if any(p not in floor or p in targets for p in cells):
            return False
        # ... et un côté entier du segment est un mur
        return all(is_wall(*p) for p in side_cells[0]) or all(is_wall(*p) for p in side_cells[1])

    # lignes horizontales : coins consécutifs d'une même ligne
    by_row = {}
    for r, c in corners:
        by_row.setdefault(r, []).append(c)
    for r, cols in by_row.items():
        cols.sort()
        for c1, c2 in zip(cols, cols[1:]):
            span = range(c1, c2 + 1)
            cells = [(r, c) for c in span]
            sides = ([(r - 1, c) for c in span], [(r + 1, c) for c in span])
            if segment_dead(cells, sides):
                dead.update(cells)

    # lignes verticales : coins consécutifs d'une même colonne
    by_col = {}
    for r, c in corners:
        by_col.setdefault(c, []).append(r)
    for c, rows in by_col.items():
        rows.sort()
        for r1, r2 in zip(rows, rows[1:]):
            span = range(r1, r2 + 1)
            cells = [(r, c) for r in span]
            sides = ([(r, c - 1) for r in span], [(r, c + 1) for r in span])
            if segment_dead(cells, sides):
                dead.update(cells)

    return frozenset(dead)


def has_deadlock(state, dead_positions=None):
    """Vrai si `state` contient une caisse (hors cible) sur une position morte.

    dead_positions : résultat de compute_dead_positions (à passer pour être rapide).
    S'il est omis, il est recalculé à partir de l'état (pratique mais plus lent).
    """
    if dead_positions is None:
        dead_positions = compute_dead_positions(state)
    return any(state.grid[r][c] == BOX for r, c in dead_positions)
