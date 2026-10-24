"""
SokobanPuzzle.py  --  Node + BFS  (Membre 2)

La classe SokobanPuzzle (état, isGoal, successorFunction) est dans sokoban.py.
On ne la redéfinit pas ici, sinon deux classes portent le même nom.
"""
from collections import deque


class Node:
    def __init__(self, state, parentNode=None, action=None):
        self.state = state
        self.parentNode = parentNode
        self.action = action
        # g : coût du chemin (coût d'un pas = 1)
        self.g = 0 if parentNode is None else parentNode.g + 1

    def getPath(self):
        """Liste des états de l'état initial jusqu'à ce noeud."""
        path, node = [], self
        while node is not None:
            path.append(node.state)
            node = node.parentNode
        return path[::-1]

    def getSolution(self):
        """Liste des actions appliquées depuis l'état initial."""
        actions, node = [], self
        while node.parentNode is not None:
            actions.append(node.action)
            node = node.parentNode
        return actions[::-1]


def BFS(s, successorsFn, isGoal):
    Open = deque()
    init_node = Node(s, None, None)

    if isGoal(init_node.state):
        return init_node
    Open.append(init_node)

    # sets au lieu de listes : même logique, mais la recherche "in" est
    # instantanée (les états sont hachables grâce à __hash__ de sokoban.py)
    open_states = {init_node.state}
    closed_states = set()

    while len(Open) > 0:
        current = Open.popleft()
        open_states.discard(current.state)
        closed_states.add(current.state)
        for action, successor in successorsFn(current.state):
            child = Node(successor, current, action)
            if isGoal(child.state):
                return child
            if child.state not in closed_states and child.state not in open_states:
                Open.append(child)
                open_states.add(child.state)

    return None
