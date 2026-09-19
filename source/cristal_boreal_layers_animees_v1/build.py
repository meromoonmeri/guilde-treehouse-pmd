#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quatre couches animées indépendantes pour la zone « Cristal · boréal » (layouts magenta V1).

La zone V1 ne livrait qu'une seule couche animée : la séquence native de l'eau, douze poses
protégées. Ce lot en ajoute quatre autres, chacune sur son propre plan, avec sa propre cadence,
sans retoucher les cinq calques statiques ni la séquence protégée :

  08_aurore_ciel     l'onde boréale indexée du lot V12, posée dans le ciel, palette cycling pur
  09_eclats_cristaux scintillement des facettes, rotation des classes de luminance du calque source
  10_scintillement_givre les points vifs des poses natives, allumés en diagonale, hors zone protégée
  11_lueur_sol       la lueur de l'aurore qui court sur le sol visible, en phase avec elle

La scène maîtresse boucle sur 1 920 ms en 48 poses de 40 ms : toutes les cadences des couches tombent
sur cette grille, donc rien n'est rééchantillonné. Contrôle central du lot : la pile SANS VOILE — la
séquence protégée, les cinq calques et les trois couches qui n'écrivent que hors zone protégée — est
posée à posée exactement égale à la frame native correspondante. L'aurore est le seul calque qui porte
sur le ciel protégé, et seulement comme voile à opacité plafonnée : elle est un calque à part, retiré
dans la pile livrée COMPOSITION_SANS_VOILE.png, et les douze poses natives restent des fichiers
recopiés octet pour octet.
"""
from pathlib import Path
import json
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
from PIL import Image, ImageDraw

from source.cristal_boreal_layers_animees_v1.lot import (GRILLE, OUT, R, SRC, V12, ZD, MD, VOILE, boucle,
                                                         charger, classes_eclat, clip, empile, key, lire_ora,
                                                         masque, ora, palette_replay, png_bytes, poses_native,
                                                         redimensionner_indexes, sha, tint, webp_uri)

CONF = [c for c in json.loads((SRC / 'references/config.json').read_text()) if c['id'] == 'cristal'][0]
IDENT = 'cristal_boreal'          # nom de la scène du lot V1 : biome + palette
TAILLE = tuple(CONF['size'])
H, W = TAILLE[1], TAILLE[0]
BIOME, PALETTE = 'cristal', 0          # palette index 0 = boréal, la de la zone
PRESERVE = np.array(charger(SRC / 'references/cristal_preserve.png', 'L')) > 0
TERRAIN = np.array(charger(MD / 'terrain_detoure.png'))[..., 3] > 0
SOL = np.array(charger(MD / 'sol_visible.png', 'L')) > 0
CRISTAUX = np.logical_or.reduce([np.array(charger(MD / f, 'L')) > 0 for f in
                                 ('04_cristaux_gauche.png', '05_cristaux_droit.png')])
STATIQUES = ['02_sol_reconstitue', '03_ombres_contact', '04_cristaux_gauche', '05_cristaux_droit',
             '07_raccord_reference']
NATIF_DUREE = 160
PAS_MAITRE = 40
CYCLE = 1920
# du bas vers le haut : l'eau protégée, les cinq calques, ce qui n'écrit que hors zone protégée, puis le voile
VOILE_NOM = '08_aurore_ciel'
ORDRE_PILE = (['01_animation_eau_protegee'] + STATIQUES +
              ['09_eclats_cristaux', '10_scintillement_givre', '11_lueur_sol', VOILE_NOM])


def frames_aurore():
    """L'onde V12 redimensionnée au plus proche voisin, puis rejouée par rotation de palette."""
    indexee = Image.open(V12 / 'onde_indexee.png')
    alpha = Image.open(V12 / 'onde_alpha.png')
    palettes = json.loads((V12 / 'palettes_8frames.json').read_text())['frames']
    h2 = max(GRILLE, int(round(indexee.height * TAILLE[0] / indexee.width / GRILLE)) * GRILLE)
    idx, a = redimensionner_indexes(indexee, alpha, (TAILLE[0], h2))
    ciel = np.zeros((H, W), bool)
    ciel[:h2, :] = ~TERRAIN[:h2, :]
    garde = ciel[:h2]
    vives, plans_h2 = [], []
    for k, pal in enumerate(palettes):
        plan = palette_replay(Image.fromarray(idx), Image.fromarray(a), pal)
        plans_h2.append(plan)
        out = np.zeros((H, W, 4), 'uint8')
        out[:h2][garde] = plan[garde]
        out[..., 3] = np.minimum(out[..., 3], VOILE)            # voile déclaré : jamais opaque
        out[out[..., 3] == 0] = 0
        vives.append(out)
    return vives, ciel, plans_h2, dict(source='renders/boreales_palette_cycling_v12/onde_indexee.png',
                            source_sha256=sha(V12 / 'onde_indexee.png'),
                            palette_sha256=sha(V12 / 'palettes_8frames.json'),
                            silhouette='figée, seule la palette tourne', hauteur=h2,
                            alpha_max=VOILE,
                            empreinte='bande de ciel au-dessus du terrain, lignes 0 à %d' % (h2 - 1),
                            regles='indices et alpha redimensionnés en NEAREST, aucun mélange, aucune couleur '
                                   'ajoutée ; le plan est posé en voile à %d/255 sur le ciel, il ne remplace '
                                   'aucun pixel, il les éclaire et reste retirable' % VOILE)


def frames_eclats(socle):
    """Rotation des classes de luminance du relief des cristaux : à chaque pose, une classe s\'allume.

    Le champ d\'éclats est le tracé que le lot V1 a lui-même reconstitué autour et sur les cristaux :
    les deux calques de cristaux et leur raccord de référence, moins ce qui reste protégé. Une classe
    allumée reçoit la couleur du cran au-dessus, prise dans le socle livré lui-même : aucune couleur
    nouvelle, aucun fondu, et le reste du dessin reste intact en dessous.
    """
    m = [np.array(charger(MD / f, 'L')) > 0 for f in ('04_cristaux_gauche.png', '05_cristaux_droit.png')]
    m.append(np.array(charger(ZD / ('%s_07_raccord_reference.png' % IDENT)))[..., 3] > 0)
    region = np.logical_or.reduce(m) & ~PRESERVE
    op = region & (socle[..., 3] > 0)
    carte, couleurs = classes_eclat(socle[..., :3], op, nb=4)
    n = len(couleurs)
    vives = []
    for k in range(n * 2):
        allumee, suivante = k % n, (k % n + 1) % n
        vives.append(np.where((op & (carte == allumee))[..., None],
                              np.concatenate([couleurs[suivante], [255]]), np.zeros(4, 'uint8')).astype('uint8'))
    return vives, op, dict(sources=['04_cristaux_gauche', '05_cristaux_droit', '07_raccord_reference'],
                           sha256=[sha(ZD / ('%s_%s.png' % (IDENT, nom))) for nom in
                                   ('04_cristaux_gauche', '05_cristaux_droit', '07_raccord_reference')],
                           nb_classes=n, regles="les seules couleurs posées sont les couleurs les plus fréquentes "
                                                "d'une classe de luminance du socle livré, jamais une moyenne")


def frames_givre(natif):
    """Les points vifs des poses natives, hors zone protégée, sélectionnés par un balayage diagonal.

    Le natif ne fait bouger que l'eau : hors zone protégée, ses douze poses sont identiques, et une
    simple recopie pose par pose serait une animation vide. Ce qui tourne ici est donc la sélection :
    des diagonales de GRILLE px, posées sur autant de positions que de poses. La couleur de chaque
    pixel allumé est celle de la pose native de même rang, teinte comme le reste de la zone. Aucun
    pixel n'est déplacé, aucune couleur n'est ajoutée.
    """
    lum = lambda a: 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    vives, champ = [], np.zeros((H, W), bool)
    for frame in natif:
        champ |= (lum(frame) > 200) & (frame[..., 3] > 0) & ~PRESERVE
    ys, xs = np.where(champ)
    rangee = np.zeros((H, W), 'int16')
    rangee[champ] = (ys // GRILLE + xs // GRILLE) % len(natif)
    n = len(natif)
    for k in range(n):
        vive = champ & ((rangee == k) | (rangee == (k + 1) % n))
        out = np.array(tint(Image.fromarray(clip(natif[k], vive)), BIOME, PALETTE))
        vives.append(out)
    return vives, champ, dict(source=CONF['source'], source_sha256=sha(R / CONF['source']),
                              diagonales=n, bandes_par_pose=2,
                              regles='pixels vifs (luminance > 200) des poses natives elles-mêmes, hors zone '
                                     'protégée, sélection tournante sur %d diagonales de %d px dont deux allumées '
                                     'par pose, teintes tint(cristal, boréal) du lot V1' % (n, GRILLE))


def frames_lueur(plans_h2):
    """La lueur de l'aurore, décalée rangée par rangée, posée en voile déclaré sur le sol visible.

    Le plan est échantillonné sur toute la hauteur du ruban, repli périodique : les couleurs restent
    celles de l'aurore, seul l'emplacement change, et le sol n'est pas repeint (voile, pas aplat).
    """
    couleur = np.stack([im[..., :3] for im in plans_h2])
    alpha = np.stack([im[..., 3] for im in plans_h2])
    hauteur = couleur.shape[1]
    ys, xs = np.where(SOL & ~PRESERVE)
    vives = []
    for k in range(len(plans_h2)):
        out = np.zeros((H, W, 4), 'uint8')
        sy = (ys + 6 * k) % hauteur
        pris = alpha[k][sy, xs] > 0
        if pris.any():
            out[ys[pris], xs[pris]] = np.concatenate([couleur[k][sy[pris], xs[pris]],
                                                      np.full((int(pris.sum()), 1), VOILE, 'uint8')], axis=1)
        vives.append(out)
    return vives, SOL & ~PRESERVE, dict(source='plans intermédiaires de 08_aurore_ciel (ruban V12 rejoué)',
                                        regles='échantillonnage du même plan indexé, décalage vertical de 6 px par '
                                               'pose avec repli périodique, opacité de voile %d, posé seulement sur '
                                               'le sol visible hors zone protégée' % VOILE)


def construire():
    SOUS_DOSSIERS = ('calques', 'boucles', 'masques', 'base', 'controles')
    for d in SOUS_DOSSIERS:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    if (OUT / 'calques').exists():
        for d in SOUS_DOSSIERS:                       # pas d'images orphelines d'un build antérieur
            shutil.rmtree(OUT / d)
        for d in SOUS_DOSSIERS:
            (OUT / d).mkdir(parents=True, exist_ok=True)

    natif, dures = poses_native(CONF['source'])
    empreintes_base = {}
    for nom in STATIQUES:
        shutil.copy2(ZD / ('%s_%s.png' % (IDENT, nom)), OUT / 'base' / ('%s.png' % nom))
        empreintes_base[nom] = sha(OUT / 'base' / (nom + '.png'))
    base_pile = [charger(OUT / 'base' / (nom + '.png')) for nom in STATIQUES]

    socle = np.array(empile(Image.new('RGBA', TAILLE, (0, 0, 0, 0)), base_pile))
    aur, region_aur, aur_h2, prov_aur = frames_aurore()
    ecl, region_ecl, prov_ecl = frames_eclats(socle)
    giv, region_giv, prov_giv = frames_givre(natif)
    lud, region_lud, prov_lud = frames_lueur(aur_h2)

    poses_livrees = []
    for i in range(CONF['frames']):
        src = ZD / ('%s_01_animation_%03d.png' % (IDENT, i))
        (OUT / 'calques' / '01_animation_eau_protegee').mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, OUT / 'calques' / '01_animation_eau_protegee' / ('frame_%02d.png' % i))
        poses_livrees.append(np.array(charger(src)))
    animees = {
        '01_animation_eau_protegee': ([np.array(charger(ZD / ('%s_01_animation_%03d.png' % (IDENT, i))))
                                       for i in range(CONF['frames'])],
                                      PRESERVE,
                                      dict(source='renders/layouts_magenta_v1/zones/cristal_boreal',
                                           regles='les douze poses livrées par le lot V1, recopiées fichier par '
                                                  'fichier, octet pour octet, sans retouche ni re-encodage',
                                           copie_identique=True), NATIF_DUREE),
        '08_aurore_ciel': (aur, region_aur, prov_aur, 120),
        '09_eclats_cristaux': (ecl, region_ecl, prov_ecl, 240),
        '10_scintillement_givre': (giv, region_giv, prov_giv, NATIF_DUREE),
        '11_lueur_sol': (lud, region_lud, prov_lud, 240),
    }

    empreintes = {}
    for nom, (plans, region, prov, duree) in animees.items():
        dossier = OUT / 'calques' / nom
        dossier.mkdir(parents=True, exist_ok=True)
        for i, arr in enumerate(plans):
            if not (nom == '01_animation_eau_protegee' and (dossier / ('frame_%02d.png' % i)).exists()):
                Image.fromarray(np.asarray(arr), 'RGBA').save(dossier / ('frame_%02d.png' % i))
            empreintes['%s/frame_%02d.png' % (nom, i)] = sha(dossier / ('frame_%02d.png' % i))
        boucle([Image.fromarray(np.asarray(a), 'RGBA') for a in plans], OUT / 'boucles' / (nom + '.webp'), duree)
        Image.fromarray(masque(region), 'L').save(OUT / 'masques' / (nom + '.png'))
        prov.setdefault('regles', '')
        prov.setdefault('source', '')
        prov.update(dict(frames=len(plans), duree_ms=duree, cycle_ms=len(plans) * duree,
                         pixels_actifs=int(region.sum()), pixels_hors_zone_protegee=int((region & ~PRESERVE).sum()),
                         ecrites_sur_zone_protegee=int(sum(int((np.asarray(a)[..., 3] > 0)[PRESERVE].sum())
                                                           for a in plans)),
                         alpha_tries=sorted(set(np.unique(np.stack(plans)[..., 3]).tolist()))))
        if nom == '01_animation_eau_protegee':
            prov['copie_identique'] = all(sha(OUT / 'calques' / nom / ('frame_%02d.png' % i)) ==
                                          sha(ZD / ('%s_01_animation_%03d.png' % (IDENT, i)))
                                          for i in range(CONF['frames']))

    # Scène maîtresse : 48 poses de 40 ms, chaque couche avancée à son propre rythme.
    k_voile = ORDRE_PILE.index(VOILE_NOM)
    maitresse, sans_voile = [], []
    for m in range(CYCLE // PAS_MAITRE):
        t = m * PAS_MAITRE
        couches = []
        for nom in ORDRE_PILE:
            if nom in STATIQUES:
                couches.append(base_pile[STATIQUES.index(nom)])
            else:
                plans, _, _, duree = animees[nom]
                couches.append(Image.fromarray(np.asarray(plans[(t // duree) % len(plans)]), 'RGBA'))
        maitresse.append(empile(Image.new('RGBA', TAILLE, (0, 0, 0, 0)), couches))
        sans_voile.append(empile(Image.new('RGBA', TAILLE, (0, 0, 0, 0)), couches[:k_voile]))
    boucle(maitresse, OUT / 'SCENE_ANIMEE.webp', PAS_MAITRE)
    boucle(sans_voile, OUT / 'SCENE_SANS_VOILE.webp', PAS_MAITRE)
    maitresse[0].save(OUT / 'COMPOSITION.png')
    sans_voile[0].save(OUT / 'COMPOSITION_SANS_VOILE.png')

    # Le .ora : la pile livrée elle-même, du bas vers le haut. Toutes les poses de chaque couche animée
    # restent dans le fichier, la pose 0 seule visible ; le groupe se lit donc 00 en haut, à l'endroit.
    couches_ora = []
    for nom in ORDRE_PILE:
        if nom in STATIQUES:
            couches_ora.append((nom, charger(OUT / 'base' / (nom + '.png')), True))
            continue
        plans = animees[nom][0]
        for i in range(len(plans) - 1, -1, -1):
            couches_ora.append(('%s_%02d' % (nom, i), Image.fromarray(np.asarray(plans[i]), 'RGBA'), i == 0))
    octets_ora = ora(OUT / ('%s_layers_animees.ora' % IDENT), couches_ora, maitresse[0])

    # autocontrôles : ce que le lot garantit, posée par posée, et écrit au manifeste
    ciel = np.asarray(animees[VOILE_NOM][1])
    garanties = {}
    identique = []
    for m in range(len(maitresse)):
        t = m * PAS_MAITRE
        attendu = np.array(tint(Image.fromarray(natif[(t // NATIF_DUREE) % 12]), BIOME, PALETTE))
        nu = np.array(sans_voile[m])
        avec = np.array(maitresse[m])
        identique.append(bool(np.array_equal(nu[PRESERVE], attendu[PRESERVE])))
        identique.append(bool(np.array_equal(avec[~ciel], nu[~ciel])))
    garanties['zone_protegee_identique_a_la_pose_native'] = all(identique[0::2])
    garanties['le_voile_ne_touche_que_le_ciel'] = all(identique[1::2])
    garanties['poses_de_la_sequence_native_recopyees_octet_pour_octet'] = all(
        sha(OUT / 'calques' / '01_animation_eau_protegee' / ('frame_%02d.png' % i)) ==
        sha(ZD / ('%s_01_animation_%03d.png' % (IDENT, i))) for i in range(CONF['frames']))
    hors, hors_nom = [], []
    for nom in ORDRE_PILE:
        if nom in STATIQUES or nom == VOILE_NOM or nom == '01_animation_eau_protegee':
            continue                                        # 01 EST la zone protégée, il n'y a rien à vérifier
        hors_nom.append(nom)
        plans = animees[nom][0]
        hors.append(int(sum(int((np.asarray(a)[..., 3] > 0)[PRESERVE].sum()) for a in plans)))
    garanties['couches_ajoutees_n_ecrivent_pas_sur_la_zone_protegee'] = dict(zip(hors_nom, hors))
    alpha_voile = int(max(int(np.unique(np.asarray(a)[..., 3]).max()) for a in animees[VOILE_NOM][0]))
    garanties['alpha_max_du_voile'] = alpha_voile
    webp_lu = Image.open(OUT / 'SCENE_ANIMEE.webp')
    garanties['scene_livree'] = dict(poses_encodées=webp_lu.n_frames,
                                      regle="l'encodeur WebP fusionne les poses consécutives identiques en "
                                            "additionnant leurs durées ; les %d poses de la scène en donnent %d "
                                            "encodées, le cycle de %d ms et chaque durée sont conservés"
                                            % (len(maitresse), webp_lu.n_frames, CYCLE))
    if not all(v for v in [garanties['zone_protegee_identique_a_la_pose_native'],
                          garanties['le_voile_ne_touche_que_le_ciel'],
                          garanties['poses_de_la_sequence_native_recopyees_octet_pour_octet'],
                          all(x == 0 for x in garanties['couches_ajoutees_n_ecrivent_pas_sur_la_zone_protegee'].values()),
                          alpha_voile <= VOILE]):
        raise SystemExit('contrôle du lot : %s' % json.dumps(garanties, ensure_ascii=False))

    # Planche de contrôle : une ligne par couche animée, une colonne par pose.
    poses_max = max(len(a[0]) for a in animees.values())
    case = (W // 4 + 1, H // 4 + 1)
    pas = 2
    planche = Image.new('RGB', (110 + (poses_max // pas + 1) * (case[0] + 3), (case[1] + 16) * len(animees) + 8),
                        (10, 12, 18))
    d = ImageDraw.Draw(planche)
    for r, (nom, (plans, _, _, duree)) in enumerate(sorted(animees.items())):
        y = 4 + r * (case[1] + 16)
        d.text((6, y + 2), '%s · %d poses · %d ms' % (nom, len(plans), duree), fill=(225, 230, 240))
        for i in range(0, len(plans), pas):
            tuile = Image.new('RGBA', TAILLE, (18, 22, 30, 255))
            tuile.alpha_composite(Image.fromarray(np.asarray(plans[i]), 'RGBA'))
            x = 110 + (i // pas) * (case[0] + 3)
            planche.paste(tuile.convert('RGB').resize(case, Image.NEAREST), (x, y + 14))
    planche.save(OUT / 'PLANCHE_COUCHEES_ANIMEES.png')

    manifest = dict(
        zone=IDENT, biome=CONF['id'], titre='Cristal · boréal — couches animées multiples', taille=list(TAILLE),
        grille=GRILLE, base='renders/layouts_magenta_v1/zones/cristal_boreal (cinq calques statiques recopiés à l\'identique)',
        methode='aucun pinceau : recopie exacte, rotation d\'indices de palette, échantillonnage décalé, voile déclaré',
        cycle_maitre_ms=CYCLE, pas_maitre_ms=PAS_MAITRE, poses_maitresse=len(maitresse),
        zone_protegee=dict(pixels=int(PRESERVE.sum()), frames_natives=CONF['frames'], duree_ms=NATIF_DUREE,
                          garantie='à chaque pose de la scène maîtresse, la pile sans voile est égale à la frame '
                                   'native correspondante sur toute la zone protégée, et les douze poses livrées '
                                   'du lot V1 sont recopiées fichier par fichier'),
        voile=dict(calque=VOILE_NOM, alpha_max=VOILE, empreinte='ciel au-dessus du terrain',
                   retirable='COMPOSITION_SANS_VOILE.png et SCENE_SANS_VOILE.webp sont la même scène sans lui'),
        couches={nom: dict(regions_px=int(np.asarray(animees[nom][1]).sum()), **animees[nom][2])
                 for nom in sorted(animees)},
        controle_des_regions='controles/regions_des_couches.png : une nuance par couche animée, le bleu sombre est '
                             'la zone protégée que rien n\'écrase',
        limites='Les cinq calques statiques et les douze poses natives de la zone V1 sont recopiés à l\'identique, '
                'fichier par fichier. L\'aurore vient de l\'image indexée du lot V12, redimensionnée au plus proche '
                'voisin et rejouée par rotation de palette seule, posée en voile à %d/255 sur le ciel : c\'est le '
                'seul calque qui porte sur la zone protégée, il est retirable (SCENE_SANS_VOILE.webp, '
                'COMPOSITION_SANS_VOILE.png). Les éclats, le givre et la lueur ne posent que des pixels déjà '
                'présents dans leurs sources et jamais sur la zone protégée. Les boucles WebP fusionnent les poses '
                'consécutives identiques en additionnant leurs durées : le décodage renvoie donc moins d\'images '
                'que de poses, pour le même cycle. Aucun pinceau, aucune couleur inventée, aucune collision, aucun '
                'warp, aucun rendu validé dans PMD Online ; art non approuvé.' % VOILE,
        ora=dict(fichier='%s_layers_animees.ora' % IDENT, calques=len(couches_ora), octets=len(octets_ora),
                 visibles=sum(1 for c in couches_ora if c[2]),
                 fusion='l\'image aplatie du fichier est la pose 0 de la scène avec voile'),
        controles=garanties, ordre_pile=ORDRE_PILE,
        base_sha256=empreintes_base, fichiers_sha256=empreintes,
        art_approved=False, runtime='NON TESTÉ',
    )
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')

    # contrôles visuels : la région que chaque couche animée a le droit de couvrir
    regions = np.zeros((H, W, 3), 'uint8')
    nuance = {'01_animation_eau_protegee': (80, 140, 220), '08_aurore_ciel': (90, 220, 200),
              '09_eclats_cristaux': (220, 200, 120), '10_scintillement_givre': (235, 235, 245),
              '11_lueur_sol': (120, 200, 130)}
    for nom, (_, region, _, _) in animees.items():
        regions[np.asarray(region)] = nuance[nom]
    regions[PRESERVE & ~np.any([np.asarray(a[1]) for a in animees.values()], axis=0)] = (40, 60, 100)
    Image.fromarray(regions, 'RGB').save(OUT / 'controles' / 'regions_des_couches.png')

    galerie(manifest, animees, maitresse)
    return manifest


def galerie(manifest, animees, maitresse):
    """Une page autonome, injectée des images livrées elles-mêmes : rien n\'est regénéré pour l\'aperçu."""
    couches = []
    for nom in manifest['ordre_pile']:
        if nom in STATIQUES:
            couches.append(dict(nom=nom, role='statique', regle='recopié du lot V1 sans retouche',
                               image=webp_uri(charger(OUT / 'base' / (nom + '.png')))))
            continue
        plans, region, prov, duree = animees[nom]
        couches.append(dict(nom=nom, role='animée', duree_ms=duree, frames=len(plans),
                            pixels=int(np.asarray(region).sum()), regle=prov['regles'],
                            poses=[webp_uri(Image.fromarray(np.asarray(a), 'RGBA')) for a in plans]))
    data = dict(titre=manifest['titre'], taille=manifest['taille'], base=manifest['base'], couches=couches,
                grille=manifest['grille'], ordre=manifest['ordre_pile'],
                voile=manifest['voile']['calque'], alpha_voile=manifest['voile']['alpha_max'],
                regions=webp_uri(Image.open(OUT / 'controles' / 'regions_des_couches.png')),
                cycle_ms=manifest['cycle_maitre_ms'], pas_ms=manifest['pas_maitre_ms'],
                poses=[webp_uri(im) for im in maitresse], protegee=int(manifest['zone_protegee']['pixels']),
                controles={k: v for k, v in manifest['controles'].items()},
                limites=manifest['limites'])
    html = (Path(__file__).parent / 'viewer.html').read_text().replace('__DATA__', json.dumps(data))
    (R / 'apercu_cristal_boreal_layers_animees_v1.html').write_text(html)
    return len(html)


if __name__ == '__main__':
    m = construire()
    octets = (R / 'apercu_cristal_boreal_layers_animees_v1.html').stat().st_size
    print('couches animées :', ', '.join('%s (%d poses %d ms)' % (k, v['frames'], v['duree_ms'])
                                          for k, v in sorted(m['couches'].items())))
    print('scène maîtresse : %d poses de %d ms, cycle %d ms ; galerie %.1f Mo'
          % (m['poses_maitresse'], m['pas_maitre_ms'], m['cycle_maitre_ms'], octets / 1e6))
    print('contrôles :', json.dumps(m['controles'], ensure_ascii=False))
