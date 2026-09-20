"""Composition des layouts « Plage — côte, mer en bas » (lot plage_cote_v2).

Source unique : `Brine_Cave_Entrance` (EoSO, PMD Sky) — 27 × 21 cellules de
24 px, UN calque, chaque cellule est un flipbook de 15 frames
(`FrameLength` 8). Deux layouts, extensions en LARGEUR uniquement (toutes les
adjacences verticales restent exactement celles de la source) :
« crique » 35 × 21 (module ×2) et « anse » 43 × 21 (module ×3).

Module = colonnes source [19..27) (mur, sol, rive, mer) : la boucle 26 → 19
respecte la phase du mur (période 4, jonction pixel-parfaite 135,4 = valeur
native) et du sol (113,0, sous le max natif) ; la mer (période 3, incompatible
avec 4 — démonstration dans ANALYSE §4) prend un saut de phase mesuré et
documenté sur les rangées 16-18 de chaque jonction intérieure.

Voir SPEC.md (composition) et ANALYSE.md (mesures).
"""
from __future__ import annotations

ORIG_W, ORIG_H = 27, 21
FRAMES = 15
CELL = 24

MODULE = list(range(19, 27))  # 8 colonnes : mur, sol, rive, mer, bord droit


def colmap(repeats: int) -> list[int]:
    """Colonnes sources : base [0..19) + module ×repeats (la dernière colonne
    du module, 26, est le bord droit natif de la source)."""
    return list(range(0, 19)) + MODULE * repeats


def rowmap() -> list[int]:
    """Aucune insertion verticale : rangées strictement identiques à la source."""
    return list(range(0, ORIG_H))


LAYOUTS = {
    'crique': {'repeats': 2, 'asset': 'plage_cv2_crique',
               'title': 'Plage — Crique de Beach Cave (mer en bas)'},
    'anse': {'repeats': 3, 'asset': 'plage_cv2_anse',
             'title': 'Plage — Grande anse de Beach Cave (mer en bas)'},
}

# Jonctions intérieures (26 | 19) : colonnes de carte où la paire se trouve,
# et rangées de mer (16-18) où le saut de phase est documenté et toléré.
SEA_PHASE_SKIP_ROWS = (16, 17, 18)


def junction_cols(name: str) -> list[int]:
    """Colonnes X de carte qui commencent une copie du module (copie 2+)."""
    return [19 + len(MODULE) * i for i in range(1, LAYOUTS[name]['repeats'])]


def dims(name: str) -> tuple[int, int]:
    spec = LAYOUTS[name]
    return len(colmap(spec['repeats'])), ORIG_H


def rive_y(name: str) -> int:
    return 16


def exit_rows(name: str) -> tuple[int, int]:
    return (12, 13)


def mouth_rows(name: str) -> tuple[int, int]:
    return (6, 7)


def source_of(name: str) -> dict[tuple[int, int], tuple[int, int]]:
    """Correspondance (X, Y) -> (sx, sy) pour toute la carte, coupe de sortie comprise."""
    cm, rp = colmap(LAYOUTS[name]['repeats']), rowmap()
    W = len(cm)
    mapping = {(X, Y): (cm[X], rp[Y]) for X in range(W) for Y in range(len(rp))}
    # Couloirs traversants : la fin de chaque copie du module est le bord
    # droit de la source (mur en 26, rocher mixte en 25 dont la sous-colonne
    # droite bloque le passage) — les deux colonnes sont ouvertes aux rangées
    # 12-13 (sol nu copié de (24,12)/(24,13)) à CHAQUE apparition, sinon
    # chaque copie resterait une bande fermée. Les rangées 11 et 14 gardent
    # le cadre rocheux naturel.
    for Xc in range(W):
        if cm[Xc] in (25, 26):
            for sy in (12, 13):
                mapping[(Xc, sy)] = (24, sy)
    return mapping


_OBJ_ANIM = {'$type': 'RogueEssence.Content.ObjAnimData, RogueEssence', 'AnimIndex': '',
             'FrameTime': 1, 'StartFrame': -1, 'EndFrame': -1, 'AnimDir': -1, 'Alpha': 255, 'AnimFlip': 0}


def entities(name: str) -> list[dict]:
    """Bloc entités : arrivée par la droite, sortie à droite, seuil de grotte à gauche.

    Formes JSON copiées des entités de la plage EoSO (lot plage_beach_cave_v1),
    colliders recalculés pour chaque layout. Coordonnées en pixels (24 px/cellule).
    Le marqueur est posé dans le couloir de sortie (dernière colonne, coupée en
    sol libre rangées 12-13) ; Exit couvre le couloir jusqu'au bord droit.
    """
    W, _ = dims(name)
    marker = {'EntName': 'Entrance', 'Direction': 2, 'EntEnabled': True, 'EntOrder': 0,
              'InteractOrder': 0, 'triggerType': 0,
              'Collider': {'X': (W - 1) * CELL + 4, 'Y': 12 * CELL + 4, 'Width': 16, 'Height': 16}}

    def obj(ent_name: str, collider: dict) -> dict:
        return {'EntName': ent_name, 'Direction': 0, 'EntEnabled': True, 'EntOrder': 0,
                'InteractOrder': 0, 'triggerType': 2, 'ObjectAnim': dict(_OBJ_ANIM),
                'Passable': False, 'CurrentAnim': dict(_OBJ_ANIM), 'AnimTime': {'Ticks': 0},
                'Cycles': 0, 'DrawOffset': {'X': 0, 'Y': 0}, 'Collider': collider}

    exit_obj = obj('Exit', {'X': (W - 1) * CELL + 8, 'Y': 12 * CELL, 'Width': 16, 'Height': 48})
    cave_obj = obj('Beach_Cave_Entrance', {'X': 9 * CELL, 'Y': 6 * CELL, 'Width': 72, 'Height': 48})
    return [{'Name': 'New EntLayer', 'Visible': True, 'MapChars': [],
             'GroundObjects': [exit_obj, cave_obj], 'Spawners': [], 'Markers': [marker]}]
