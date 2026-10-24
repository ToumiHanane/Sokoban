"""
solvers.py  --  colle le BFS de l'équipe à l'interface (sokoban_gui.py)

L'interface appelle un solveur avec les lignes du niveau et attend un dict :
  {"solution": [actions] ou None, "cost": ..., "expanded": ..., "time": ...}
"""
import time

from sokoban import SokobanPuzzle
from SokobanPuzzle import BFS


def team_bfs(lines):
    start = SokobanPuzzle(lines)
    expanded = 0

    def successors(state):              # on compte les noeuds développés
        nonlocal expanded
        expanded += 1
        return state.successorFunction()

    t0 = time.time()
    node = BFS(start, successors, SokobanPuzzle.isGoal)
    elapsed = time.time() - t0

    if node is None:
        return {"solution": None, "expanded": expanded, "time": elapsed}
    return {"solution": node.getSolution(), "cost": node.g,
            "expanded": expanded, "time": elapsed}
