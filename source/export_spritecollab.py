#!/usr/bin/env python3
"""Export final au **format exact du dépôt PMDCollab/SpriteCollab**.

Les dossiers `personnages/` et `portraits/` de ce dépôt sont organisés pour le travail : ils
contiennent des aperçus, des GIF, des fichiers Aseprite, des variantes nuit, des `kit.json`.
Rien de tout cela n'existe dans SpriteCollab. Ce script produit à côté une arborescence
**telle qu'on la déposerait sur le dépôt officiel**, et rien d'autre.

────────────────────────────────────────────────────────────────────────────────
LE FORMAT OFFICIEL, RELEVÉ SUR LE DÉPÔT
────────────────────────────────────────────────────────────────────────────────
    sprite/<num>/
        AnimData.xml            fins de ligne CRLF, deux espaces d'indentation,
                                déclaration `<?xml version="1.0"?>` (sans espace avant `?>`)
        <Anim>-Anim.png         feuille RGBA
        <Anim>-Offsets.png
        <Anim>-Shadow.png
        credits.txt             une ligne par contribution, colonnes séparées par des
                                tabulations : date, auteur, CUR, licence, liste d'animations
    portrait/<num>/
        <Emotion>.png           40 × 40 RGBA
        <Emotion>^.png          version retournée
        credits.txt             même format, la liste énumère les émotions

Points vérifiés sur les fichiers officiels et reproduits ici :
- `AnimData.xml` officiel est en **CRLF** avec une indentation de **deux espaces** ; le nôtre
  était en LF avec des tabulations. Sans importance pour SkyTemple, mais un diff propre sur le
  dépôt officiel compte pour une contribution.
- les PNG sont écrits sans métadonnées superflues ;
- `credits.txt` **conserve les lignes d'origine** et ajoute la nôtre à la fin.

────────────────────────────────────────────────────────────────────────────────
CE QUI EST EXPORTÉ
────────────────────────────────────────────────────────────────────────────────
sprite/  : les dix Pokémon complétés (animations d'origine + les 22 de scène), plus le `Eat`
           dessiné à la main de Politoed, qui remplace le `Eat` composé.
portrait/: les quatre planches complétées à 16 émotions + versions `^`.

Un `RAPPORT.md` récapitule ce qui est officiel, ce qui est ajouté, et par quel moyen.
"""
from __future__ import annotations

import shutil
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "source" / "personnages"))
sys.path.insert(0, str(ROOT / "source" / "portraits"))
OUT = ROOT / "spritecollab"

# num -> dossier de travail contenant le sprite complet
SPRITES = {
    "0186": "politoed", "0241": "miltank", "0282": "gardevoir", "0297": "hariyama",
    "0424": "ambipom", "0443": "gible", "0674": "pancham", "0685": "slurpuff",
    "0702": "dedenne", "0923": "pawmot",
}
PORTRAITS = {"0186": "politoed", "0297": "hariyama", "0424": "ambipom", "0923": "pawmot"}

# Le `Eat` dessiné à la main remplace le `Eat` composé pour ces Pokémon : leur bouche s'ouvre
# vraiment, dessinée dans la palette du sprite (voir `dessine_eat_politoed.py` et
# `dessine_eat_officiel.py`). Les autres gardent le `Eat` composé, faute d'un trait de bouche
# assez lisible à leur échelle pour être animé sans bouillie.
EAT_DESSINE = {
    num: ROOT / "personnages" / nom / "eat_dessine"
    for num, nom in [("0186", "politoed"), ("0424", "ambipom"), ("0443", "gible"),
                     ("0923", "pawmot"), ("0702", "dedenne")]
}
# Produits par un **générateur d'images**, puis disciplinés (grille exacte, palette rabattue sur
# celle du sprite, masque limité à la bouche) et vérifiés — voir `eat_generateur.py`.
EAT_GENERE = {
    num: ROOT / "personnages" / nom / "eat_generateur"
    for num, nom in [("0282", "gardevoir"), ("0674", "pancham"), ("0685", "slurpuff")]
}
EAT_DESSINE.update(EAT_GENERE)

AUTEUR = "Guilde Treehouse"
EMOTIONS = ["Normal", "Happy", "Pain", "Angry", "Worried", "Sad", "Crying", "Shouting",
            "Teary-Eyed", "Determined", "Joyous", "Inspired", "Surprised", "Dizzy",
            "Sigh", "Stunned"]
SCENES = ["EventSleep", "Wake", "Eat", "Tumble", "Pose", "Pull", "Pain", "Float", "DeepBreath",
          "Nod", "Sit", "LookUp", "Sink", "Trip", "Laying", "LeapForth", "Head", "Cringe",
          "LostBalance", "TumbleBack", "HitGround", "Faint"]


def animdata_officiel(source: Path, cible: Path) -> int:
    """Réécrit `AnimData.xml` avec la mise en forme exacte du dépôt officiel (CRLF, 2 espaces)."""
    root = ET.parse(source).getroot()
    lignes = ['<?xml version="1.0"?>', "<AnimData>",
              f"  <ShadowSize>{root.findtext('ShadowSize')}</ShadowSize>", "  <Anims>"]
    n = 0
    for anim in root.find("Anims").iter("Anim"):
        n += 1
        lignes.append("    <Anim>")
        lignes.append(f"      <Name>{anim.findtext('Name')}</Name>")
        if anim.findtext("Index") is not None:
            lignes.append(f"      <Index>{anim.findtext('Index')}</Index>")
        if anim.findtext("CopyOf") is not None:
            lignes.append(f"      <CopyOf>{anim.findtext('CopyOf')}</CopyOf>")
            lignes.append("    </Anim>")
            continue
        lignes.append(f"      <FrameWidth>{anim.findtext('FrameWidth')}</FrameWidth>")
        lignes.append(f"      <FrameHeight>{anim.findtext('FrameHeight')}</FrameHeight>")
        for tag in ("RushFrame", "HitFrame", "ReturnFrame"):
            if anim.findtext(tag) is not None:
                lignes.append(f"      <{tag}>{anim.findtext(tag)}</{tag}>")
        lignes.append("      <Durations>")
        for d in anim.find("Durations").iter("Duration"):
            lignes.append(f"        <Duration>{d.text}</Duration>")
        lignes.append("      </Durations>")
        lignes.append("    </Anim>")
    lignes += ["  </Anims>", "</AnimData>", ""]
    cible.write_bytes("\r\n".join(lignes).encode("utf-8"))
    return n


def png_propre(source: Path, cible: Path) -> None:
    """Recopie un PNG en RGBA sans métadonnée, comme les fichiers du dépôt."""
    Image.open(source).convert("RGBA").save(cible, "PNG", optimize=True)


def credits_officiels(origine: Path, cible: Path, ajout: str, licence: str) -> None:
    """Conserve les lignes d'origine et ajoute la nôtre, au format tabulé du dépôt."""
    lignes = []
    if origine.is_file():
        lignes = [l for l in origine.read_text(encoding="utf-8").splitlines() if l.strip()]
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")
    lignes.append(f"{date}\t{AUTEUR}\tCUR\t{licence}\t{ajout}")
    cible.write_bytes(("\n".join(lignes) + "\n").encode("utf-8"))


def licence_du_sprite(credits: Path) -> str:
    """Reprend la licence la plus restrictive déjà déclarée sur le sprite."""
    if not credits.is_file():
        return "Unspecified"
    licences = {l.split("\t")[3] for l in credits.read_text(encoding="utf-8").splitlines()
                if len(l.split("\t")) > 3}
    for candidate in ("CC_BY-NC_4", "PMDCollab_2", "PMDCollab_1", "Unspecified"):
        if candidate in licences:
            return candidate
    return "Unspecified"


def exporter_sprite(num: str, dossier: str, rapport: list) -> None:
    src = ROOT / "personnages" / dossier / "animations_scenes"
    dst = OUT / "sprite" / num
    dst.mkdir(parents=True, exist_ok=True)

    # Le Eat dessiné remplace le Eat composé, s'il existe pour ce Pokémon.
    remplace = EAT_DESSINE.get(num)
    for png in sorted(src.glob("*.png")):
        if remplace and png.name.startswith("Eat-"):
            continue
        png_propre(png, dst / png.name)
    if remplace:
        for png in sorted(remplace.glob("Eat-*.png")):
            png_propre(png, dst / png.name)

    # AnimData : si le Eat dessiné a une autre case, reprendre ses dimensions
    arbre = ET.parse(src / "AnimData.xml")
    if remplace:
        neuf = ET.parse(remplace / "AnimData.xml").getroot()
        src_eat = next(a for a in neuf.find("Anims").iter("Anim") if a.findtext("Name") == "Eat")
        for anim in arbre.getroot().find("Anims").iter("Anim"):
            if anim.findtext("Name") == "Eat":
                for tag in ("FrameWidth", "FrameHeight"):
                    anim.find(tag).text = src_eat.findtext(tag)
    tmp = dst / "_tmp.xml"
    arbre.write(tmp, encoding="utf-8", xml_declaration=True)
    n = animdata_officiel(tmp, dst / "AnimData.xml")
    tmp.unlink()

    origine = ROOT / "source" / "personnages" / "reference" / num / "credits.txt"
    licence = licence_du_sprite(origine)
    ajout = ",".join(SCENES)
    credits_officiels(origine, dst / "credits.txt", ajout, licence)
    rapport.append({"type": "sprite", "num": num, "nom": dossier, "animations": n,
                    "ajoutees": len(SCENES), "licence": licence,
                    "eat": ("généré puis discipliné" if num in EAT_GENERE
                            else "dessiné à la main" if remplace else "composé")})


def exporter_portrait(num: str, dossier: str, rapport: list) -> None:
    src = ROOT / "portraits" / dossier / "emotions"
    dst = OUT / "portrait" / num
    dst.mkdir(parents=True, exist_ok=True)
    noms = []
    for emo in EMOTIONS:
        for suffixe in ("", "^"):
            f = src / f"{emo}{suffixe}.png"
            if f.is_file():
                png_propre(f, dst / f.name)
                noms.append(f"{emo}{suffixe}")
    origine = ROOT / "source" / "portraits" / "reference" / num / "credits.txt"
    licence = licence_du_sprite(origine)
    credits_officiels(origine, dst / "credits.txt", ",".join(noms), licence)
    rapport.append({"type": "portrait", "num": num, "nom": dossier,
                    "emotions": len(noms), "licence": licence})


def controler(rapport: list) -> list[str]:
    """Relit l'export : dimensions, alpha, palette, cohérence AnimData ↔ feuilles."""
    journal = []
    for d in sorted((OUT / "sprite").iterdir()):
        root = ET.parse(d / "AnimData.xml").getroot()
        brut = (d / "AnimData.xml").read_bytes()
        assert brut.count(b"\r\n") and brut.count(b"\n") == brut.count(b"\r\n"), f"{d.name} : CRLF"
        for anim in root.find("Anims").iter("Anim"):
            nom = anim.findtext("Name")
            if anim.findtext("CopyOf") is not None:
                continue
            fw, fh = int(anim.findtext("FrameWidth")), int(anim.findtext("FrameHeight"))
            durees = len(list(anim.find("Durations").iter("Duration")))
            for genre in ("Anim", "Offsets", "Shadow"):
                f = d / f"{nom}-{genre}.png"
                assert f.is_file(), f"{d.name}/{f.name} manquant"
                im = Image.open(f)
                assert im.mode == "RGBA", f"{f} mode {im.mode}"
                assert im.width == fw * durees and im.height % fh == 0, f"{f} {im.size} ≠ {fw}×{fh}×{durees}"
            a = np.array(Image.open(d / f"{nom}-Anim.png"))
            assert set(np.unique(a[:, :, 3]).tolist()) <= {0, 255}, f"{nom} alpha"
            couleurs = len({tuple(c) for c in a[a[:, :, 3] > 0][:, :3].tolist()})
            assert couleurs <= 15, f"{d.name}/{nom} {couleurs} couleurs"
        journal.append(f"sprite/{d.name} : {len(list(root.find('Anims').iter('Anim')))} animations, format officiel")
    for d in sorted((OUT / "portrait").iterdir()):
        n = 0
        for f in d.glob("*.png"):
            im = Image.open(f)
            assert im.size == (40, 40) and im.mode == "RGBA", f"{f} {im.size} {im.mode}"
            a = np.array(im)
            assert (a[:, :, 3] == 255).all(), f"{f} doit être opaque"
            assert len({tuple(c) for c in a[:, :, :3].reshape(-1, 3).tolist()}) <= 15, f"{f} palette"
            n += 1
        for emo in EMOTIONS:
            droit, gauche = np.array(Image.open(d / f"{emo}.png")), np.array(Image.open(d / f"{emo}^.png"))
            assert np.array_equal(gauche, droit[:, ::-1]), f"{d.name}/{emo}^ miroir"
        journal.append(f"portrait/{d.name} : {n} images 40 × 40, miroirs exacts")
    return journal


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    rapport: list = []
    for num, dossier in sorted(SPRITES.items()):
        exporter_sprite(num, dossier, rapport)
    for num, dossier in sorted(PORTRAITS.items()):
        exporter_portrait(num, dossier, rapport)
    journal = controler(rapport)

    sprites = [r for r in rapport if r["type"] == "sprite"]
    portraits = [r for r in rapport if r["type"] == "portrait"]
    lignes = [
        "# Export au format SpriteCollab",
        "",
        "Arborescence telle qu'on la déposerait sur "
        "[PMDCollab/SpriteCollab](https://github.com/PMDCollab/SpriteCollab) : **rien que les",
        "fichiers du format officiel**, sans aperçu, sans GIF, sans Aseprite, sans `kit.json`.",
        "",
        "```",
        "spritecollab/",
        "├── sprite/<num>/    AnimData.xml (CRLF, 2 espaces), <Anim>-Anim/Offsets/Shadow.png, credits.txt",
        "└── portrait/<num>/  <Emotion>.png et <Emotion>^.png en 40 × 40, credits.txt",
        "```",
        "",
        "## Sprites — animations de scène ajoutées",
        "",
        "| # | Pokémon | Animations au total | Ajoutées | `Eat` | Licence |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in sprites:
        lignes.append(f"| {r['num']} | {r['nom'].capitalize()} | {r['animations']} | "
                      f"{r['ajoutees']} | {r['eat']} | {r['licence']} |")
    lignes += [
        "",
        f"Les {len(SCENES)} animations ajoutées : " + ", ".join(f"`{s}`" for s in SCENES) + ".",
        "",
        "## Portraits — émotions complétées",
        "",
        "| # | Pokémon | Images (émotions + miroirs) | Licence |",
        "| --- | --- | --- | --- |",
    ]
    for r in portraits:
        lignes.append(f"| {r['num']} | {r['nom'].capitalize()} | {r['emotions']} | {r['licence']} |")
    lignes += [
        "",
        "## Comment c'est fait",
        "",
        "- **Animations de scène** : chaque image est une case officielle du Pokémon lui-même,",
        "  replacée par rapport à son ancre, avec déformation à charnière basse (les appuis au sol",
        "  restent fixes) et membres articulés repérés par les ancres `lhand`/`rhand` de",
        "  `-Offsets.png`. Cadences, cases et créneaux `<Index>` relus sur Bayleef #0155.",
        "  **Aucun pixel repeint** : la palette est incluse dans celle du sprite d'origine.",
        "- **`Eat` dessinés à la main** (Politoed, Ambipom, Gible, Pawmot, Dedenne) : la bouche est",
        "  peinte dans la palette du sprite, à la manière relevée sur les `Eat` de Pichu #0172 et",
        "  Riolu #0447 (palette fermée, cerne noir, ombrage ordonné, changement local).",
        "- **`Eat` produits par générateur d'images** (Gardevoir, Pancham, Slurpuff) : le PNG du sprite",
        "  officiel a été soumis à un générateur, dont la sortie a été ramenée sur la grille exacte,",
        "  rabattue sur la palette du sprite (178 à 251 couleurs → 9 à 11) et limitée au rectangle de",
        "  la bouche. 86 à 90 % du sprite conservé. Hariyama et Miltank, essayés de la même façon,",
        "  ont été **écartés** (68 % et 15 % de conservation : personnage méconnaissable).",
        "- **Portraits** : le `Normal` officiel sert de base et n'est jamais redessiné. Le fond est",
        "  repeint aux **couleurs canoniques de l'émotion** dans la géométrie officielle (ciel plein,",
        "  damier de transition, sol plein) ; les yeux sont transformés par opérations sur leurs",
        "  propres couleurs ; les effets viennent de la palette Chunsoft.",
        "",
        "## Contrôle",
        "",
        "```",
    ] + [f"{l}" for l in journal] + [
        "```",
        "",
        "Vérifié à l'export : `AnimData.xml` en CRLF, feuilles aux dimensions déclarées, alpha 0 ou 255,",
        "15 couleurs au plus, portraits 40 × 40 opaques, versions `^` miroirs exacts.",
        "",
        "## Licence et statut",
        "",
        "Les `credits.txt` **conservent toutes les lignes d'origine** et ajoutent la contribution en",
        "reprenant la licence déjà déclarée sur le sprite. Ces ajouts n'ont été **ni soumis ni",
        "approuvés** sur SpriteCollab : c'est un export prêt à être proposé, pas un contenu officiel.",
        "",
    ]
    (OUT / "RAPPORT.md").write_text("\n".join(lignes), encoding="utf-8")

    fichiers = sum(1 for _ in OUT.rglob("*") if _.is_file())
    print(f"Export SpriteCollab : {len(sprites)} sprites, {len(portraits)} planches de portraits, "
          f"{fichiers} fichiers → {OUT.relative_to(ROOT)}")
    for l in journal:
        print("  " + l)


if __name__ == "__main__":
    main()
