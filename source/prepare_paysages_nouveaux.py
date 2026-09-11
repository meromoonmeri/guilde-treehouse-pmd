"""Entrée compatible : préparation des plans de zones et des cartes de palette cycling.

La version « image complète puis détourage » reste dans l'historique a23a0d5.
Elle n'est plus reconstruite par cette commande.
"""
from pathlib import Path
import json
from prepare_zones_tt import prepare

CONFIG=json.loads((Path(__file__).resolve().parent/'zones_treasure_town/layouts.json').read_text())

if __name__=='__main__':prepare()
