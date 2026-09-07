#!/usr/bin/env python3
"""Animations manquantes (Eat, Wake, Sink, Faint…) pour huit Pokémon de la guilde.

Méthode — suite directe de celle de Falinks (§3 de METHODE_SPRITES_PMD.md) : **composer,
ne pas générer**. Aucun pixel n'est repeint ni inventé. Chaque image d'une animation
manquante est une case officielle du même Pokémon (Idle, Walk, Hurt, Hop, Charge, Rotate,
Sleep, Swing…), replacée par rapport à son ancre, éventuellement décalée de quelques pixels
ou tronquée par le bas (enfoncement dans le sol). Le **squelette** — nombre d'images, durées,
déplacements d'ancre, nombre de lignes — est relu tel quel sur un sprite officiel qui possède
déjà ces animations (Bayleef #0155, jeu complet Chunsoft), comme le squelette de Rillaboom
avait servi à Zarude (§6).

Pokémon traités : Politoed #0186, Dunsparce #0241, Vigoroth #0297, Gardevoir #0282,
Riolu #0443, Pachirisu #0424, Tarpaud/Grafaiai #0923 et Mega-Charm #0674 — soit les huit
liens fournis. Il leur manquait à tous les 22 animations de scène du « set complet »
de SpriteCollab.

Sorties, dans `personnages/<nom>/animations_scenes/` : les feuilles `-Anim/-Offsets/-Shadow`,
`AnimData.xml` complet (animations d'origine + nouvelles), Aseprite, aperçus, `kit.json`,
`credits.txt`. Les animations d'origine sont recopiées **octet pour octet** depuis la
référence : le dossier est directement importable dans SkyTemple.
"""
from __future__ import annotations

import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source"))
sys.path.insert(0, str(ROOT / "source" / "personnages"))
import pmd_sprite as P                       # noqa: E402
from rebuild_kit import night                # noqa: E402

REF = ROOT / "source" / "personnages" / "reference"
SKELETON = "0155"                            # Bayleef : jeu Chunsoft complet, sert de squelette de temps

POKEMON = {
    "0186": ("politoed", "Politoed", "Tarpaud"),
    "0241": ("miltank", "Miltank", "Écrémeuh"),
    "0297": ("hariyama", "Hariyama", "Hariyama"),
    "0282": ("gardevoir", "Gardevoir", "Gardevoir"),
    "0443": ("gible", "Gible", "Griknot"),
    "0424": ("ambipom", "Ambipom", "Capidextre"),
    "0923": ("pawmot", "Pawmot", "Pawmot"),
    "0674": ("pancham", "Pancham", "Pandespiègle"),
    "0685": ("slurpuff", "Slurpuff", "Aromatisse"),
    "0702": ("dedenne", "Dedenne", "Dedenne"),
}


# ---------------------------------------------------------------------------
# Recettes : une image = une case officielle, replacée.
# ---------------------------------------------------------------------------
@dataclass
class Step:
    src: str                 # animation officielle où prendre la case
    frame: int               # index de l'image dans cette animation
    dx: int = 0              # décalage supplémentaire par rapport à l'ancre
    dy: int = 0
    dir_mode: str = "same"   # "same" = même direction ; "down" = toujours la ligne Bas ;
                             # "spin" = direction (d − frame) mod 8, comme Rotate
    sink: int = 0            # lignes retirées par le bas (enfoncement / évanouissement)
    fade_top: int = 0        # lignes retirées par le haut (glissement dans le sol)
    # --- déformations physiologiques (voir DÉFORMATIONS ci-dessous) ---
    squash: int = 0          # écrasement : le haut descend de n px, les pieds restent posés
    stretch: int = 0         # étirement : le haut monte de n px, les pieds restent posés
    lean: int = 0            # penché : le haut part de n px sur le côté, les pieds restent posés
    pivot: float = 0.45      # hauteur de la charnière (0 = pieds, 1 = sommet) : le bas de la
                             # silhouette ne bouge pas, le haut prend tout le mouvement


# ---------------------------------------------------------------------------
# DÉFORMATIONS PHYSIOLOGIQUES
#
# Un « Eat » ne se fabrique pas en descendant tout le sprite de 2 px : les pattes restent
# posées et c'est le buste et la tête qui plongent vers la nourriture. C'est exactement ce
# que font les animations officielles de Chunsoft. Relevé ligne par ligne sur l'`Eat` de
# Bayleef #0155 (source de vérité de ce fichier) :
#
#     image 0 : lignes 2→19, 188 pixels        (repos)
#     image 1 : lignes 5→19, 162 pixels        (la tête descend de 3 px, le sol ne bouge pas,
#                                               et le sprite PERD 26 pixels : il s'écrase)
#
# Une simple translation garderait 188 pixels et ferait bouger les pieds : c'est faux.
# On reproduit donc l'écrasement par un rééchantillonnage vertical de la seule partie haute
# de la silhouette, la partie basse (pattes, socle) restant intacte — `pivot` fixe la césure.
# Même principe pour l'étirement (LookUp, DeepBreath) et l'inclinaison (LostBalance, Trip).
#
# Aucune couleur n'est créée : on ne fait que supprimer ou dupliquer des lignes/colonnes de
# pixels existants, donc la palette reste celle du sprite d'origine.
# ---------------------------------------------------------------------------
def deform(src: np.ndarray, squash: int, stretch: int, lean: int, pivot: float) -> tuple[np.ndarray, int]:
    """Déforme une silhouette autour d'une charnière basse. Renvoie (image, décalage du haut).

    `squash` / `stretch` : le haut du corps descend / monte de n pixels, la partie basse ne
    bouge pas — le corps se tasse ou se tend, comme sur les animations officielles.
    `lean` : le haut se décale latéralement, proportionnellement à la hauteur.
    """
    h, w = src.shape[:2]
    if h < 4 or (squash == 0 and stretch == 0 and lean == 0):
        return src, 0
    cut = max(1, min(h - 1, int(round(h * (1.0 - pivot)))))   # lignes du haut concernées
    top, bottom = src[:cut], src[cut:]
    delta = squash - stretch
    new_h = max(1, cut - delta)
    # rééchantillonnage au plus proche voisin : on ne fait que garder ou répéter des lignes
    idx = np.clip((np.arange(new_h) * cut) // max(1, new_h), 0, cut - 1)
    top = top[idx]
    if lean:
        # élargir la boîte des deux côtés puis décaler chaque ligne : un `np.roll` ferait
        # réapparaître les pixels sortis par le bord opposé, ce qui couperait la silhouette.
        pad = abs(lean)
        top = np.pad(top, ((0, 0), (pad, pad), (0, 0)))
        bottom = np.pad(bottom, ((0, 0), (pad, pad), (0, 0)))
        rows = []
        for j in range(new_h):
            shift = int(round(lean * (new_h - 1 - j) / max(1, new_h - 1)))
            line = np.zeros_like(top[j])
            if shift >= 0:
                line[shift:] = top[j][:top.shape[1] - shift] if shift else top[j]
            else:
                line[:shift] = top[j][-shift:]
            rows.append(line)
        top = np.stack(rows)
    return np.concatenate([top, bottom]), delta


# Physionomies : quelle charnière et quelle amplitude conviennent au gabarit du Pokémon.
# Un petit rongeur trapu ne plonge pas comme un grand lutteur : l'amplitude est relative
# à la hauteur de la silhouette, mesurée sur la case d'attente.
def physiology(height: int) -> dict:
    """Amplitudes de déformation adaptées à la taille du sprite au repos."""
    return {
        "eat": max(2, round(height * 0.13)),      # plongée de la tête vers le sol
        "bob": max(1, round(height * 0.07)),      # respiration, hochement
        "sit": max(3, round(height * 0.22)),      # affaissement assis
        "look": max(1, round(height * 0.06)),     # étirement vers le haut
        "lean": max(2, round(height * 0.10)),     # inclinaison latérale
    }


# Chaque recette : nom -> (lignes, [Step]). Les durées et les déplacements d'ancre
# viennent du squelette de Bayleef, jamais d'une invention.
# Les amplitudes notées `E`, `B`, `S`, `L`, `N` sont résolues par Pokémon au moment de la
# construction (voir `physiology`) : un Dedenne de 20 px ne plonge pas de la même hauteur
# qu'un Hariyama de 40 px. Les durées et déplacements d'ancre restent ceux du squelette.
class Amp(str):
    """Amplitude symbolique ("eat", "bob"…), résolue en pixels par Pokémon.

    Se comporte comme un nombre pour la négation et la multiplication, de sorte que les
    recettes s'écrivent `lean=-L` ou `squash=S * 2` sans connaître la valeur finale.
    """
    factor = 1

    def _with(self, factor):
        a = Amp(str(self))
        a.factor = self.factor * factor
        return a

    def __neg__(self):
        return self._with(-1)

    def __mul__(self, k):
        return self._with(k)

    __rmul__ = __mul__


E, B, S, L = Amp("eat"), Amp("bob"), Amp("sit"), Amp("look")
N = Amp("lean")

RECIPES: dict[str, tuple[int, list[Step]]] = {
    # Sommeil de scène : la pose de sommeil officielle, disponible dans les huit directions.
    "EventSleep": (8, [Step("Sleep", 0, dir_mode="down"), Step("Sleep", 1, dir_mode="down")]),
    # Réveil : sommeil, sommeil, le corps se déplie et se redresse (écrasement qui se relâche).
    "Wake": (8, [Step("Sleep", 0, dir_mode="down"), Step("Sleep", 1, dir_mode="down"),
                 Step("Idle", 0, squash=S), Step("Idle", 0, squash=B), Step("Idle", 0)]),
    # REPAS — relevé sur l'Eat officiel de Bayleef : le buste et la tête plongent vers le sol,
    # les pattes ne bougent pas, la silhouette se tasse. Deux bouchées, cadence 6/8/6/8.
    "Eat": (1, [Step("Idle", 0),
                Step("Idle", 0, squash=E, pivot=0.35),
                Step("Idle", 0),
                Step("Idle", 0, squash=E, pivot=0.35)]),
    # Culbute avant : le tour complet de Rotate lu sur la ligne Bas.
    "Tumble": (1, [Step("Rotate", i, dir_mode="spin") for i in range(8)]),
    # Pose : attente, puis le buste se cambre et tient.
    "Pose": (8, [Step("Idle", 0), Step("Idle", 0, stretch=B, lean=N), Step("Idle", 0, stretch=B, lean=N)]),
    # Tirer : le corps se penche en arrière et se redresse, en appui sur les pattes.
    "Pull": (1, [Step("Idle", 0, lean=-N if i % 2 else 0, squash=B if i % 2 else 0) for i in range(7)]),
    # Douleur : la case blessée qui tremble et se recroqueville par à-coups.
    "Pain": (8, [Step("Hurt", 1, dx=(1 if i % 2 else 0), squash=(B if i % 4 == 2 else 0)) for i in range(12)]),
    # Flotter : léger sur-place au-dessus du sol — ici tout le corps monte (il ne touche plus terre),
    # donc c'est bien une translation, pas une déformation.
    "Float": (8, [Step("Idle", 0, dy=-3), Step("Idle", 0, dy=-4), Step("Idle", 0, dy=-3), Step("Idle", 0, dy=-2)]),
    # Grande inspiration : le torse se gonfle et se tend, en cadence, pieds au sol.
    "DeepBreath": (1, [Step("Idle", 0),
                       Step("Idle", 0, stretch=L), Step("Idle", 0, stretch=L, dx=-1),
                       Step("Idle", 0, stretch=L), Step("Idle", 0, stretch=L, dx=-1),
                       Step("Idle", 0, stretch=L), Step("Idle", 0, stretch=L, dx=-1),
                       Step("Idle", 0), Step("Idle", 0, squash=B)]),
    # Hochement : la tête plonge et remonte, le corps reste planté.
    "Nod": (8, [Step("Idle", 0), Step("Idle", 0, squash=B, pivot=0.3), Step("Idle", 0)]),
    # S'asseoir : le corps s'affaisse sur son train arrière en trois temps.
    "Sit": (1, [Step("Idle", 0, squash=B), Step("Idle", 0, squash=S, pivot=0.55),
                Step("Idle", 0, squash=S, pivot=0.55, dy=1)]),
    # Lever les yeux : le corps se tend vers le haut et tient.
    "LookUp": (1, [Step("Idle", 0), Step("Idle", 0, stretch=L), Step("Idle", 0, stretch=L)]),
    # S'enfoncer : douze paliers, le sprite disparaît par le bas dans le sol.
    "Sink": (1, [Step("Idle", 0, sink=i * 2, dy=0) for i in range(12)]),
    # Trébucher : le corps part en avant, bascule, puis tombe.
    "Trip": (8, [Step("Hurt", 0), Step("Hurt", 1, lean=N), Step("Hurt", 1, lean=N * 2, squash=B),
                 Step("Hurt", 1, squash=S, dy=2), Step("Hurt", 1, squash=S, dy=3)]),
    # Étendu : la pose de sommeil, tenue une image.
    "Laying": (8, [Step("Sleep", 1, dir_mode="down")]),
    # Bond en avant : la parabole officielle de Hop, six temps.
    "LeapForth": (1, [Step("Hop", i) for i in (0, 1, 3, 5, 6, 8)]),
    # Coup de tête : le buste projeté en avant, une image.
    "Head": (8, [Step("Idle", 0, squash=B, lean=N, pivot=0.3)]),
    # Reculer : le corps se recroqueville sur les deux cases de blessure.
    "Cringe": (1, [Step("Hurt", 0), Step("Hurt", 1, squash=B)]),
    # Perte d'équilibre : le haut du corps bascule d'un côté puis de l'autre, pieds ancrés.
    "LostBalance": (1, [Step("Idle", 0, lean=-N * 2), Step("Idle", 0, lean=N * 2)]),
    # Culbute arrière : le tour de Rotate à l'envers.
    "TumbleBack": (1, [Step("Rotate", (8 - i) % 8, dir_mode="spin") for i in range(10)]),
    # Chute au sol : impact, le corps s'écrase puis rebondit faiblement.
    "HitGround": (1, [Step("Hurt", 1, squash=S, dy=3), Step("Hurt", 1, squash=S, dy=4),
                      Step("Hurt", 1, squash=B, dy=3), Step("Hurt", 1, squash=S, dy=4),
                      Step("Hurt", 1, squash=S, dy=4), Step("Hurt", 1, squash=S, dy=4),
                      Step("Hurt", 1, squash=S, dy=4), Step("Hurt", 1, squash=S, dy=4)]),
    # K.O. : le corps s'affaisse, s'aplatit et s'efface par le haut.
    "Faint": (8, [Step("Hurt", 1, squash=B, dy=2), Step("Hurt", 1, squash=S, dy=3, fade_top=4),
                  Step("Hurt", 1, squash=S, dy=4, fade_top=10), Step("Hurt", 1, squash=S, dy=5, fade_top=18)]),
}


# ---------------------------------------------------------------------------
# Squelette
# ---------------------------------------------------------------------------
def skeleton() -> dict[str, P.Anim]:
    _, anims = P.load_sprite(REF / SKELETON)
    return anims


def resolve(anims: dict[str, P.Anim], name: str) -> P.Anim:
    """Suit les CopyOf (une seule indirection, comme le format l'impose)."""
    a = anims[name]
    return anims[a.copy_of] if a.copy_of else a


def pick(anims: dict[str, P.Anim], step: Step, d: int) -> P.Frame:
    a = resolve(anims, step.src)
    if step.dir_mode == "spin":
        row = (d - step.frame) % 8 if a.dirs > 1 else 0
        col = 0
    elif step.dir_mode == "down" or a.dirs == 1:
        row, col = 0, min(step.frame, len(a.durations) - 1)
    else:
        row, col = (d if d < a.dirs else 0), min(step.frame, len(a.durations) - 1)
    if step.dir_mode == "spin":
        col = min(step.frame % len(a.durations), len(a.durations) - 1)
    return a.frames[row][col]


def amplitudes(anims: dict[str, P.Anim]) -> dict:
    """Amplitudes de déformation de CE Pokémon, d'après la hauteur de sa silhouette au repos."""
    f = anims["Idle"].frames[0][0]
    x0, y0, x1, y1 = f.bbox
    return physiology(y1 - y0 + 1)


def resolved(st: Step, amp: dict) -> tuple[int, int, int]:
    """Remplace les amplitudes symboliques ("eat", "bob"…) par leur valeur en pixels."""
    def val(v):
        if isinstance(v, Amp):
            return int(round(amp[str(v)] * v.factor))
        if isinstance(v, str):
            return amp[v]
        return v
    return val(st.squash), val(st.stretch), val(st.lean)


def build_anim(name: str, anims: dict[str, P.Anim], skel: P.Anim) -> P.Built:
    """`skel` est l'animation homonyme du squelette : elle fournit les durées, le nombre
    d'images, les déplacements d'ancre **et le numéro de créneau** (`<Index>`), qui suit dans
    tous les sprites Chunsoft complets la même numérotation 13 → 34 après Rotate.

    Les déformations physiologiques (`squash`, `stretch`, `lean`) sont appliquées ici : elles
    modifient la silhouette autour d'une charnière basse, de sorte que les appuis au sol
    restent fixes et que seul le haut du corps bouge — comportement des animations Chunsoft."""
    amp = amplitudes(anims)
    rows, steps = RECIPES[name]
    n = len(steps)
    assert n == len(skel.durations), f"{name} : {n} images pour {len(skel.durations)} durées du squelette"
    disp = [skel.frames[0][i].disp for i in range(n)]

    # 1. étendue nécessaire, en coordonnées relatives à l'ancre de la formation
    ext_x = ext_y = 0
    for d in range(rows):
        for i, st in enumerate(steps):
            f = pick(anims, st, d)
            sq, stre, ln = resolved(st, amp)
            x0, y0, x1, y1 = f.bbox
            # la déformation garde le bas en place et déplace le haut de `delta`
            y0 += sq - stre
            x0 -= abs(ln)
            x1 += abs(ln)
            x0 += st.dx + disp[i][0]
            x1 += st.dx + disp[i][0]
            y0 += st.dy + disp[i][1] + st.fade_top
            y1 += st.dy + disp[i][1] - st.sink
            ext_x = max(ext_x, abs(x0), abs(x1))
            ext_y = max(ext_y, abs(y0 + 4), abs(y1 - 4))
    fw = max(16, ((2 * (ext_x + 1) + 7) // 8) * 8)
    fh = max(16, ((2 * (ext_y + 5) + 7) // 8) * 8)

    built = P.Built(name, skel.index, fw, fh, list(skel.durations),
                    notes=f"images composées de cases officielles ; squelette #{SKELETON}")
    ref_shadow = anims["Idle"].frames[0][0]
    for d in range(rows):
        row_cells, row_anchors = [], []
        for i, st in enumerate(steps):
            f = pick(anims, st, d)
            ax = fw // 2 + disp[i][0]
            ay = fh // 2 + 4 + disp[i][1]
            cell = np.zeros((fh, fw, 4), np.uint8)
            offs = np.zeros((fh, fw, 4), np.uint8)
            shad = np.zeros((fh, fw, 4), np.uint8)

            # dessin : uniquement la boîte du contenu, collée par rapport à l'ancre (§4 des ratés)
            sx0, sy0, sx1, sy1 = f.bbox
            src = f.image[f.anchor[1] + sy0:f.anchor[1] + sy1 + 1, f.anchor[0] + sx0:f.anchor[0] + sx1 + 1]
            # déformation physiologique : le bas de la silhouette reste en place, le haut bouge.
            # `delta` > 0 = corps tassé, donc la boîte commence plus bas de `delta` pixels.
            sq, stre, ln = resolved(st, amp)
            if sq or stre or ln:
                src, delta = deform(src, sq, stre, ln, st.pivot)
                sy0 += delta
            if st.sink:
                src = src[:max(0, src.shape[0] - st.sink)]
            if st.fade_top:
                src = src[min(st.fade_top, src.shape[0]):]
                sy0 += st.fade_top
            if src.size:
                px, py = ax + sx0 + st.dx, ay + sy0 + st.dy
                h, w = src.shape[:2]
                px, py = max(0, min(px, fw - w)), max(0, min(py, fh - h))
                block = cell[py:py + h, px:px + w]
                mask = src[:, :, 3] > 0
                block[mask] = src[mask]

            # repères : ceux de la case source, replacés sur la nouvelle ancre
            for key, colour in P.MARK_COLOURS.items():
                if key not in f.marks:
                    continue
                mx, my = f.marks[key]
                mx, my = ax + mx + st.dx, ay + my + st.dy
                if 0 <= mx < fw and 0 <= my < fh:
                    offs[my, mx, :3] = np.maximum(offs[my, mx, :3], colour)
                    offs[my, mx, 3] = 255

            # ombre : gabarit du Pokémon lui-même (case d'attente), autour de la nouvelle ancre
            gx0, gy0, gx1, gy1 = ref_shadow.shadow_box
            g = ref_shadow.shadow
            if g.size:
                px, py = ax + gx0, ay + gy0
                h, w = g.shape[:2]
                if 0 <= px and px + w <= fw and 0 <= py and py + h <= fh:
                    block = shad[py:py + h, px:px + w]
                    mask = g[:, :, 3] > 0
                    block[mask] = g[mask]
            shad[ay, ax] = (255, 255, 255, 255)

            row_cells.append((cell, offs, shad))
            row_anchors.append((ax, ay))
        built.cells.append(row_cells)
        built.anchors.append(row_anchors)
    return built


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------
def font(size: int):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


def contact_sheet(builts: list[P.Built], title: str, path: Path) -> None:
    zoom = 2
    blocks = []
    for b in builts:
        n = len(b.durations)
        img = Image.new("RGBA", (n * (b.fw * zoom + 2) + 8, b.fh * zoom + 28), (26, 26, 46, 255))
        d = ImageDraw.Draw(img)
        d.text((4, 4), f"{b.name} — index {b.index}, case {b.fw} × {b.fh}, {n} images, "
                       f"{b.dirs} direction(s), durées {b.durations}", fill=(230, 230, 230, 255), font=font(12))
        for i in range(n):
            cell = Image.fromarray(b.cells[0][i][0], "RGBA").resize((b.fw * zoom, b.fh * zoom), Image.NEAREST)
            tile = Image.new("RGBA", cell.size, (36, 36, 60, 255))
            tile.alpha_composite(cell)
            img.alpha_composite(tile, (4 + i * (b.fw * zoom + 2), 26))
        blocks.append(img)
    W = max(b.width for b in blocks) + 16
    H = sum(b.height + 6 for b in blocks) + 56
    out = Image.new("RGBA", (W, H), (26, 26, 46, 255))
    d = ImageDraw.Draw(out)
    d.text((12, 10), title, fill=(240, 240, 240, 255), font=font(18))
    d.text((12, 34), "Cases officielles replacées par rapport à l'ancre — aucun pixel repeint. "
                     f"Squelette de temps : #{SKELETON}.", fill=(170, 170, 200, 255), font=font(12))
    y = 56
    for b in blocks:
        out.alpha_composite(b, (8, y))
        y += b.height + 6
    out.save(path, optimize=True)


def parquet(size: tuple[int, int], zoom: int) -> Image.Image:
    src = ROOT / "salles" / "01_accueil" / "salle_jour.png"
    bg = Image.new("RGBA", size, (150, 104, 52, 255))
    if src.is_file():
        tile = Image.open(src).convert("RGBA").crop((264, 252, 392, 316))
        a = np.array(tile).astype(np.int16)
        a[:, :, :3] = (a[:, :, :3] * 0.72).clip(0, 255)
        tile = Image.fromarray(a.astype(np.uint8), "RGBA")
        tile = tile.resize((tile.width * zoom, tile.height * zoom), Image.NEAREST)
        for y in range(0, size[1], tile.height):
            for x in range(0, size[0], tile.width):
                bg.alpha_composite(tile, (x, y))
    return bg


def gif(builts: list[P.Built], names: list[str], path: Path, zoom: int = 3) -> None:
    sel = [b for b in builts if b.name in names]
    cw = max(b.fw for b in sel) * zoom + 8
    ch = max(b.fh for b in sel) * zoom + 8
    bg = parquet((len(sel) * cw, ch), zoom)
    frames, durs = [], []
    total = max(sum(b.durations) for b in sel)
    tick = 0
    while tick < total:
        img = bg.copy()
        step = total - tick
        for col, b in enumerate(sel):
            t = tick % sum(b.durations)
            acc = 0
            for i, dv in enumerate(b.durations):
                if acc + dv > t:
                    step = min(step, acc + dv - t)
                    break
                acc += dv
            cell = Image.fromarray(b.cells[0][i][0], "RGBA").resize((b.fw * zoom, b.fh * zoom), Image.NEAREST)
            ax, ay = b.anchors[0][i]
            img.alpha_composite(cell, (col * cw + cw // 2 - ax * zoom, ch * 2 // 3 - ay * zoom))
        frames.append(img.convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
        durs.append(int(round(step * 1000 / 60)))
        tick += step
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durs, loop=0, optimize=True)


def player_html(num: str, label: str, builts: list[P.Built], originals: list[str], path: Path) -> None:
    manifest = {b.name: {"fw": b.fw, "fh": b.fh, "durations": b.durations, "dirs": b.dirs,
                         "anchors": b.anchors} for b in builts}
    html = f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><title>{label} #{num} — animations de scène</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{{margin:0;font-family:system-ui,sans-serif;background:#1a1a2e;color:#eee}}
header{{padding:12px 16px;border-bottom:1px solid #333}}
h1{{font-size:18px;margin:0 0 4px}} p{{margin:2px 0;color:#aab;font-size:13px}}
.bar{{display:flex;flex-wrap:wrap;gap:8px 16px;padding:10px 16px;align-items:center;font-size:14px}}
canvas{{image-rendering:pixelated;background:#241c14;display:block;margin:12px 16px;border:1px solid #333}}
select,input{{background:#222;color:#eee;border:1px solid #444;padding:3px}}
</style></head><body>
<header><h1>{label} #{num} — animations de scène ajoutées</h1>
<p>Cases officielles replacées par rapport à l'ancre, squelette de temps du sprite #{SKELETON}. Aucun pixel repeint.</p></header>
<div class="bar">
<label>Animation <select id="anim"></select></label>
<label>Direction <select id="dir"></select></label>
<label>Zoom <input id="zoom" type="range" min="1" max="8" value="4"></label>
<label><input id="play" type="checkbox" checked> lecture</label>
<span id="info"></span></div>
<canvas id="c" width="400" height="300"></canvas>
<script>
const M = {json.dumps(manifest)};
const imgs = {{}};
const anim = document.getElementById('anim'), dsel = document.getElementById('dir');
for (const k of Object.keys(M)) {{ const o = document.createElement('option'); o.textContent = k; anim.append(o); }}
function loadDirs() {{
  dsel.innerHTML = '';
  const names = ['Bas','Bas-droite','Droite','Haut-droite','Haut','Haut-gauche','Gauche','Bas-gauche'];
  for (let i = 0; i < M[anim.value].dirs; i++) {{ const o = document.createElement('option'); o.value = i; o.textContent = names[i]; dsel.append(o); }}
}}
anim.onchange = loadDirs; loadDirs();
function img(n) {{ if (!imgs[n]) {{ const i = new Image(); i.src = n + '-Anim.png'; imgs[n] = i; }} return imgs[n]; }}
const c = document.getElementById('c'), g = c.getContext('2d');
let t = 0;
setInterval(() => {{
  const m = M[anim.value], z = +document.getElementById('zoom').value, d = +dsel.value || 0;
  const total = m.durations.reduce((a, b) => a + b, 0);
  if (document.getElementById('play').checked) t = (t + 1) % total; 
  let acc = 0, f = 0;
  for (let i = 0; i < m.durations.length; i++) {{ if (acc + m.durations[i] > t) {{ f = i; break; }} acc += m.durations[i]; }}
  c.width = m.fw * z + 40; c.height = m.fh * z + 40;
  g.imageSmoothingEnabled = false;
  g.clearRect(0, 0, c.width, c.height);
  const im = img(anim.value);
  if (im.complete) g.drawImage(im, f * m.fw, d * m.fh, m.fw, m.fh, 20, 20, m.fw * z, m.fh * z);
  document.getElementById('info').textContent = anim.value + ' — image ' + (f + 1) + '/' + m.durations.length + ', case ' + m.fw + ' × ' + m.fh;
}}, 1000 / 60);
</script>
<p style="padding:0 16px 24px;color:#889;font-size:12px">Animations d'origine conservées telles quelles : {", ".join(originals)}.</p>
</body></html>
"""
    path.write_text(html, encoding="utf-8")


def credits(num: str, label: str, out: Path) -> None:
    src = (REF / num / "credits.txt").read_text(encoding="utf-8").rstrip("\n").splitlines()
    new = [f"# {label} #{num} — animations de scène ajoutées à partir des cases officielles",
           "# Lignes d'origine du dépôt SpriteCollab, conservées :"] + src + [
        "2026-09-07 00:00:00.000000\tGuilde Treehouse (composition scriptée, aucun pixel repeint)\tCUR\tCC_BY-NC_4\t"
        + ",".join(RECIPES),
        "",
        f"Sprite d'origine : https://sprites.pmdcollab.org/#/{num}?form=0 — crédits et licence ci-dessus.",
        f"Squelette de temps (durées, déplacements d'ancre, nombre d'images) : sprite officiel #{SKELETON}, inchangé.",
        "Les animations ajoutées ne contiennent que des pixels des cases officielles du même Pokémon, replacés.",
        "Elles n'ont été ni soumises ni approuvées sur SpriteCollab.",
    ]
    (out / "credits.txt").write_text("\n".join(new) + "\n", encoding="utf-8")


def build_one(num: str, skel: dict[str, P.Anim]) -> dict:
    folder, label, fr = POKEMON[num]
    out = ROOT / "personnages" / folder / "animations_scenes"
    out.mkdir(parents=True, exist_ok=True)
    (out / "nuit").mkdir(exist_ok=True)
    shadow_size, anims = P.load_sprite(REF / num)

    builts = [build_anim(name, anims, skel[name]) for name in RECIPES]
    for b in builts:
        for which, kind in enumerate(["Anim", "Offsets", "Shadow"]):
            P.sheet(b, which).save(out / f"{b.name}-{kind}.png", optimize=True)
        night(P.sheet(b, 0)).save(out / "nuit" / f"{b.name}-Anim.png", optimize=True)

    # animations d'origine recopiées telles quelles pour que le dossier soit importable
    originals = []
    entries: list = []
    for name, a in anims.items():
        if a.copy_of:
            entries.append((name, a.index, a.copy_of))
            originals.append(f"{name} (copie de {a.copy_of})")
            continue
        for kind in ("Anim", "Offsets", "Shadow"):
            shutil.copyfile(REF / num / f"{name}-{kind}.png", out / f"{name}-{kind}.png")
        entries.append(P.Built(name, a.index, a.fw, a.fh, a.durations, rush=a.rush, hit=a.hit, ret=a.ret))
        originals.append(name)
    P.write_animdata(shadow_size, entries + builts, out / "AnimData.xml")

    ase = P.write_aseprite(builts, out / f"{folder}_scenes.aseprite")
    contact_sheet(builts, f"{label.upper()} #{num} — 22 ANIMATIONS DE SCÈNE AJOUTÉES (× 2)", out / "apercu.png")
    gif(builts, ["Eat", "Wake", "Nod", "Sit"], out / "apercu_eat.gif")
    gif(builts, ["Faint", "HitGround", "Sink", "Tumble"], out / "apercu_chute.gif")
    player_html(num, label, builts, originals, out / "apercu.html")
    credits(num, label, out)

    used: set[tuple[int, int, int]] = set()
    for b in builts:
        for row in b.cells:
            for cell in row:
                px = cell[0][cell[0][:, :, 3] > 0]
                used |= set(map(tuple, px[:, :3].tolist()))
    kit = {
        "pokemon": {"numero": num, "nom": label, "nom_fr": fr, "forme": "0000",
                    "source": f"https://sprites.pmdcollab.org/#/{num}?form=0"},
        "methode": "composition : chaque image est une case officielle du même Pokémon, replacée par rapport à son ancre "
                   f"(décalage, direction, troncature) ; durées et déplacements d'ancre relus sur le squelette #{SKELETON}",
        "shadow_size": shadow_size,
        "animations_origine": originals,
        "animations_ajoutees": {b.name: {"index": b.index, "case": [b.fw, b.fh], "images": len(b.durations),
                                         "directions": b.dirs, "durees": b.durations, "ticks": sum(b.durations),
                                         "sources": sorted({s.src for s in RECIPES[b.name][1]})}
                                for b in builts},
        "aseprite": ase,
        "nuit": "nuit/<Anim>-Anim.png : filtre night() de source/rebuild_kit.py ; Offsets et Shadow inchangés",
        "palette": sorted("#%02x%02x%02x" % c for c in used),
        "couleurs": len(used),
    }
    (out / "kit.json").write_text(json.dumps(kit, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"numero": num, "nom": label, "ajoutees": len(builts), "couleurs": len(used),
            "dossier": str(out.relative_to(ROOT))}


def main() -> None:
    skel = skeleton()
    manquants = [n for n in RECIPES if n not in skel]
    assert not manquants, f"le squelette #{SKELETON} n'a pas {manquants}"
    resume = [build_one(num, skel) for num in POKEMON]
    for r in resume:
        print(f"#{r['numero']} {r['nom']:10s} : {r['ajoutees']} animations, {r['couleurs']} couleurs → {r['dossier']}")


if __name__ == "__main__":
    main()
