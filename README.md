# Sokoban – Modélisation et résolution (BFS, A*, deadlocks) + interface Pygame

Projet 1 – Problem Solving, Master 1 Visual Computing, USTHB 2026/2027.

## Lancer

```bash
pip install -r requirements.txt
python main.py                      # interface graphique
python -m experiments.benchmark     # tableau comparatif en console (pour le rapport)
python -m unittest discover tests   # tests
```

## Structure

```
main.py                 point d'entrée de l'interface
sokoban/                le "moteur" (aucune dépendance à pygame)
  puzzle.py             SokobanPuzzle : état, isGoal, successorFunction
  search.py             Node, BFS, A* (avec élagage des deadlocks)
  heuristics.py         h1, h2, h3
  deadlock.py           coins + lignes morts, has_deadlock
  levels.py             les niveaux (dont les exemples de la Fig. 7)
  solvers.py            relie les algorithmes à l'interface (coût + noeuds développés)
gui/                    interface Pygame
  app.py                écrans, événements, calculs en arrière-plan
  ui.py                 sprites pixel-art, particules, boutons, panneaux
assets/                 images et police
tests/  experiments/    tests unitaires et benchmark
```

## Algorithmes proposés dans l'interface

BFS · A* h1 · A* h2 · A* h3 · A* h3+DL (h3 avec détection de deadlocks)

## Jeu

Flèches / WASD pour jouer, `U` annuler, `R` recommencer, `Espace` pause du replay,
`Échap` retour au menu. Le bouton **COMPARE** lance tous les algorithmes en arrière-plan.
