"""Tableau comparatif console (pour le rapport) :  python -m experiments.benchmark"""
from sokoban.levels import LEVELS, LEVEL_NAMES
from sokoban.solvers import default_solvers


def main():
    solvers = default_solvers()
    print("| Niveau | " + " | ".join(f"{n} (coût / noeuds)" for n in solvers) + " |")
    print("|---|" + "---|" * len(solvers))
    for name, lines in zip(LEVEL_NAMES, LEVELS):
        cells = []
        for solve in solvers.values():
            res = solve(lines)
            cells.append("aucune solution" if res["solution"] is None
                         else f'{res["cost"]} / {res["expanded"]}')
        print(f"| {name} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
