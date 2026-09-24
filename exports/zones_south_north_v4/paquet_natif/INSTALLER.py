#!/usr/bin/env python3
"""Copie le paquet natif sud->nord V4 dans un dossier MODS de PMDO.
Usage : python INSTALLER.py "C:/chemin/vers/PMDO/MODS/SouthNorthV4"  (le dossier est cree)
Copie Data/Ground/*.rsground et Content/Tile/*.tile. Aucun fichier du jeu n'est ecrase.
Ce paquet n'a pas ete teste dans le moteur : ouvrir d'abord dans PMDO Dev."""
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if len(sys.argv) != 2:
    print(__doc__)
    sys.exit(1)
dest = Path(sys.argv[1])
copied = 0
for sub in ('Data/Ground', 'Content/Tile'):
    for f in sorted((HERE / sub).glob('*')):
        target = dest / sub / f.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)
        copied += 1
        print('copie', target)
print(f'{copied} fichiers copies dans {dest}')
