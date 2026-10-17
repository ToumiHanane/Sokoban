# search.py -- Travail d'Ilham (Membre 2) : Node + BFS
# Code d'Ilham repris tel quel (logique inchangée) ; seuls la mise en page
# (indentation, import en haut du fichier) a été corrigée pour qu'il s'exécute.
from collections import deque


class Node:
    def __init__(self, state, parentNode=None, action=None):
        self.state = state
        self.parentNode = parentNode
        self.action = action


def BFS(s, successorsFn, isGoal):
    Open = deque()
    Closed = []
    init_node = Node(s, None, None)

    if isGoal(init_node.state):
        return init_node
    Open.append(init_node)
    Closed = []

    while len(Open) > 0:
        current = Open.popleft()
        Closed.append(current)
        for action, successor in successorsFn(current.state):
            child = Node(successor, current, action)
            if isGoal(child.state):
                return child
            closed_states = [node.state for node in Closed]
            open_states = [node.state for node in Open]
            if child.state not in closed_states and child.state not in open_states:
                Open.append(child)

    return None
