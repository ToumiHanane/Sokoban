"""
puzzle.py  --  Formulation du problème (modélisation de l'état)

Formulation (Chapitre 1, section 1.2.1) :
- État              : la grille complète (murs, cases vides, cibles, joueur, caisses)
- État initial      : la grille du niveau chargé
- successorFunction : liste de (action, successeur)
- isGoal            : toutes les caisses sont sur des cibles
- Coût d'un pas     : 1 (coût du chemin = nombre d'actions)

Codage des cases (imposé par l'énoncé) :
'O' mur | ' ' vide | 'S' cible | 'R' joueur | 'B' caisse
'.' joueur sur une cible | '*' caisse sur une cible
"""

# --- Symboles -----------------------------------------------------------
WALL = "O"
EMPTY = " "
TARGET = "S"
PLAYER = "R"
BOX = "B"
PLAYER_ON_TARGET = "."
BOX_ON_TARGET = "*"

# --- Actions (énoncé : UP (-1,0), DOWN (1,0), LEFT (0,-1), RIGHT (0,1)) ---
MOVES = {
    "UP": (-1, 0),
    "DOWN": (1, 0),
    "LEFT": (0, -1),
    "RIGHT": (0, 1),
}


class SokobanPuzzle:
    """    L'état est IMMUABLE : la grille est un tuple de chaînes. Chaque successeur
    est un nouvel objet, l'état parent n'est jamais modifié. Cela permet à BFS
    de comparer des états ("child.state not in Closed") grâce à __eq__/__hash__.
    """

    # ------------------------------------------------------------------
    # init()
    # ------------------------------------------------------------------
    def __init__(self, grid):
        """(une chaîne = une ligne).    """
        rows = [str(row) for row in grid]
        if not rows:
            raise ValueError("La grille est vide.")

        # Lignes de longueurs différentes -> on complète avec des murs
        width = max(len(row) for row in rows)
        self.grid = tuple(row.ljust(width, WALL) for row in rows)
        self.rows = len(self.grid)
        self.cols = width

        self._validate()
        self.player = self._find_player()

    # ------------------------------------------------------------------
    # Construction interne (sans validation) pour les successeurs
    # ------------------------------------------------------------------
    @classmethod
    def _build(cls, grid, player):
        obj = cls.__new__(cls)
        obj.grid = grid
        obj.rows = len(grid)
        obj.cols = len(grid[0])
        obj.player = player
        return obj
    def _validate(self):
        """Vérifie que le niveau respecte les règles de l'énoncé."""
        flat = "".join(self.grid)
        valid = {WALL, EMPTY, TARGET, PLAYER, BOX, PLAYER_ON_TARGET, BOX_ON_TARGET}
        bad = set(flat) - valid
        if bad:
            raise ValueError(f"Caractères invalides dans la grille : {bad}")

        nb_players = flat.count(PLAYER) + flat.count(PLAYER_ON_TARGET)
        if nb_players != 1:
            raise ValueError(f"Il faut exactement 1 joueur (trouvé : {nb_players}).")

        nb_boxes = flat.count(BOX) + flat.count(BOX_ON_TARGET)
        nb_targets = flat.count(TARGET) + flat.count(BOX_ON_TARGET) + flat.count(PLAYER_ON_TARGET)
        if nb_boxes != nb_targets:
            raise ValueError(
                f"Il faut autant de caisses que de cibles (caisses={nb_boxes}, cibles={nb_targets})."
            )

    def _find_player(self):
        for r, row in enumerate(self.grid):
            for c, ch in enumerate(row):
                if ch in (PLAYER, PLAYER_ON_TARGET):
                    return (r, c)
        raise ValueError("Joueur introuvable.")  # ne devrait pas arriver après _validate

    # ------------------------------------------------------------------
    # Accès aux cases
    # ------------------------------------------------------------------
    def cell(self, r, c):
        """Contenu de la case (r, c). Hors grille = mur."""
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return self.grid[r][c]
        return WALL

    # ------------------------------------------------------------------
    # isGoal()
    # ------------------------------------------------------------------
    def isGoal(self):
        """But : toutes les caisses sont sur des cibles.

        Comme il y a autant de caisses que de cibles, il suffit qu'il ne
        reste aucune caisse 'B' hors cible.
        """
        return not any(BOX in row for row in self.grid)

    # ------------------------------------------------------------------
    # successorFunction()
    # ------------------------------------------------------------------
    def successorFunction(self):
        """Retourne la liste des paires (action, état_successeur) valides."""
        successors = []
        for action, (dr, dc) in MOVES.items():
            new_state = self._apply_move(dr, dc)
            if new_state is not None:
                successors.append((action, new_state))
        return successors

    def _apply_move(self, dr, dc):
        """Applique un déplacement (dr, dc). Retourne le nouvel état, ou None si invalide."""
        r, c = self.player
        nr, nc = r + dr, c + dc
        dest = self.cell(nr, nc)

        # 1) Mur : déplacement impossible
        if dest == WALL:
            return None

        cells = [list(row) for row in self.grid]

        # Le joueur quitte sa case : on restaure la cible si besoin
        cells[r][c] = TARGET if cells[r][c] == PLAYER_ON_TARGET else EMPTY

        if dest in (BOX, BOX_ON_TARGET):
            # 2) Poussée : la case derrière la caisse doit être libre
            #    (vide ou cible). Un mur ou une autre caisse bloque -> on ne
            #    peut donc jamais pousser 2 caisses ni tirer une caisse.
            br, bc = nr + dr, nc + dc
            beyond = self.cell(br, bc)
            if beyond not in (EMPTY, TARGET):
                return None
            cells[br][bc] = BOX_ON_TARGET if beyond == TARGET else BOX
            cells[nr][nc] = PLAYER_ON_TARGET if dest == BOX_ON_TARGET else PLAYER
        else:
            # 3) Simple déplacement sur une case vide ou une cible
            cells[nr][nc] = PLAYER_ON_TARGET if dest == TARGET else PLAYER

        new_grid = tuple("".join(row) for row in cells)
        return SokobanPuzzle._build(new_grid, (nr, nc))

    # ------------------------------------------------------------------
    # Comparaison / hachage (indispensable pour BFS : Closed et Open)
    # ------------------------------------------------------------------
    def __eq__(self, other):
        return isinstance(other, SokobanPuzzle) and self.grid == other.grid

    def __hash__(self):
        return hash(self.grid)

    # ------------------------------------------------------------------
    # Affichage
    # ------------------------------------------------------------------
    def __str__(self):
        return "\n".join(self.grid)

    def __repr__(self):
        return f"SokobanPuzzle(player={self.player}, boxes_left={sum(r.count(BOX) for r in self.grid)})"