"""
solvers.py  --  relie BFS / A* (et heuristiques, deadlock) à l'interface

Un solveur prend les lignes du niveau et renvoie un dict :
  {"solution": [actions] ou None, "cost": ..., "expanded": ...}
"""
from .puzzle import SokobanPuzzle
from .search import BFS, AStar
from .heuristics import h1, h2, h3
from .deadlock import compute_dead_positions, has_deadlock


def _run(lines, search):
    start = SokobanPuzzle(lines)
    expanded = 0

    def successors(state):              # on compte les noeuds développés
        nonlocal expanded
        expanded += 1
        return state.successorFunction()

    node = search(start, successors)
    if node is None:
        return {"solution": None, "expanded": expanded}
    return {"solution": node.getSolution(), "cost": node.g, "expanded": expanded}


def team_bfs(lines):
    return _run(lines, lambda s, succ: BFS(s, succ, SokobanPuzzle.isGoal))


def team_astar(h, use_deadlock=False):
    """Solveur A* avec l'heuristique h ; use_deadlock=True élague les deadlocks."""
    def solver(lines):
        def search(s, succ):
            is_dead = None
            if use_deadlock:
                dead = compute_dead_positions(s)          # calculé une seule fois
                is_dead = lambda state: has_deadlock(state, dead)
            return AStar(s, succ, SokobanPuzzle.isGoal, h, is_dead)
        return _run(lines, search)
    return solver


def default_solvers():
    """Les 5 algorithmes proposés dans l'interface (ordre d'affichage)."""
    return {
        "BFS": team_bfs,
        "A* h1": team_astar(h1),
        "A* h2": team_astar(h2),
        "A* h3": team_astar(h3),
        "A* h3+DL": team_astar(h3, use_deadlock=True),
    }
