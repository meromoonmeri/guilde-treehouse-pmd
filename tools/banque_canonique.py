#!/usr/bin/env python3
"""Construit la banque de textures canoniques du dépôt.

Pour chaque feuille native `.tile` trouvée dans le dépôt (dédoublonnée par SHA-256) :
  - atlas PNG 1:1 en alpha droit dans `banque_canonique/atlas/<Nom>.png` (+ `.json` : taille de tuile, nombre de tuiles) ;
  - vignette réduite dans `banque_canonique/planches/`.
Pour chaque carte native `.rsground` de référence : rendu composé `banque_canonique/cartes_natives/<nom>.png`
(phase 0) et rendu par calque, uniquement à partir des feuilles disponibles ; les feuilles manquantes sont listées.
Enfin : `INVENTAIRE.json`, `INVENTAIRE.md` et `index.html`.

Aucun pixel natif n'est recoloré, tourné, retourné ou redimensionné dans les atlas 1:1 ; seules les vignettes
(`planches/`) sont réduites, pour la navigation, et ne doivent pas être importées.

Exécution : `.venv/bin/python tools/banque_canonique.py`
"""
import hashlib
import html
import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pmdo_tiles import SheetBank, load_ground, render_ground, tile_to_atlas  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'banque_canonique'
IGNORE_DIRS = {'.git', '.venv', 'node_modules', '__pycache__', 'banque_canonique'}

# Provenance connue des feuilles (dépôt, commit épinglé) — issue des provenance.json / README du dépôt.
PROVENANCE = {
    'Halcyon 1522c7a8 (Palikadude/Halcyon, working-copy)': [
        'Metano_Town_', 'Altere_Pond_', 'Vast_Steppe_', 'Ledian_Dojo_', 'Guild_Second_Floor_', 'SpindaCafe',
        'Relic_Forest_Base', 'Illuminant_Riverbed_Base'],
    'Halcyon da6c2130 (Palikadude/Halcyon)': ['Halcyon__Crooked_Cavern_'],
    'Abyss to Ascension V4 55860b9a (meromoonmeri/new-era-abyss-to-ascension-V4)': ['_Night'],
    'Explorers of Sky Origins (EoSO)': ['ExplorersOfSkyOrigins__'],
    'PMDO DumpAsset 3e767571 (audinowho/DumpAsset)': [
        'CrystalCave1', 'DarkCrater', 'MurkyForest', 'QuicksandCave', 'SealedRuin', 'SkyPeak4thPass',
        'SouthernCavern1', 'SouthernJungle', 'SteamCave', 'TreeshroudForest1', 'VastIceMountain', 'AppleWoods', 'BeachCave'],
}
# Feuilles produites par ce dépôt (copies vérifiées de tuiles natives ou constructions) — signalées, pas natives.
PROJECT_PREFIXES = ('Extension_Metano', 'Falaises_', 'Maisons_', 'Ponts_', 'Metano_Canonique_8px', 'Zones_Guidees_Canon_8px',
                    'Cascades_Metano_Exact', 'Riviere_Metano_Compacte')

FAMILIES = [
    ('Métano Town (village côtier, falaises ocre, rivière)', re.compile(r'^Metano_Town_(?!Cafe)')),
    ('Métano Café (intérieur)', re.compile(r'^Metano_Town_Cafe|^SpindaCafe')),
    ('Altere Pond (étang, falaises sable, cascade)', re.compile(r'^Altere_Pond_')),
    ('Vast Steppe (plaine, rampe herbeuse, fleurs animées)', re.compile(r'^Vast_Steppe_')),
    ('Crooked Cavern (entrée de grotte)', re.compile(r'^Halcyon__Crooked')),
    ('EoSO — Brine Cave / Drenched Bluff (entrées)', re.compile(r'^ExplorersOfSkyOrigins__')),
    ('Halcyon — décors Ground divers', re.compile(r'^Relic_Forest|^Illuminant|^Ledian_Dojo|^Guild_Second_Floor')),
    ('Donjons PMDO — autotiles 24 px (DTEF 47 cases)', re.compile(r'^(CrystalCave1|DarkCrater|MurkyForest|QuicksandCave|SealedRuin|SkyPeak4thPass|SouthernCavern1|SouthernJungle|SteamCave|TreeshroudForest1|VastIceMountain|AppleWoods|BeachCave)$')),
    ('Feuilles construites par ce dépôt (non natives, à ne pas confondre)', re.compile(r'^(' + '|'.join(PROJECT_PREFIXES) + ')')),
]

NATIVE_MAPS = [
    'source/amp_plains_fleurie_v1/references/vast_steppe_entrance.rsground',
    'source/antre_harmonie_v3/references/altere_pond.rsground',
    'source/cafe_multietage_v1/references/metano_cafe.rsground',
    'source/cafe_multietage_v1/references/spinda_cafe.rsground',
    'source/cafe_multietage_v3/references/guild_second_floor.rsground',
    'source/cote_v5_expeditions/references/ExplorersOfSkyOrigins__Brine_Cave_Entrance.rsground',
    'source/cote_v5_expeditions/references/ExplorersOfSkyOrigins__drenched_bluff_entrance.rsground',
    'source/cote_v5_expeditions/references/Halcyon__crooked_cavern_entrance.rsground',
    'source/ledian_dojo_v1/references/ledian_dojo.rsground',
    'cliffdaytest.rsground',
    'cliffnordouesttest1.rsground',
]

USER_REFERENCE_PNGS = [
    'arenapmdskybeach.png', 'aurorepmdsky.png', 'bassinchauffantpmdsky.png', 'bgnightbackgroundpmdskyda.png',
    'entrancearidedungeonpmdsky.png', 'forêtglomypmdsky.png', 'iceroadpmdsky.png', 'interiorbedroompmdsky.png',
    'junglewaterfallzonepmdsky.png', 'lakecrystalpmdsky.png', 'large.P27P01A.png.c5ad9818930eb0d4f403f64607318c37.png',
    'large.S01P03A.png.84e22fb77c4061e77b0f546545fed2c7.png', 'large.S05P03A.png.301f7a1eadda348357be0801e81faa2a.png',
    'oldcastlepmd.png', 'pmdskyicearena.png', 'roadundergound.png', 'rockgeyserlike.png', 'rockroadpmd.png',
    'secretgarden.png', 'starcavepmdsky.png', 'undergroundpmd.png', 'energeticforest.png', 'finalisland.png',
    'witheringdesert.png', 'DSVFS.png',
    'Amp_Plains_entrance_TD.png', 'Apple_Woods_entrance_TDS.png', 'Dark_Crater_Pit_TDS.png', 'Dark_Crater_entrance_TDS.png',
    'Foggy_Forest_Base_Camp_TDS.png', 'Mt_Bristle_entrance_TD.png', 'Mt_Horn_entrance_Sky.png',
    'Mystifying_Forest_entrance_TDS.png', 'Sealed_Ruin_entrance_TDS.png', 'Sealed_Ruin_pit_TDS.png',
    'Southern_Jungle_entrance_S.png', 'Southern_Jungle_exit_2_S.png', 'Southern_Jungle_exit_S.png',
    'Steam_Cave_Peak_TDS.png', 'Steam_Cave_entrance_TDS.png', 'Underground_Lake_shore_TDS.png',
    'Waterfall_Cave_gem_TDS.png', 'Waterfall_Cave_ledge_TDS.png',
    'DS _ DSi - Pokemon Mystery Dungeon_ Explorers of Sky - Maps - Murky Forest & Armaldo House.png',
    'DS _ DSi - Pokemon Mystery Dungeon_ Explorers of Time _ Darkness - Backgrounds - Beach & Path to Beach.png',
    'Game Boy Advance - Pokemon Mystery Dungeon_ Red Rescue Team - Dungeon Boss Rooms - Mt. Thunder.png',
    'Game Boy Advance - Pokemon Mystery Dungeon_ Red Rescue Team - Dungeon Boss Rooms - Northern Range.png',
    'Game Boy Advance - Pokemon Mystery Dungeon_ Red Rescue Team - Friend Areas - Energetic Forest.png',
    'Game Boy Advance - Pokemon Mystery Dungeon_ Red Rescue Team - Friend Areas - Mushroom Forest.png',
    'Game Boy Advance - Pokemon Mystery Dungeon_ Red Rescue Team - Friend Areas - Waterfall Lake.png',
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def iter_tiles():
    for p in sorted(ROOT.rglob('*.tile')):
        if any(part in IGNORE_DIRS for part in p.relative_to(ROOT).parts):
            continue
        yield p


def provenance_of(name):
    for label, prefixes in PROVENANCE.items():
        for pre in prefixes:
            if (pre.startswith('_') and name.endswith(pre)) or name.startswith(pre):
                if label.startswith('Abyss') and not name.endswith('_Night'):
                    continue
                return label
    if name.startswith(PROJECT_PREFIXES):
        return 'Construit par ce dépôt (voir README du dossier source)'
    return 'À vérifier'


def family_of(name):
    for label, rx in FAMILIES:
        if rx.search(name):
            return label
    return 'Autres'


def thumb(img, max_w=720, max_h=420):
    w, h = img.size
    s = 1
    while w // s > max_w or h // s > max_h:
        s += 1
    if s > 1:
        img = img.resize((max(1, w // s), max(1, h // s)), Image.NEAREST)
    bg = Image.new('RGBA', img.size, (255, 0, 255, 255))
    bg.alpha_composite(img)
    return bg.convert('RGB'), s


def main():
    (OUT / 'atlas').mkdir(parents=True, exist_ok=True)
    (OUT / 'planches').mkdir(exist_ok=True)
    (OUT / 'cartes_natives').mkdir(exist_ok=True)
    (OUT / 'references_png').mkdir(exist_ok=True)

    sheets, by_hash = [], {}
    for p in iter_tiles():
        digest = sha256(p)
        rel = str(p.relative_to(ROOT))
        if digest in by_hash:
            by_hash[digest]['copies'].append(rel)
            continue
        size, atlas, meta = tile_to_atlas(p)
        name = p.stem
        dst = OUT / 'atlas' / f'{name}.png'
        atlas.save(dst, optimize=True)
        (OUT / 'atlas' / f'{name}.json').write_text(json.dumps(
            {'sheet': name, 'tile_size': size, 'count': meta['count'], 'atlas_size': meta['atlas_size'],
             'source_tile': rel, 'sha256_tile': digest}, ensure_ascii=False))
        th, s = thumb(atlas)
        th.save(OUT / 'planches' / f'{name}.png', optimize=True)
        entry = {'sheet': name, 'tile_size': size, 'count': meta['count'], 'atlas_size': meta['atlas_size'],
                 'source_tile': rel, 'sha256_tile': digest, 'copies': [], 'family': family_of(name),
                 'provenance': provenance_of(name), 'atlas_png': f'atlas/{name}.png', 'planche': f'planches/{name}.png',
                 'planche_reduction': s}
        by_hash[digest] = entry
        sheets.append(entry)
        print(f'{name:48s} {size:2d}px {meta["count"]:6d} tuiles  atlas {meta["atlas_size"]}  <- {rel}')

    # Cartes natives : rendu avec les feuilles disponibles (alias sur nom normalisé).
    bank = SheetBank()
    bank.add_dir(OUT / 'atlas')
    norm = {re.sub(r'[^a-z0-9]', '', k.lower()): k for k in bank.sheets}
    norm.update({re.sub(r'[^a-z0-9]', '', k.split('__', 1)[-1].lower()): k for k in list(bank.sheets)})

    class AliasBank(SheetBank):
        def get(self, name, x, y, tex_size=1):
            if name not in self.sheets:
                key = re.sub(r'[^a-z0-9]', '', name.lower())
                if key in norm:
                    name = norm[key]
            return SheetBank.get(self, name, x, y, tex_size)

    abank = AliasBank()
    abank.sheets = bank.sheets
    maps = []
    for rel in NATIVE_MAPS:
        p = ROOT / rel
        if not p.exists():
            continue
        g = load_ground(p)
        missing = {}
        out, per_layer = render_ground(g, abank, 0, missing=missing)
        stem = p.stem
        Image.fromarray(out).save(OUT / 'cartes_natives' / f'{stem}.png', optimize=True)
        layer_files = []
        for k, (lname, img) in enumerate(per_layer):
            safe = re.sub(r'[^A-Za-z0-9]+', '_', lname).strip('_') or f'layer{k}'
            fn = f'{stem}__L{k:02d}_{safe}.png'
            Image.fromarray(img).save(OUT / 'cartes_natives' / fn, optimize=True)
            layer_files.append(fn)
        used = {}
        for L in g['Layers']:
            for col in L['Tiles']:
                for c in col:
                    for a in c.get('Layers', []):
                        for fr in a.get('Frames', []):
                            used[fr['Sheet']] = used.get(fr['Sheet'], 0) + 1
        th, s = thumb(Image.fromarray(out), 720, 520)
        th.save(OUT / 'planches' / f'carte__{stem}.png', optimize=True)
        maps.append({'map': rel, 'name': g.get('Name', {}).get('DefaultText', ''), 'tex_size': g.get('TexSize', 1),
                     'cells': [len(g['Layers'][0]['Tiles']), len(g['Layers'][0]['Tiles'][0])],
                     'pixels': [out.shape[1], out.shape[0]], 'layers': [L.get('Name', '') for L in g['Layers']],
                     'sheets_used': used, 'sheets_missing': missing, 'render': f'cartes_natives/{stem}.png',
                     'layer_renders': layer_files, 'planche': f'planches/carte__{stem}.png'})
        print(f'carte {rel}: {out.shape[1]}x{out.shape[0]}, manquantes={list(missing)}')

    refs = []
    for fn in USER_REFERENCE_PNGS:
        p = ROOT / fn
        if not p.exists():
            continue
        im = Image.open(p).convert('RGBA')
        safe = re.sub(r'[^A-Za-z0-9]+', '_', p.stem).strip('_')[:60]
        th, s = thumb(im, 360, 260)
        th.save(OUT / 'references_png' / f'{safe}.png', optimize=True)
        refs.append({'file': fn, 'size': list(im.size), 'planche': f'references_png/{safe}.png', 'sha256': sha256(p)})

    inv = {'sheets': sheets, 'native_maps': maps, 'reference_pngs': refs,
           'note': 'Atlas 1:1 en alpha droit, décodés des .tile prémultipliés. Vignettes réduites uniquement pour la navigation.'}
    (OUT / 'INVENTAIRE.json').write_text(json.dumps(inv, indent=1, ensure_ascii=False))

    # Markdown
    md = ['# Banque de textures canoniques — inventaire', '',
          'Atlas PNG 1:1 (alpha droit) décodés depuis les feuilles natives `.tile` conservées dans le dépôt, '
          'dédoublonnés par SHA-256. Les vignettes de `planches/` sont réduites : ne pas les importer.', '',
          f'Reconstruction : `.venv/bin/python tools/banque_canonique.py` · lecture/rendu : `tools/pmdo_tiles.py`.', '',
          '## Feuilles natives', '', '| Famille | Feuille | Tuile | Tuiles | Atlas (px) | Provenance | Source dans le dépôt |',
          '|---|---|---:|---:|---|---|---|']
    for e in sorted(sheets, key=lambda e: (e['family'], e['sheet'])):
        md.append(f"| {e['family']} | [{e['sheet']}]({e['atlas_png']}) | {e['tile_size']} | {e['count']} | "
                  f"{e['atlas_size'][0]}×{e['atlas_size'][1]} | {e['provenance']} | `{e['source_tile']}` |")
    md += ['', '## Cartes natives rendues (phase 0, feuilles disponibles seulement)', '',
           '| Carte | Nom | TexSize | Cellules | Pixels | Calques | Feuilles manquantes |', '|---|---|---:|---|---|---|---|']
    for m in maps:
        md.append(f"| [{Path(m['map']).name}]({m['render']}) | {m['name']} | {m['tex_size']} | {m['cells'][0]}×{m['cells'][1]} | "
                  f"{m['pixels'][0]}×{m['pixels'][1]} | {', '.join(m['layers'])} | {', '.join(m['sheets_missing']) or '—'} |")
    md += ['', '## Références PNG canoniques fournies par l’utilisateur (racine du dépôt)', '',
           '| Fichier | Taille |', '|---|---|']
    for r in refs:
        md.append(f"| `{r['file']}` | {r['size'][0]}×{r['size'][1]} |")
    (OUT / 'INVENTAIRE.md').write_text('\n'.join(md) + '\n')

    # HTML
    h = ['<!doctype html><meta charset="utf-8"><title>Banque de textures canoniques</title>',
         '<style>body{font-family:system-ui;background:#1b1d22;color:#e8e8e8;margin:20px}h1,h2{font-weight:600}'
         '.g{display:flex;flex-wrap:wrap;gap:14px}.c{background:#23262d;border:1px solid #333;border-radius:8px;padding:8px;max-width:740px}'
         '.c img{image-rendering:pixelated;max-width:720px;display:block;background:#f0f}.c small{color:#aaa;display:block;margin-top:4px}'
         'a{color:#8fd3ff}</style>',
         '<h1>Banque de textures canoniques</h1>',
         '<p>Atlas 1:1 en alpha droit (dossier <code>atlas/</code>) décodés des <code>.tile</code> natifs. Les vignettes ci-dessous sont réduites (facteur indiqué) : ouvrir l’atlas pour les pixels réels. Aucun pixel natif modifié.</p>']
    fam_order = [f for f, _ in FAMILIES] + ['Autres']
    for fam in fam_order:
        items = [e for e in sheets if e['family'] == fam]
        if not items:
            continue
        h.append(f'<h2>{html.escape(fam)}</h2><div class="g">')
        for e in items:
            h.append(f'<div class="c"><a href="{e["atlas_png"]}"><img src="{e["planche"]}" alt=""></a>'
                     f'<b>{html.escape(e["sheet"])}</b><small>tuile {e["tile_size"]} px · {e["count"]} tuiles · atlas {e["atlas_size"][0]}×{e["atlas_size"][1]} px · vignette 1/{e["planche_reduction"]}</small>'
                     f'<small>{html.escape(e["provenance"])}</small><small><code>{html.escape(e["source_tile"])}</code></small></div>')
        h.append('</div>')
    h.append('<h2>Cartes natives (rendu phase 0 avec les feuilles disponibles)</h2><div class="g">')
    for m in maps:
        miss = ', '.join(m['sheets_missing']) or 'aucune'
        h.append(f'<div class="c"><a href="{m["render"]}"><img src="{m["planche"]}" alt=""></a><b>{html.escape(Path(m["map"]).name)}</b>'
                 f'<small>{m["pixels"][0]}×{m["pixels"][1]} px · TexSize {m["tex_size"]} · calques : {html.escape(", ".join(m["layers"]))}</small>'
                 f'<small>feuilles manquantes : {html.escape(miss)}</small></div>')
    h.append('</div><h2>Références PNG canoniques (racine)</h2><div class="g">')
    for r in refs:
        h.append(f'<div class="c"><a href="../{html.escape(r["file"])}"><img src="{r["planche"]}" alt="" style="max-width:360px"></a>'
                 f'<small>{html.escape(r["file"])} · {r["size"][0]}×{r["size"][1]}</small></div>')
    h.append('</div>')
    (OUT / 'index.html').write_text('\n'.join(h))
    print(f'{len(sheets)} feuilles, {len(maps)} cartes, {len(refs)} références -> {OUT}')


if __name__ == '__main__':
    main()
