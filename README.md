

Readme · MD
Sokoban — Projet 1 (Problem Solving, M1 MIV, USTHB 2026/2027)
Modélisation et résolution du puzzle Sokoban avec BFS, plus une interface Pygame.

Équipe et répartition
Membre	Rôle	Fichiers
Hanane	Modélisation de l'état	sokoban.py, test_sokoban.py
Ilhem	Node + BFS	search.py
Sarah	Niveaux, intégration, interface Pygame	levels.py, main.py, interface.py
Installation
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux / Mac
pip install -r requirements.txt
Lancer
Tests du modèle : python test_sokoban.py
Programme complet : python main.py
Convention de travail (Git)
Une branche par membre : hanane-sokoban, ilhem-search, sarah-interface.
On ne pousse jamais directement sur main : Pull Request, puis fusion.
git pull avant de commencer à travailler.
Chacune modifie uniquement ses propres fichiers.
Codage des cases
O mur,   vide, S cible, R joueur, B caisse, . joueur sur cible, * caisse sur cible.


