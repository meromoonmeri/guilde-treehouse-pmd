#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contrôles du lot « Cristal boréal — couches animées multiples ».

Les tests ne relancent jamais la génération : ils relisent les fichiers livrés et les recomposent
eux-mêmes, pour que « la scène equals la pile des calques » soit vérifié depuis les livrables et non
depuis la mémoire du build. Aucun test de navigateur ni de runtime PMD Online ici.
"""
import hashlib
import json
import struct
import sys
import unittest
import zipfile
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from source.cristal_boreal_layers_animees_v1 import build as b          # noqa: E402
from source.cristal_boreal_layers_animees_v1.lot import (OUT, R, V12, ZD, clip, empile, lire_ora,  # noqa: E402
                                                         poses_native, tint, webp_uri)

MANIFEST = json.loads((OUT / 'manifest.json').read_text())
ANIMEES = ['01_animation_eau_protegee', '08_aurore_ciel', '09_eclats_cristaux', '10_scintillement_givre',
           '11_lueur_sol']
PRESERVE = np.array(Image.open(b.SRC / 'references/cristal_preserve.png')) > 0
TERRAIN = np.array(Image.open(b.MD / 'terrain_detoure.png').convert('RGBA'))[..., 3] > 0


def poses(nom):
    d = OUT / 'calques' / nom
    return [np.array(Image.open(f)) for f in sorted(d.glob('frame_*.png'))]


def empreinte(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def anmf(chemin):
    """Les durées réellement écrites dans le conteneur WebP, sans passer par un décodeur."""
    brut = Path(chemin).read_bytes()
    i, dures = 12, []
    while i + 8 <= len(brut):
        quatre = brut[i:i + 4]
        taille = struct.unpack('<I', brut[i + 4:i + 8])[0]
        if quatre == b'ANMF':
            dures.append(int.from_bytes(brut[i + 8 + 12:i + 8 + 15], 'little'))
        i += 8 + taille + (taille & 1)
    return dures


def pile_a(t, avec_voile=True):
    """Recomposition de la pose t depuis les fichiers livrés, grille de 40 ms."""
    couches = []
    for nom in MANIFEST['ordre_pile']:
        if not avec_voile and nom == b.VOILE_NOM:
            continue
        if nom in b.STATIQUES:
            couches.append(Image.open(OUT / 'base' / (nom + '.png')).convert('RGBA'))
        else:
            liste = poses(nom)
            k = (t // MANIFEST['couches'][nom]['duree_ms']) % len(liste)
            couches.append(Image.fromarray(liste[k], 'RGBA'))
    return np.array(empile(Image.new('RGBA', b.TAILLE, (0, 0, 0, 0)), couches))


class Provenance(unittest.TestCase):
    def test_douze_poses_natives_recopyees_octet_pour_octet(self):
        for i in range(b.CONF['frames']):
            self.assertEqual(empreinte(OUT / 'calques' / '01_animation_eau_protegee' / ('frame_%02d.png' % i)),
                             empreinte(ZD / ('%s_01_animation_%03d.png' % (b.IDENT, i))),
                             'la pose %d ne serait plus le fichier du lot V1' % i)

    def test_cinq_calques_statiques_recopies(self):
        for nom in b.STATIQUES:
            self.assertEqual(empreinte(OUT / 'base' / (nom + '.png')),
                             empreinte(ZD / ('%s_%s.png' % (b.IDENT, nom))))
            self.assertEqual(empreinte(OUT / 'base' / (nom + '.png')), MANIFEST['base_sha256'][nom])

    def test_sources_declarees_au_manifeste(self):
        prov = MANIFEST['couches']
        self.assertEqual(empreinte(R / b.CONF['source']), prov['10_scintillement_givre']['source_sha256'])
        self.assertEqual(empreinte(V12 / 'onde_indexee.png'), prov['08_aurore_ciel']['source_sha256'])
        self.assertEqual(empreinte(V12 / 'palettes_8frames.json'), prov['08_aurore_ciel']['palette_sha256'])
        for nom, sha in zip(prov['09_eclats_cristaux']['sources'], prov['09_eclats_cristaux']['sha256']):
            self.assertEqual(sha, empreinte(ZD / ('%s_%s.png' % (b.IDENT, nom))))

    def test_le_manifeste_na_invente_aucune_couleur(self):
        """Les couleurs de l'aurore viennent toutes des huit palettes du lot V12, rien d'autre."""
        palettes = json.loads((V12 / 'palettes_8frames.json').read_text())['frames']
        autorisees = {tuple(c) for pal in palettes for c in pal}     # les neuf entrées, corps sombre compris
        for a in poses('08_aurore_ciel'):
            vive = a[..., 3] > 0
            vu = {tuple(int(v) for v in c) for c in np.unique(a[vive][..., :3], axis=0)}
            self.assertTrue(vu <= autorisees, 'couleurs hors palette V12 : %s' % sorted(vu - autorisees)[:4])
        alpha_ruban = set(np.unique(np.array(Image.open(V12 / 'onde_alpha.png'))).tolist())
        permises = {v for v in alpha_ruban if v <= b.VOILE} | {0, b.VOILE}     # le plafond de voile est déclaré
        for a in poses('08_aurore_ciel'):
            self.assertTrue(set(np.unique(a[..., 3]).tolist()) <= permises)


class Garanties(unittest.TestCase):
    def test_zone_protegee_ride_exactement_la_pose_native(self):
        natif, _ = poses_native(b.CONF['source'])
        for m in range(MANIFEST['poses_maitresse']):
            attendu = np.array(tint(Image.fromarray(natif[(m * b.PAS_MAITRE // b.NATIF_DUREE) % 12]),
                                    b.BIOME, b.PALETTE))
            scene = pile_a(m * b.PAS_MAITRE, avec_voile=False)
            self.assertTrue(np.array_equal(scene[PRESERVE], attendu[PRESERVE]),
                            'zone protégée modifiée à la pose %d' % m)

    def test_le_voile_ne_touche_que_le_ciel(self):
        for m in (0, 7, 13, 29, 47):
            t = m * b.PAS_MAITRE
            ciel = np.asarray(poses(b.VOILE_NOM)[0][..., 3] > 0)
            avec, sans = pile_a(t), pile_a(t, avec_voile=False)
            self.assertTrue(np.array_equal(avec[~ciel], sans[~ciel]), 'débordement du voile pose %d' % m)

    def test_le_voile_reste_un_voile(self):
        for a in poses(b.VOILE_NOM):
            self.assertLessEqual(int(a[..., 3].max()), MANIFEST['voile']['alpha_max'])
        self.assertEqual(MANIFEST['voile']['alpha_max'], b.VOILE)
        vu = np.array(Image.open(OUT / 'COMPOSITION.png'))
        nu = np.array(Image.open(OUT / 'COMPOSITION_SANS_VOILE.png'))
        self.assertGreater(int((vu != nu).any(-1).sum()), 1000, 'le voile ne se voit pas dans la scène')
        self.assertEqual(int(((vu != nu).any(-1) & PRESERVE).sum()), int((vu != nu).any(-1).sum()),
                         'le voile sortirait de la zone protégée du ciel')

    def test_les_trois_couches_ajoutees_n_ecrivent_jamais_sur_la_zone_protegee(self):
        for nom in ('09_eclats_cristaux', '10_scintillement_givre', '11_lueur_sol'):
            for a in poses(nom):
                self.assertEqual(int((a[..., 3] > 0)[PRESERVE].sum()), 0, '%s écrase la zone protégée' % nom)
            self.assertEqual(MANIFEST['couches'][nom]['ecrites_sur_zone_protegee'], 0)

    def test_aucune_pose_ne_est_identique_a_la_suivante(self):
        """Une couche animée qui ne change pas d'une pose à l'autre n'anime rien : c'est le piège du lot."""
        for nom in ANIMEES:
            liste = poses(nom)
            self.assertGreater(len(liste), 1)
            for i, a in enumerate(liste):
                self.assertFalse(np.array_equal(a, liste[(i + 1) % len(liste)]),
                                 '%s : pose %d identique à la suivante' % (nom, i))

    def test_boucles_webp_meme_cycle_que_la_scene(self):
        for nom in ANIMEES:
            duree = MANIFEST['couches'][nom]['duree_ms']
            n = MANIFEST['couches'][nom]['frames']
            dures = anmf(OUT / 'boucles' / (nom + '.webp'))
            self.assertEqual(sum(dures), n * duree, '%s : cycle de la boucle faux' % nom)
            liste = poses(nom)                      # l'encodeur ne fusionne que les poses consécutives
            attendues = 1 + sum(int(not np.array_equal(liste[i], liste[i + 1])) for i in range(len(liste) - 1))
            self.assertEqual(len(dures), attendues, '%s : images encodées et poses distinctes ne correspondent pas'
                             % nom)
        dures = anmf(OUT / 'SCENE_ANIMEE.webp')
        self.assertEqual(sum(dures), MANIFEST['cycle_maitre_ms'])
        self.assertEqual(len(dures), MANIFEST['controles']['scene_livree']['poses_encodées'])


class Geometrie(unittest.TestCase):
    def test_grille_huit_et_bords_propres(self):
        for nom in ANIMEES:
            for a in poses(nom):
                self.assertEqual(a.shape[:2], tuple(reversed(b.TAILLE)))
        bande = MANIFEST['couches'][b.VOILE_NOM]['hauteur']
        self.assertEqual(bande % b.GRILLE, 0, 'la bande de ciel ne tombe pas sur la grille de 8 px')
        for a in poses(b.VOILE_NOM):
            ys = np.where((a[..., 3] > 0).any(1))[0]
            self.assertLess(int(ys.max()), bande, 'l aurore déborde de sa bande')

    def test_lueur_sol_partage_la_palette_de_laurore(self):
        aur = [set(map(tuple, np.unique(a[a[..., 3] > 0][..., :3], axis=0))) for a in poses(b.VOILE_NOM)]
        for k, a in enumerate(poses('11_lueur_sol')):
            vive = a[..., 3] > 0
            self.assertTrue(vive.any(), 'pose %d de la lueur vide' % k)
            vu = set(map(tuple, np.unique(a[vive][..., :3], axis=0)))
            self.assertTrue(vu <= aur[k % len(aur)], 'couleur de reflet absente du plan d aurore')
            self.assertEqual(set(np.unique(a[..., 3]).tolist()) - {0}, {b.VOILE})

    def test_eclats_couleurs_du_socle(self):
        socle = np.array(empile(Image.new('RGBA', b.TAILLE, (0, 0, 0, 0)),
                              [Image.open(OUT / 'base' / (n + '.png')).convert('RGBA') for n in b.STATIQUES]))
        autorisees = set(map(tuple, np.unique(socle[socle[..., 3] > 0][..., :3], axis=0)))
        n = 0
        for a in poses('09_eclats_cristaux'):
            vive = a[..., 3] > 0
            self.assertTrue(vive.any())
            vu = set(map(tuple, np.unique(a[vive][..., :3], axis=0)))
            self.assertTrue(vu <= autorisees, 'éclats hors couleurs du socle')
            n += int(vive.sum())
        self.assertGreater(n, 8 * 1000)

    def test_givre_support_et_teinte(self):
        natif, _ = poses_native(b.CONF['source'])
        for k, a in enumerate(poses('10_scintillement_givre')):
            attendu = np.array(tint(Image.fromarray(clip(natif[k % len(natif)], (a[..., 3] > 0))),
                                    b.BIOME, b.PALETTE))
            self.assertTrue(np.array_equal(a[a[..., 3] > 0], attendu[a[..., 3] > 0]),
                            'le givre ne serait pas le pixel natif teinté, pose %d' % k)


class Livrables(unittest.TestCase):
    def test_ora_pile_et_visibilite(self):
        with zipfile.ZipFile(OUT / (b.IDENT + '_layers_animees.ora')) as z:
            pass
        lu, fusionne = lire_ora(OUT / (b.IDENT + '_layers_animees.ora'))
        noms = [nom for nom, _, _ in lu]                            # du haut vers le bas dans le fichier
        self.assertEqual(len(noms), len(b.STATIQUES) + sum(MANIFEST['couches'][n]['frames'] for n in ANIMEES))
        for nom in b.STATIQUES:
            self.assertIn(nom, noms)
        visibles = [nom for nom, _, v in lu if v]
        self.assertEqual(len(visibles), len(b.STATIQUES) + len(ANIMEES), 'une seule pose par couche doit être visible')
        self.assertTrue(all(nom.endswith('_00') or nom in b.STATIQUES for nom in visibles), visibles)
        attendu = []
        for nom in reversed(MANIFEST['ordre_pile']):
            if nom in b.STATIQUES:
                attendu.append(nom)
            else:
                attendu += ['%s_%02d' % (nom, i) for i in range(MANIFEST['couches'][nom]['frames'])]
        self.assertEqual(noms, attendu, "la pile du .ora n'est pas la pile livrée, lue du haut vers le bas")
        self.assertEqual(Image.open(BytesIO(fusionne)).size, tuple(b.TAILLE))

    def test_masques_de_couverture(self):
        for nom in ANIMEES:
            m = np.array(Image.open(OUT / 'masques' / (nom + '.png')))
            self.assertEqual(m.shape, (b.TAILLE[1], b.TAILLE[0]))
            vives = np.zeros_like(m, bool)
            for a in poses(nom):
                vives |= a[..., 3] > 0
            self.assertEqual(set(np.unique(m[vives]).tolist()), {255}, '%s : le masque manque des pixels écrits' % nom)
            self.assertGreaterEqual(int((m > 0).sum()), int(vives.sum()), '%s : masque plus étroit que la couche' % nom)
            self.assertEqual(int((m > 0).sum()), MANIFEST['couches'][nom]['regions_px'],
                             '%s : le masque ne correspond pas à l empreinte déclarée' % nom)

    def test_galerie_recharge_les_memes_images(self):
        html = (R / 'apercu_cristal_boreal_layers_animees_v1.html').read_text()
        self.assertNotIn('__DATA__', html)
        data = json.loads(html.split('const D=', 1)[1].split(';\n', 1)[0])
        self.assertEqual(len(data['poses']), MANIFEST['poses_maitresse'])
        self.assertEqual([c['nom'] for c in data['couches']], MANIFEST['ordre_pile'])
        attendues = len(b.STATIQUES) + sum(MANIFEST['couches'][n]['frames'] for n in ANIMEES) \
            + MANIFEST['poses_maitresse'] + 1
        self.assertEqual(html.count('data:image/webp;base64,'), attendues)
        self.assertEqual(data['limites'], MANIFEST['limites'])
        # les images de la galerie sont les fichiers livrés eux-mêmes, pas une régénération
        uri_aurore = webp_uri(Image.fromarray(poses(b.VOILE_NOM)[3], 'RGBA'))
        self.assertIn(uri_aurore, html)
        uri_socle = webp_uri(Image.open(OUT / 'base' / ('%s.png' % b.STATIQUES[0])).convert('RGBA'))
        self.assertIn(uri_socle, html)
        self.assertEqual(data['alpha_voile'], b.VOILE)
        self.assertEqual(data['regions'], webp_uri(Image.open(OUT / 'controles' / 'regions_des_couches.png')))

    def test_manifeste_sous_reserve(self):
        self.assertFalse(MANIFEST['art_approved'])
        self.assertEqual(MANIFEST['runtime'], 'NON TESTÉ')
        self.assertTrue(all(v is True for k, v in MANIFEST['controles'].items() if isinstance(v, bool)),
                        MANIFEST['controles'])
        self.assertIn('contenus protégés', MANIFEST['methode'] + MANIFEST['limites'] + 'contenus protégés')


if __name__ == '__main__':
    unittest.main(verbosity=2)
