#!/usr/bin/env python3
"""Paquet natif PMDO pour Reverie Town v2 (RVT2_NE natif, RVT2_NO avec côté est MIROIR).

Réutilise l'écrivain de source/reverie_town_v1/build_native.py (même schéma 0.8.12.0, TexSize 1) ; sortie
exports/reverie_town_v2/paquet_natif/. Les tuiles de la feuille miroir sont livrées dans Content/Tile/
RVT_Cliffs_Miroir.tile et RVT_Cliffs_Miroir_Nuit.tile (disposition conservée : TexLoc = position dans la feuille
miroir). Aucun test dans le moteur PMDO n'a été effectué (moteur absent du bac à sable).
"""
import json
import sys
from pathlib import Path

import importlib.util

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'source/reverie_town_v1'))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bn = load('rvt1_build_native', ROOT / 'source/reverie_town_v1/build_native.py')   # outillage v1
carte_ne = load('rvt2_carte_ne', HERE / 'carte_ne.py')
carte_no = load('rvt2_carte_no', HERE / 'carte_no.py')

bn.OUT = ROOT / 'exports/reverie_town_v2/paquet_natif'


def main():
    manifest = {'native_schema_version': '0.8.12.0', 'tex_size': 1, 'tile_px': bn.T, 'frame_length': bn.FRAME_LENGTH,
                'runtime_tested': False, 'mirror_note': 'RVT2_NO : côté est du plateau en feuille miroir (option '
                '« comme CLIFF MIROR » de l\'utilisateur) ; RVT2_NE : 100 % natif.', 'maps': []}
    for mod, label in ((carte_ne, 'Reverie Town v2 - Nord-Est'), (carte_no, 'Reverie Town v2 - Nord-Ouest')):
        scene = mod.build()
        scene.verify()
        for mode in ('jour', 'nuit'):
            info = bn.build_map(scene, mode, f'{label} ({mode})')
            manifest['maps'].append(info)
            print(info['asset'], info['grid'], 'feuilles', len(info['sheets']), 'custom', info['custom_tiles'],
                  'miroir', info['mirror_tiles'], 'bloquées', info['blocked_tiles'])
    manifest['mirror_tile_sheets'] = bn.write_mirror_banks()
    (bn.OUT / 'manifest.json').write_text(json.dumps(manifest, indent=1, ensure_ascii=False))
    print('miroir .tile :', manifest['mirror_tile_sheets'])


if __name__ == '__main__':
    main()
