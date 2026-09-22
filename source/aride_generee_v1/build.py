"""Assemblage map aride generee V1 depuis 5 bruts generateur (1224x864 -> 408x288).

Methode rendus generes: normalisation /3 NEAREST, detourage magenta par
inondation depuis les bords, calques separes, sol cache reconstitue,
FX poussiere animes (proposes, pas officiels).
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image
from scipy.ndimage import label, binary_fill_holes

R = Path(__file__).resolve().parents[2]
SRC = R / "source/aride_generee_v1/bruts"
OUT = R / "renders/aride_generee_v1"
OUT.mkdir(parents=True, exist_ok=True)

BRUTS = ["terrain_complet.png", "sol_seul.png", "parois_seules.png",
         "props_seuls.png", "fx_poussiere.png"]
DS = 3  # 1224x864 -> 408x288
MAGENTA = np.array([255, 0, 255], dtype=int)

# Placement des props (x, y du coin haut-gauche dans la scene 408x288).
# Ajuste apres inspection du corridor (bouche centree x~200).
PLACEMENTS = {
    "arbre0": (28, 168),
    "arbre1": (96, 148),
    "arbre2": (288, 150),
    "arbre3": (336, 172),
    "bloc0": (66, 196),
    "bloc1": (312, 198),
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_small(name):
    im = Image.open(SRC / name).convert("RGB")
    assert im.size == (1224, 864), im.size
    return np.array(im.resize((408, 288), Image.NEAREST)).astype(int)


def magenta_mask(a):
    return (np.abs(a - MAGENTA).sum(axis=2) < 90)


def flood_transparent(a):
    """Magenta inonde depuis les bords -> alpha 0. Trous magenta internes
    non relies aux bords = conserves opaques (pas de fill_holes aveugle)."""
    h, w, _ = a.shape
    mag = magenta_mask(a)
    seed = np.zeros((h, w), bool)
    seed[0, :] = seed[-1, :] = seed[:, 0] = seed[:, -1] = True
    seed &= mag
    # propagation iterative sur le 4-voisinage magenta
    prev = np.zeros((h, w), bool)
    cur = seed.copy()
    while not np.array_equal(cur, prev):
        prev = cur.copy()
        cur[1:, :] |= prev[:-1, :] & mag[1:, :]
        cur[:-1, :] |= prev[1:, :] & mag[:-1, :]
        cur[:, 1:] |= prev[:, :-1] & mag[:, 1:]
        cur[:, :-1] |= prev[:, 1:] & mag[:, :-1]
    rgba = np.dstack([a.astype(np.uint8), np.where(cur, 0, 255).astype(np.uint8)])
    return rgba, cur


def clean(rgba):
    """RGB à zéro sous alpha 0 (exports GIF/WebP propres, leçon V10)."""
    m = rgba[:, :, 3] == 0
    rgba[m] = (0, 0, 0, 0)
    return rgba


def despill(rgba):
    """Retire la frange rose d'AA : pixels rosés adjacent au transparent."""
    rgb = rgba[:, :, :3].astype(int)
    a = rgba[:, :, 3]
    pink = (rgb[:, :, 0] > 140) & (rgb[:, :, 2] > 140) & (rgb[:, :, 1] < 170)
    # 3 passes pour les franges epaisses
    for _ in range(3):
        tr = rgba[:, :, 3] == 0
        adj = np.zeros_like(tr)
        adj[1:, :] |= tr[:-1, :]
        adj[:-1, :] |= tr[1:, :]
        adj[:, 1:] |= tr[:, :-1]
        adj[:, :-1] |= tr[:, 1:]
        kill = pink & adj & (rgba[:, :, 3] > 0)
        if not kill.any():
            break
        rgba[kill] = (0, 0, 0, 0)
    return rgba


def main():
    manifest = {"bruts": {}, "scene": [408, 288], "downscale": "NEAREST /3"}
    for b in BRUTS:
        manifest["bruts"][b] = {"size": [1224, 864], "sha256": sha(SRC / b)}

    # ---- L00 sol : sable plein cadre (smear des bords magenta) ----
    sol = load_small("sol_seul.png")
    rgba_sol, _ = flood_transparent(sol)
    # retire d'abord les pixels roses d'AA au bord du sable, sinon le smear
    # les recopie sur tout le cadre
    rgba_sol = despill(rgba_sol)
    t_sol = rgba_sol[:, :, 3] == 0
    rgb = rgba_sol[:, :, :3].copy()
    # rebouche le cadre par dilatation du sable. Le vrai sable a G-B > 15 ;
    # les pixels rosés d'AA (G-B faible) pres du cadre sont rebouches aussi
    # et ne servent jamais de source (sinon liseré rose).
    gb = rgb[:, :, 1].astype(int) - rgb[:, :, 2].astype(int)
    from scipy.ndimage import binary_dilation
    near = binary_dilation(t_sol, iterations=4)
    dist_mag = np.abs(rgb.astype(int) - MAGENTA).sum(axis=2)
    bad = t_sol | (dist_mag < 200) | ((gb < 10) & near)
    sandlike = (gb > 15) & (~bad)
    good = ~bad
    for _ in range(500):
        if not bad.any():
            break
        filled = np.zeros_like(bad)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            src = np.roll(np.roll(sandlike, dy, 0), dx, 1)
            # annule le wrap du roll sur les bords
            if dy == 1:
                src[0, :] = False
            elif dy == -1:
                src[-1, :] = False
            if dx == 1:
                src[:, 0] = False
            elif dx == -1:
                src[:, -1] = False
            take = bad & src & ~filled
            # copie la couleur du voisin sain en [y-dy, x-dx]
            moved = np.roll(np.roll(rgb, dy, 0), dx, 1)
            rgb[take] = moved[take]
            filled |= take
        bad &= ~filled
        good |= filled
        sandlike |= filled
    assert not bad.any(), f"sable non rebouche : {bad.sum()} px"
    l00 = np.dstack([rgb, np.full((288, 408), 255, np.uint8)])
    Image.fromarray(l00).save(OUT / "L00_sol.png")

    # ---- L01/L03 parois + bouche ----
    par = load_small("parois_seules.png")
    rgba_par, t_par = flood_transparent(par)
    rgba_par = despill(rgba_par)
    # bouche = composante quasi noire (coeur ~(8,12,23)) dans le tiers haut.
    # Les fissures de roche sont bien plus claires : seuil strict.
    lum = rgba_par[:, :, :3].astype(int).sum(axis=2)
    dark = (lum < 150) & (rgba_par[:, :, 3] > 0)
    dark[150:, :] = False
    lab, n = label(dark)
    assert n >= 1, "bouche introuvable"
    mouth_id = max(range(1, n + 1), key=lambda i: int((lab == i).sum()))
    mouth = lab == mouth_id
    ys, xs = np.where(mouth)
    mouth_bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    manifest["bouche_bbox"] = mouth_bbox
    print("bouche bbox:", mouth_bbox, "px:", int(mouth.sum()))
    l03 = np.zeros((288, 408, 4), np.uint8)
    l03[mouth] = rgba_par[mouth]
    l01 = rgba_par.copy()
    l01[mouth] = (0, 0, 0, 0)
    l01 = clean(l01)
    l03 = clean(l03)
    Image.fromarray(l01).save(OUT / "L01_parois.png")
    Image.fromarray(l03).save(OUT / "L03_bouche.png")
    Image.fromarray(rgba_par).save(OUT / "L01_parois_avec_bouche_REF.png")

    # ---- L02 props : composantes du brut, replacees ----
    pr = load_small("props_seuls.png")
    rgba_pr, t_pr = flood_transparent(pr)
    rgba_pr = despill(rgba_pr)
    # les props ne contiennent legitiment aucun rose : kill total des
    # residus roses, meme non adjacents au transparent (speckles internes)
    prgb = rgba_pr[:, :, :3].astype(int)
    rose = (prgb[:, :, 0] > 150) & (prgb[:, :, 2] > 120) & (prgb[:, :, 1] < 170)
    rose &= rgba_pr[:, :, 3] > 0
    print("props: pixels roses residuels tues:", int(rose.sum()))
    rgba_pr[rose] = (0, 0, 0, 0)
    solid = rgba_pr[:, :, 3] > 0
    labp, np_ = label(solid)
    comps = []
    for i in range(1, np_ + 1):
        m = labp == i
        if m.sum() > 60:
            yy, xx = np.where(m)
            comps.append({"n": int(m.sum()),
                          "bbox": [int(xx.min()), int(yy.min()), int(xx.max()), int(yy.max())],
                          "id": i})
    comps.sort(key=lambda c: c["bbox"][0])
    print("props composantes:", [(c["bbox"], c["n"]) for c in comps])
    manifest["props_composantes"] = comps
    # ordre attendu gauche->droite : arbre, arbre, arbre, arbre, bloc, bloc
    names = ["arbre0", "arbre1", "arbre2", "arbre3", "bloc0", "bloc1"]
    assert len(comps) == 6, f"attendu 6 props, trouve {len(comps)}"
    l02 = np.zeros((288, 408, 4), np.uint8)
    (OUT / "props").mkdir(exist_ok=True)
    for comp, name in zip(comps, names):
        x0, y0, x1, y1 = comp["bbox"]
        spr = clean(rgba_pr[y0:y1 + 1, x0:x1 + 1].copy())
        Image.fromarray(spr).save(OUT / "props" / f"{name}.png")
        dx, dy = PLACEMENTS[name]
        h, w = spr.shape[:2]
        l02[dy:dy + h, dx:dx + w] = np.where(
            (spr[:, :, 3:4] > 0), spr, l02[dy:dy + h, dx:dx + w])
    manifest["placements"] = PLACEMENTS
    l02 = clean(l02)
    Image.fromarray(l02).save(OUT / "L02_props.png")

    # ---- composite statique ----
    comp = l00.copy()
    for lay in (l01, l03, l02):
        m = lay[:, :, 3:4] > 0
        comp = np.where(m, lay, comp)
    Image.fromarray(comp).save(OUT / "composite.png")
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print("composite + manifest OK")


if __name__ == "__main__":
    main()
