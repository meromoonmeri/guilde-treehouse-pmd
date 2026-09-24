"""Jardin secret v2 — export : calques jour/nuit, fleurs animées (calques propres), aperçus, ORA, manifeste, vérifications."""
import hashlib, io, json, os, sys, zipfile
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'cote_v4_abyss'))
import compose_v2 as C
from night import night

W, H = C.W, C.H
P = 'JSEC2_'
OUT = '../../renders/jardin_secret_v2'
for d in ['calques', 'nuit', 'fleurs_anim', 'fleurs_anim/nuit', 'sprites']:
    os.makedirs(f'{OUT}/{d}', exist_ok=True)

DESC = {
    '01_sol': 'Sol : sous-bois, lisière festonnée, pelouse, haies, chemin de tapis droit (généré, opaque)',
    '02_fleurs': 'Fleurs animées 24×24 : 3 horloges × 3 poses (fichiers fleurs_anim/)',
    '03_rochers': 'Rochers (générés, sous le joueur)',
    '04_souche_temple': 'Souche-sanctuaire + hokora miniature de Celebi (généré, sous le joueur)',
    '05_arbres_troncs': 'Arbres : troncs + ombres au sol (sous le joueur)',
    '06_arbres_cimes': 'Arbres : cimes, dont cimes seules de lisière façon Halcyon (au-dessus du joueur)',
    '07_rayon': 'Rayon de lumière : sprite natif de secretgarden.png (au-dessus du joueur)',
    '08_feuillage_avant': 'Feuillage immersif d\'avant-plan (généré, recoupé et festonné aux outils)',
}


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def over(dst, src):
    m = src[..., 3] > 0
    dst[m] = src[m]


def save_ora(path, layers, comp):
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
        st = [f'<image w="{W}" h="{H}"><stack>']
        for k in reversed(list(layers)):
            st.append(f'<layer name="{P}{k}" src="data/{k}.png" x="0" y="0" visibility="visible"/>')
        st.append('</stack></image>')
        z.writestr('stack.xml', '\n'.join(st))
        for k, a in layers.items():
            b = io.BytesIO(); Image.fromarray(a).save(b, 'PNG'); z.writestr(f'data/{k}.png', b.getvalue())
        b = io.BytesIO(); Image.fromarray(comp).save(b, 'PNG'); z.writestr('mergedimage.png', b.getvalue())
        t = Image.fromarray(comp); t.thumbnail((256, 256))
        b = io.BytesIO(); t.save(b, 'PNG'); z.writestr('Thumbnails/thumbnail.png', b.getvalue())


def main():
    sol, L, flowers, placements, warn, (lawn, carpet, void) = C.compose()
    fol = C.foliage()
    fl = C.flower_layers(flowers)
    layers = {'01_sol': np.dstack([sol, np.full((H, W), 255, np.uint8)])}
    layers.update({k: L[k] for k in ['03_rochers', '04_souche_temple', '05_arbres_troncs', '06_arbres_cimes', '07_rayon']})
    layers['08_feuillage_avant'] = fol
    order = ['01_sol', '02_fleurs', '03_rochers', '04_souche_temple', '05_arbres_troncs', '06_arbres_cimes', '07_rayon', '08_feuillage_avant']

    def composite(mode, pose_of_clock, with_fol=True):
        g = (lambda a: np.array(night(Image.fromarray(a)))) if mode == 'nuit' else (lambda a: a)
        comp = g(layers['01_sol']).copy()
        for c in C.CLOCKS:
            over(comp, g(fl[(c, pose_of_clock[c])]))
        for k in order[2:]:
            if k == '08_feuillage_avant' and not with_fol:
                continue
            over(comp, g(layers[k]))
        return comp

    files = {}
    for mode, sub in [('jour', 'calques'), ('nuit', 'nuit')]:
        for k, a in layers.items():
            arr = a if mode == 'jour' else np.array(night(Image.fromarray(a)))
            fn = f'{OUT}/{sub}/{P}{k}{"_nuit" if mode == "nuit" else ""}.png'
            Image.fromarray(arr).save(fn); files[fn] = sha(fn)
        for (c, p), a in fl.items():
            arr = a if mode == 'jour' else np.array(night(Image.fromarray(a)))
            fn = f'{OUT}/fleurs_anim/{"nuit/" if mode == "nuit" else ""}{P}02_fleurs_c{c:02d}_p{p}{"_nuit" if mode == "nuit" else ""}.png'
            Image.fromarray(arr).save(fn); files[fn] = sha(fn)
        rest = {c: 0 for c in C.CLOCKS}
        comp = composite(mode, rest)
        Image.fromarray(comp).save(f'{OUT}/{P}composition_{mode}.png')
        if mode == 'jour':
            Image.fromarray(composite(mode, rest, False)).save(f'{OUT}/{P}composition_sans_feuillage.png')
        # ORA : un calque par pose d'horloge (pose 0 visible)
        ol = {}
        g = (lambda a: a) if mode == 'jour' else (lambda a: np.array(night(Image.fromarray(a))))
        ol['01_sol'] = g(layers['01_sol'])
        for c in C.CLOCKS:
            for p in range(3):
                ol[f'02_fleurs_c{c:02d}_p{p}'] = g(fl[(c, p)])
        for k in order[2:]:
            ol[k] = g(layers[k])
        save_ora(f'{OUT}/{P}{mode}.ora', ol, comp)

    # sprites de travail livrés (fleurs 24×24 × poses, temple, arbres)
    for f in os.listdir(C.SP):
        if f.endswith('.png') and (f.startswith('fleur_') or f.startswith('souche') or f.startswith('arbre_')):
            Image.open(f'{C.SP}/{f}').save(f'{OUT}/sprites/{P}{f}')

    # aperçu animé : clairière, cycle complet (PPCM 32/40/56 frames = 1120 frames de jeu à 60 i/s)
    box = (160, 60, 656, 440)
    events = sorted({t for c in C.CLOCKS for t in range(0, 1120, c)})
    frames, durs = [], []
    for i, t in enumerate(events):
        pose = {c: C.SEQ[(t // c) % 4] for c in C.CLOCKS}
        frames.append(Image.fromarray(composite('jour', pose)).crop(box))
        nxt = events[i + 1] if i + 1 < len(events) else 1120
        durs.append(round((nxt - t) * 1000 / 60))
    frames[0].save(f'{OUT}/{P}fleurs_animation_clairiere.webp', save_all=True, append_images=frames[1:], duration=durs, loop=0, lossless=True)
    # planche des poses ×6
    board = Image.new('RGBA', (3 * 24 * 6 + 40, 3 * 24 * 6 + 40), (111, 151, 71, 255))
    for r, c in enumerate(C.COULEURS):
        for p in range(3):
            s = Image.open(f'{C.SP}/fleur_{c}_pose{p}.png').resize((144, 144), Image.NEAREST)
            board.alpha_composite(s, (10 + p * 154, 10 + r * 154))
    board.save(f'{OUT}/{P}planche_fleurs_poses_x6.png')

    # ---------------- vérifications ----------------
    V = {}
    V['dimensions_grille_8px'] = W % 8 == 0 and H % 8 == 0
    allL = list(layers.values()) + list(fl.values())
    V['alpha_binaire'] = all(set(np.unique(a[..., 3])) <= {0, 255} for a in allL)
    V['sol_opaque'] = bool((layers['01_sol'][..., 3] == 255).all())
    def magenta(a):
        r, g, b = [a[..., i].astype(int) for i in range(3)]
        return int(((a[..., 3] > 0) & (r > 150) & (b > 150) & (g < 110)).sum())
    V['zero_pixel_magenta_residuel'] = sum(magenta(a) for a in allL) == 0
    # recomposition exacte depuis les PNG écrits
    rc = np.array(Image.open(f'{OUT}/calques/{P}01_sol.png').convert('RGBA'))
    for c in C.CLOCKS:
        over(rc, np.array(Image.open(f'{OUT}/fleurs_anim/{P}02_fleurs_c{c:02d}_p0.png').convert('RGBA')))
    for k in order[2:]:
        over(rc, np.array(Image.open(f'{OUT}/calques/{P}{k}.png').convert('RGBA')))
    V['recomposition_exacte'] = bool((rc == np.array(Image.open(f'{OUT}/{P}composition_jour.png').convert('RGBA'))).all())
    V['nuit_egale_filtre_abyss'] = all((np.array(Image.open(f'{OUT}/nuit/{P}{k}_nuit.png').convert('RGBA')) == np.array(night(Image.fromarray(a)))).all() for k, a in layers.items())
    names = [os.path.basename(f) for f in files]
    V['noms_uniques'] = len(names) == len(set(names))
    # fleurs : base de feuilles identique entre poses, touffes hors du chemin
    V['fleurs_base_fixe'] = all((np.array(Image.open(f'{C.SP}/fleur_{c}_pose{p}.png'))[14:] == np.array(Image.open(f'{C.SP}/fleur_{c}_pose0.png'))[14:]).all() for c in C.COULEURS for p in (1, 2))
    fl_any = np.zeros((H, W), bool)
    for a in fl.values():
        fl_any |= a[..., 3] > 0
    V['fleurs_hors_chemin'] = int((fl_any & carpet).sum()) == 0
    # parcours : chemin (tapis) continu du bord sud à la clairière, libre d'obstacles solides (gabarit 24 px)
    solid = (layers['03_rochers'][..., 3] > 0) | (layers['04_souche_temple'][..., 3] > 0) | (layers['05_arbres_troncs'][..., 3] > 0)
    walk = (lawn | carpet) & ~solid
    wk = ndi.binary_erosion(walk, structure=np.ones((24, 24)), border_value=1)
    lab, n = ndi.label(wk)
    south = set(np.unique(lab[H - 1][lab[H - 1] > 0]))
    tx, ty = C.TEMPLE_XY[0] + 50, C.TEMPLE_XY[1] + 101 + 16
    goal = set(np.unique(lab[ty - 8:ty + 8, tx - 20:tx + 20])) - {0}
    V['parcours_sud_vers_temple'] = bool(south & goal)
    V['largeur_chemin_px'] = int(carpet[H - 200].sum())
    V['avertissements_placement'] = warn
    V['all_pass'] = all(v for k, v in V.items() if isinstance(v, bool))
    json.dump(V, open(f'{OUT}/verification.json', 'w'), ensure_ascii=False, indent=1)

    man = {
        'lot': 'jardin_secret_v2', 'taille': [W, H], 'cellules_8px': [W // 8, H // 8], 'origine': [0, 0],
        'methode': 'générateur d\'images sur fond magenta #FF00FF, un calque/planche par appel, détourage, échelle canonique, palette, assemblage multicalque, corrections aux outils',
        'provenance': {
            'natif': ['07_rayon (secretgarden.png, translation seule)'],
            'genere': ['01_sol', '02_fleurs', '03_rochers', '04_souche_temple', '05_arbres_troncs', '06_arbres_cimes', '08_feuillage_avant'],
            'bruts': sorted(f for f in os.listdir('bruts') if f.endswith('.png')),
            'rejetes': sorted(os.listdir('bruts/rejetes')),
        },
        'echelles': {
            'arbres': 'largeur de cime 126 px = cime de l\'arbre Halcyon Vast Steppe 144×120 (native_tree_complete.png)',
            'fleurs': '24×24 = Vast_Steppe_Flower_Animations.png (Halcyon)',
            'souche': '100 px de large = souche de secretgarden.png',
        },
        'palette': 'sol, feuillage, arbres, rochers : ramenés aux 139 couleurs de secretgarden.png ; temple (28) et fleurs (20) : palette limitée propre (rouge/jaune absents de la référence)',
        'corrections_outils': [
            'sol : îlots clairs isolés dans le sous-bois effacés (couleur voisine)',
            'feuillage : recoupé sur le masque de la maquette +10 px, bord festonné (demi-disques 7-11 px), contour sombre 1 px + ombre intérieure',
            'fleurs : lignes 14-23 des poses 1 et 2 = pose 0 (base fixe, seuls tiges/pétales bougent)',
            'arbres : séparés troncs+ombre / cime',
        ],
        'animation_fleurs': {
            'fichiers': 'fleurs_anim/JSEC2_02_fleurs_cXX_pY.png (XX = horloge, Y = pose)',
            'sequence': C.SEQ, 'horloges_frames_jeu': C.CLOCKS,
            'pmdo': 'un calque animé par horloge, images p0,p1,p0,p2, durée XX frames de jeu par image',
            'touffes': [{'x': x, 'y': y, 'couleur': c, 'horloge': k} for x, y, c, k, _ in flowers],
        },
        'calques': [{'id': k, 'fichier': f'{P}{k}.png' if k != '02_fleurs' else 'fleurs_anim/', 'description': DESC[k]} for k in order],
        'placements': [{'sprite': n, 'xy': list(map(int, xy))} for n, xy in placements],
        'limites': ['pixels générés d\'après références (pas natifs certifiés), sauf le rayon', 'aucun test PMDO (moteur absent)', 'collisions/warps à dessiner dans l\'éditeur'],
        'fichiers_sha256': {os.path.relpath(k, OUT): v for k, v in files.items()},
    }
    json.dump(man, open(f'{OUT}/manifest.json', 'w'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in V.items()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
