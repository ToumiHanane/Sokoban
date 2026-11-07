"""heuristics.py  --  h1, h2, h3 pour A*"""

from .puzzle import WALL, TARGET, BOX, BOX_ON_TARGET, PLAYER_ON_TARGET

INF = float("inf")
DETOUR_COST = 2


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _boxes_not_placed(state):
   
    return [(r, c)
            for r, row in enumerate(state.grid)
            for c, ch in enumerate(row) if ch == BOX]





def _free_targets(state):
   
    return [(r, c)
            for r, row in enumerate(state.grid)
            for c, ch in enumerate(row)
            if ch in (TARGET, PLAYER_ON_TARGET)]



def h1(state):
    return len(_boxes_not_placed(state))


def h2(state):

    boxes = _boxes_not_placed(state)
    if not boxes:
        return 0
    targets = _free_targets(state)
    total = 2 * len(boxes)
    for b in boxes:
        total += min(manhattan(b, t) for t in targets)
    return total



# h3

def _path_is_blocked(state, start, end, row_first):
   
    (r1, c1), (r2, c2) = start, end
    corner = (r1, c2) if row_first else (r2, c1)
 
    def segment_has_wall(a, b):
        (ra, ca), (rb, cb) = a, b
        if ra == rb:                                  # segment horizontal
            lo, hi = sorted((ca, cb))
            return any(state.cell(ra, c) == WALL for c in range(lo, hi + 1))
        lo, hi = sorted((ra, rb))                     # segment vertical
        return any(state.cell(r, ca) == WALL for r in range(lo, hi + 1))
 
    return segment_has_wall(start, corner) or segment_has_wall(corner, end)
 
 
def _obstacle_cost(state, box, target):
   
    blocked_1 = _path_is_blocked(state, box, target, row_first=True)
    blocked_2 = _path_is_blocked(state, box, target, row_first=False)
    return DETOUR_COST if (blocked_1 and blocked_2) else 0
 
 
def h3(state):

    boxes = _boxes_not_placed(state)
    if not boxes:
        return 0
    targets = _free_targets(state)
 
    total = h2(state)
    for b in boxes:
        nearest = min(targets, key=lambda t: manhattan(b, t))
        total += _obstacle_cost(state, b, nearest)
    return total