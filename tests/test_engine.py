"""Tests rapides :  python -m unittest discover tests"""
import unittest

from sokoban.puzzle import SokobanPuzzle
from sokoban.search import BFS, AStar
from sokoban.heuristics import h1, h2, h3
from sokoban.deadlock import compute_dead_positions, has_deadlock, corner_deadlocks
from sokoban.levels import LEVELS
from sokoban.solvers import default_solvers


class TestPuzzle(unittest.TestCase):
    def test_all_levels_are_valid(self):
        for lines in LEVELS:
            SokobanPuzzle(lines)

    def test_invalid_level_raises(self):
        with self.assertRaises(ValueError):
            SokobanPuzzle(["OOOOO", "OR*SO", "OOOOO"])      # 1 caisse pour 2 cibles

    def test_push_reaches_goal(self):
        s = SokobanPuzzle(["OOOOO", "ORBSO", "OOOOO"])
        nxt = dict(s.successorFunction())["RIGHT"]
        self.assertTrue(nxt.isGoal())

    def test_cannot_push_two_boxes(self):
        s = SokobanPuzzle(["OOOOOOO", "ORBBSSO", "OOOOOOO"])
        self.assertNotIn("RIGHT", [a for a, _ in s.successorFunction()])


class TestDeadlock(unittest.TestCase):
    def test_corner(self):
        s = SokobanPuzzle(["OOOOO", "O S O", "OB RO", "OOOOO"])
        self.assertIn((1, 1), corner_deadlocks(s))
        self.assertNotIn((1, 2), corner_deadlocks(s))       # cible : jamais morte

    def test_line(self):
        s = SokobanPuzzle(LEVELS[5])                         # couloir de la Fig. 7 ex. 1
        dead = compute_dead_positions(s)
        self.assertTrue(len(dead) > 0)

    def test_box_on_target_is_not_deadlock(self):
        s = SokobanPuzzle(["OOOOO", "O*R O", "OOOOO"])
        self.assertFalse(has_deadlock(s))


class TestSolvers(unittest.TestCase):
    def test_all_solvers_find_same_optimal_cost(self):
        for lines in LEVELS[:5]:
            costs = {n: s(lines)["cost"] for n, s in default_solvers().items()}
            self.assertEqual(len(set(costs.values())), 1, costs)

    def test_solution_really_solves(self):
        lines = LEVELS[2]
        res = default_solvers()["A* h3+DL"](lines)
        state = SokobanPuzzle(lines)
        for a in res["solution"]:
            state = dict(state.successorFunction())[a]
        self.assertTrue(state.isGoal())


if __name__ == "__main__":
    unittest.main()
