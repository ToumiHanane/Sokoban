"""
search.py  --  Node + BFS + A*

A* accepte en plus un test de deadlock optionnel (isDeadlock) : un enfant
qui contient une caisse bloquée à jamais n'est PAS ajouté à Open.
"""
from collections import deque
import heapq
from itertools import count


class Node:
    def __init__(self, state, parentNode=None, action=None):
        self.state = state
        self.parentNode = parentNode
        self.action = action
        # g : coût du chemin (coût d'un pas = 1)
        self.g = 0 if parentNode is None else parentNode.g + 1
        # f : fonction d'évaluation de A* (f = g + h)
        self.f = self.g

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

    def setF(self, h):
        """Calcule f = g + h(état) à partir d'une heuristique h."""
        self.f = self.g + h(self.state)


def BFS(s, successorsFn, isGoal):
    Open = deque()
    init_node = Node(s, None, None)

    if isGoal(init_node.state):
        return init_node
    Open.append(init_node)

    # sets au lieu de listes : le test "in" est instantané
    # (les états sont hachables grâce à __hash__ de puzzle.py)
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


def AStar(s, successorsFn, isGoal, h, isDeadlock=None):
    """A*.  isDeadlock(state) -> bool (optionnel) : si vrai, l'enfant est
    abandonné et n'entre jamais dans Open.

    Le test de but se fait à l'EXPANSION du noeud (quand on le retire de Open),
    ce qui garantit l'optimalité de A*. Un enfant but n'a de toute façon
    jamais de deadlock (il n'a plus aucune caisse hors cible).
    """
    init_node = Node(s, None, None)
    init_node.setF(h)

    tie = count()                                  # départage les noeuds de même f
    Open = [(init_node.f, next(tie), init_node)]   # file de priorité (tas) triée par f
    open_nodes = {init_node.state: init_node}      # état -> meilleur noeud dans Open
    closed_nodes = {}                              # état -> noeud dans Closed

    while Open:
        _, _, current = heapq.heappop(Open)
        # entrée périmée (noeud remplacé par un meilleur) : on l'ignore
        if open_nodes.get(current.state) is not current:
            continue
        del open_nodes[current.state]

        if isGoal(current.state):
            return current
        closed_nodes[current.state] = current

        for action, successor in successorsFn(current.state):
            child = Node(successor, current, action)

            # deadlock : on n'ajoute même pas l'enfant à Open
            if isDeadlock is not None and isDeadlock(child.state):
                continue

            child.setF(h)

            if child.state not in open_nodes and child.state not in closed_nodes:
                heapq.heappush(Open, (child.f, next(tie), child))
                open_nodes[child.state] = child
            elif child.state in open_nodes and open_nodes[child.state].f > child.f:
                heapq.heappush(Open, (child.f, next(tie), child))
                open_nodes[child.state] = child
            elif child.state in closed_nodes and closed_nodes[child.state].f > child.f:
                del closed_nodes[child.state]
                heapq.heappush(Open, (child.f, next(tie), child))
                open_nodes[child.state] = child

    return None
