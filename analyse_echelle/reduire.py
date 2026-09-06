# -*- coding: utf-8 -*-
"""
Base de travail a l'echelle cible : reduit les 11 calques de chaque salle
(jour et nuit) aux dimensions de analyse_echelle/cibles.json.

C'est un point de depart pour le redessin, pas un livrable final : un
reechantillonnage non entier adoucit le pixel art, il faut reprendre a la main
les contours, les lattes de plancher et les croisillons de fenetre.

Sorties :
  calques_reduits/<dossier>/<jour|nuit>/*.png
  salles_reduites/<dossier>_<jour|nuit>.png   (composite de controle)
"""
import io, json, os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CALQUES = ['00_exterieur', '01_sol', '02_structure', '03_cadres_fenetres',
           '04_tableaux', '05_porte_maitre', '06_decorations', '07_objets',
           '08_ombres_acces', '09_eclairage_fixe', '10_bordure_avant']


def main():
    kit = json.load(io.open(os.path.join(REPO, 'kit.json'), encoding='utf-8'))
    cibles = {c['id']: c for c in json.load(
        io.open(os.path.join(HERE, 'cibles.json'), encoding='utf-8'))['salles']}
    for s in kit['salles']:
        W, H = cibles[s['id']]['toile_ajustee_px']
        for palette in ('jour', 'nuit'):
            dst = os.path.join(REPO, 'calques_reduits', s['dossier'], palette)
            os.makedirs(dst, exist_ok=True)
            comp = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            for c in CALQUES:
                src = os.path.join(REPO, 'calques', s['dossier'], palette, c + '.png')
                if not os.path.exists(src):
                    continue
                im = Image.open(src).convert('RGBA').resize((W, H), Image.LANCZOS)
                im.save(os.path.join(dst, c + '.png'))
                if c != '00_exterieur':
                    comp.alpha_composite(im)
            out = os.path.join(REPO, 'salles_reduites')
            os.makedirs(out, exist_ok=True)
            comp.save(os.path.join(out, '%s_%s.png' % (s['dossier'], palette)))
        print('%s %-26s -> %d x %d' % (s['id'], s['nom'][:26], W, H))


if __name__ == '__main__':
    main()
