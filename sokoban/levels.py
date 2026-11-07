"""levels.py  --  niveaux du jeu (R joueur, O mur, ' ' vide, S cible, B caisse, . joueur/cible, * caisse/cible)"""

LEVELS = [
    ["OOOOOO",
     "OS B O",
     "O OR O",
     "O    O",
     "O    O",
     "OOOOOO"],

    ["OOOOOOOO",
     "O      O",
     "O OOOO O",
     "O  S   O",
     "O B  R O",
     "O      O",
     "OOOOOOOO"],

    ["OOOOOOOO",
     "O  R   O",
     "O B  B O",
     "O  O   O",
     "O S  S O",
     "OOOOOOOO"],

    ["OOOOOOOOO",
     "O   S   O",
     "O  B*B  O",
     "O   R   O",
     "O  S    O",
     "OOOOOOOOO"],

    ["  OOOOOO  ",
     "OOO S  OO ",
     "O   B R  O",
     "O  OB OO O",
     "OOO  S  OO",
     " OO    OOO",
     "  OOOOOO  "],

    # Figure 7 de l'énoncé - exemple 1 (3 caisses alignées dans un couloir)
    ["OOOOOOO",
     "OS O RO",
     "O  OB O",
     "OS  B O",
     "O  OB O",
     "OS O  O",
     "OOOOOOO"],

    # Figure 7 de l'énoncé - exemple 2 (4 caisses)
    ["OOOOOOOO",
     "OSSS OOO",
     "O S B  O",
     "O  BBB O",
     "OOOO  RO",
     "OOOOOOOO"],
]

LEVEL_NAMES = ["Level 1", "Level 2", "Level 3", "Level 4", "Level 5", "level 6", "level 7"]
