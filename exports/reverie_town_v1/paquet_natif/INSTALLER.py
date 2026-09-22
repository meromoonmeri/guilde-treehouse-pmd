#!/usr/bin/env python3
"""Copie le paquet natif Reverie Town v1 dans un dossier MODS de PMDO.
Usage : python INSTALLER.py "C:/chemin/vers/PMDO/MODS/ReverieTown"  (le dossier est créé)
Copie Data/Ground/*.rsground et Content/Tile/*.tile. Les feuilles Metano_Town_* sont celles du jeu (déjà présentes).
Aucun fichier du jeu n'est écrasé. Ce paquet n'a pas été testé dans le moteur : ouvrir d'abord dans PMDO Dev."""
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
        print('copié', target)
print(f'{copied} fichiers copiés dans {dest}')
