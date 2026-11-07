
"""Tests de sokoban.py  --  lancer avec :  python test_sokoban.py"""
import unittest
 
from sokoban.puzzle import SokobanPuzzle
 
 
def succ(state):
    """Dictionnaire {action: état} pour faciliter les tests."""
    return dict(state.successorFunction())
 
 
class TestInit(unittest.TestCase):
    def test_player_position(self):
        s = SokobanPuzzle(["OOOO", "ORSO", "OB O", "OOOO"])
        self.assertEqual(s.player, (1, 1))
 
    def test_no_player(self):
        with self.assertRaises(ValueError):
            SokobanPuzzle(["OOOO", "O SO", "OOOO"])
 
    def test_boxes_targets_mismatch(self):
        with self.assertRaises(ValueError):
            SokobanPuzzle(["OOOOO", "ORB O", "OOOOO"])
 
    def test_invalid_char(self):
        with self.assertRaises(ValueError):
            SokobanPuzzle(["OOOO", "ORXO", "OOOO"])
 
 
class TestMoves(unittest.TestCase):
    def test_simple_move(self):
        s = SokobanPuzzle(["OOOO", "OR O", "OOOO"])
        res = succ(s)
        self.assertEqual(list(res.keys()), ["RIGHT"])  # murs partout ailleurs
        self.assertEqual(res["RIGHT"].grid, ("OOOO", "O RO", "OOOO"))
 
    def test_wall_blocks(self):
        s = SokobanPuzzle(["OOO", "ORO", "OOO"])
        self.assertEqual(s.successorFunction(), [])
 
    def test_push_box(self):
        s = SokobanPuzzle(["OOOOOO", "ORB SO", "OOOOOO"])
        res = succ(s)
        self.assertEqual(res["RIGHT"].grid[1], "O RBSO")
        self.assertEqual(res["RIGHT"].player, (1, 2))
 
    def test_box_against_wall(self):
        s = SokobanPuzzle(["OOOOO", "ORBOS", "OOOOO"])
        self.assertNotIn("RIGHT", succ(s))
 
    def test_cannot_push_two_boxes(self):
        s = SokobanPuzzle(["OOOOOOO", "ORBB  O", "OSS   O", "OOOOOOO"])
        self.assertNotIn("RIGHT", succ(s))
 
    def test_cannot_pull(self):
        # Le joueur recule : la caisse reste en place
        s = SokobanPuzzle(["OOOOOO", "O RBSO", "OOOOOO"])
        res = succ(s)
        self.assertEqual(res["LEFT"].grid[1], "OR BSO")
 
 
class TestTargets(unittest.TestCase):
    def test_player_on_target_then_leaves(self):
        s = SokobanPuzzle(["OOOOOO", "ORSB O", "OOOOOO"])
        on_target = succ(s)["RIGHT"]
        self.assertEqual(on_target.grid[1], "O .B O")
        back = succ(on_target)["LEFT"]
        self.assertEqual(back.grid[1], "ORSB O")  # la cible est restaurée
 
    def test_box_on_target_and_pushed_off(self):
        s = SokobanPuzzle(["OOOOOO", "ORBS O", "OOOOOO"])
        s1 = succ(s)["RIGHT"]            # la caisse arrive sur la cible
        self.assertEqual(s1.grid[1], "O R* O")
        s2 = succ(s1)["RIGHT"]           # on pousse encore : elle quitte la cible
        self.assertEqual(s2.grid[1], "O  .BO")
 
 
class TestGoalAndImmutability(unittest.TestCase):
    def test_goal_reached_by_pushing(self):
        s = SokobanPuzzle(["OOOOOO", "ORB SO", "OOOOOO"])
        self.assertFalse(s.isGoal())
        s = succ(s)["RIGHT"]
        self.assertFalse(s.isGoal())
        s = succ(s)["RIGHT"]
        self.assertTrue(s.isGoal())
        self.assertEqual(s.grid[1], "O  R*O")
 
    def test_parent_not_modified(self):
        s = SokobanPuzzle(["OOOOOO", "ORB SO", "OOOOOO"])
        before = s.grid
        s.successorFunction()
        self.assertEqual(s.grid, before)
 
    def test_equality_and_hash(self):
        a = SokobanPuzzle(["OOOOOO", "ORB SO", "OOOOOO"])
        b = SokobanPuzzle(["OOOOOO", "ORB SO", "OOOOOO"])
        self.assertEqual(a, b)
        self.assertEqual(len({a, b}), 1)
        self.assertNotEqual(a, succ(a)["RIGHT"])
 
 
if __name__ == "__main__":
    unittest.main(verbosity=2)
 
