"""Batch V7 — first slice of the 124 missing guild actions, built only from
native pixels already pinned in the audit references.

Two action families are safe to author for every member with zero invented
anatomy and no held-item masking:
  * Pain       : a flinch/wince assembled from the native Hurt sheet (8 dirs).
                 Every produced frame is a translated copy of a native Hurt
                 frame; nothing is recolored or redrawn.
  * DeepBreath : a subtle breathing bob assembled from the native Idle sheet
                 (8 dirs), again pure translation of native frames.

Producing these does not claim artistic approval or a PMDO runtime test; it
only supplies technically-valid cycles whose every visible pixel is provably a
native source pixel (see the provenance arrays and test_build.py).
"""
from pathlib import Path
import sys, json, hashlib, shutil, base64
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]; SRC = Path(__file__).parent
OUT = ROOT/'exports/guild_scene_actions_v7'
REF = ROOT/'source/guild_members_audit/references'
sys.path.insert(0, str(ROOT/'source/guild_scene_recovery_v5'))
import build as v5  # reuse DIRS, export_action, preview, native loaders

MEMBERS = [
    ('0282', 'Gardevoir', 'gardevoir'),
    ('0083', 'Farfetch’d', 'farfetchd'),
    ('0674', 'Pancham', 'pancham'),
    ('0285', 'Shroomish', 'shroomish'),
    ('0461', 'Weavile', 'weavile'),
    ('0186', 'Politoed', 'politoed'),
]

# 16-step choreographies expressed as (native_frame_index, dx, dy). Pure
# translations of native drawings; loop closes (first == last).
PAIN_STEPS = [(0,0,0),(1,0,0),(1,0,1),(1,0,1),(1,0,1),(1,0,0),(1,0,0),(1,0,1),
              (1,0,0),(1,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0)]
BREATH_STEPS = [(0,0,0),(0,0,0),(0,0,0),(0,0,1),(0,0,1),(0,0,1),(0,0,1),(0,0,0),
                (0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0)]
PAIN_TICKS = [3,2,3,3,3,2,4,2,3,6,4,3,3,3,3,3]
BREATH_TICKS = [4,3,3,3,4,4,4,3,3,3,4,4,4,4,4,4]


def load_action(slot, name):
    folder = REF/slot/'sprite'
    root = ET.parse(folder/'AnimData.xml').getroot()
    a = next(a for a in root.findall('./Anims/Anim') if a.findtext('Name') == name)
    w, h = int(a.findtext('FrameWidth')), int(a.findtext('FrameHeight'))
    ticks = [int(d.text) for d in a.findall('./Durations/Duration')]
    anim = Image.open(folder/f'{name}-Anim.png').convert('RGBA')
    offs = Image.open(folder/f'{name}-Offsets.png').convert('RGBA')
    shad = Image.open(folder/f'{name}-Shadow.png').convert('RGBA')
    cols, rows = anim.size[0]//w, anim.size[1]//h
    return dict(w=w, h=h, ticks=ticks, cols=cols, rows=rows, anim=anim, offs=offs, shad=shad)


def translated(frame_sheet, w, h, di, fi, dx, dy):
    base = frame_sheet.crop((fi*w, di*h, (fi+1)*w, (di+1)*h))
    out = Image.new('RGBA', (w, h))
    out.alpha_composite(base, (dx, dy))
    return out


def build_action(src, steps):
    """rows[dir][frame] = [anim, offsets, shadow]; prov[dir][frame] = (fi,dx,dy)."""
    rows, prov = [], []
    for di in range(8):
        row, prow = [], []
        sh = src['shad'].crop((0, di*src['h'], src['w'], (di+1)*src['h']))
        for (fi, dx, dy) in steps:
            an = translated(src['anim'], src['w'], src['h'], di, fi % src['cols'], dx, dy)
            of = translated(src['offs'], src['w'], src['h'], di, fi % src['cols'], dx, dy)
            row.append([an, of, sh.copy()]); prow.append([int(fi), dx, dy])
        rows.append(row); prov.append(prow)
    return rows, prov


def preview(prefix, rows, ticks):
    """Local preview GIFs into this lot's review folder (not V5's)."""
    folder = OUT/'review'; folder.mkdir(parents=True, exist_ok=True)
    dur = [round(t*1000/60/10)*10 for t in ticks]
    TW, TH = 48, 64  # preview cell box, bottom-aligned
    boards = []
    for f in range(len(rows[0])):
        board = Image.new('RGB', (640, 448), (35, 47, 60)); draw = ImageDraw.Draw(board)
        for d, row in enumerate(rows):
            actor = row[f][0]
            tile = Image.new('RGBA', (TW, TH), (35, 47, 60, 255)); tile.alpha_composite(actor, ((TW-actor.width)//2, TH-actor.height))
            x = d % 4 * 160; y = d // 4 * 224
            sc = min(160//TW, 200//TH)
            board.paste(tile.convert('RGB').resize((TW*sc, TH*sc), Image.Resampling.NEAREST), (x, y+24+(200-TH*sc)))
            draw.text((x+6, y+6), v5.DIRS[d], fill='white')
        boards.append(board)
    boards[0].save(folder/f'{prefix}_8directions.gif', save_all=True, append_images=boards[1:], duration=dur, loop=0, disposal=2)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'scope': 'First slice of the missing guild actions. Every visible pixel is a translated copy of a pinned native frame; no recoloring, redraw or held-item masking.',
              'source_pin': '3609a86be2a4c8ad7cf255bd2255f044daafe24f', 'food_in_sprite': False,
              'art_approved': False, 'runtime_PMDO': 'NOT TESTED', 'actions': {}, 'packs': {}}
    sys.path.insert(0, str(ROOT/'source/pmd_character_pipeline'))
    from validate import run

    for slot, name, slug in MEMBERS:
        pack = OUT/slug; pack.mkdir(exist_ok=True)
        base = REF/slot/'sprite'
        for p in base.iterdir():
            if p.suffix in ['.png', '.xml']:
                shutil.copyfile(p, pack/p.name)
        root = ET.parse(base/'AnimData.xml').getroot()
        hurt = load_action(slot, 'Hurt'); idle = load_action(slot, 'Idle')
        tasks = [('Pain', hurt, PAIN_STEPS, PAIN_TICKS), ('DeepBreath', idle, BREATH_STEPS, BREATH_TICKS)]
        report['packs'][slug] = {'slot': slot, 'pokemon': name, 'actions': {}}
        for act, src, steps, ticks in tasks:
            rows, prov = build_action(src, steps)
            v5.export_action(pack, root, act, rows, ticks)
            preview(f'{slug}_{act}', rows, ticks)
            unique = [len({row[f][0].tobytes() for f in range(len(steps))}) for row in rows]
            for row in rows:
                assert row[0][0].tobytes() == row[-1][0].tobytes(), 'loop must close'
            check = run('sprite', pack, 'dungeon')
            assert check['technical_precheck'] == 'PASS', check['errors']
            report['actions'][f'{slug}/{act}'] = {'directions': 8, 'frames': len(steps),
                'unique_drawings_per_direction': unique, 'durations_ticks': ticks,
                'provenance': prov, 'native_sheet': 'Hurt' if act == 'Pain' else 'Idle',
                'state': 'technical_pass'}
            report['packs'][slug]['actions'][act] = {'technical_check': 'PASS'}
        hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in base.glob('*.png')}
        report['packs'][slug]['native_png_sha256'] = hashes
        shutil.copyfile(base/'credits.txt', OUT/f'{slug}_native_credits.txt')
    (OUT/'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    gallery(report)
    print({k: v['unique_drawings_per_direction'][:2] for k, v in report['actions'].items()})


def gallery(report):
    def uri(p): return 'data:image/gif;base64,'+base64.b64encode(p.read_bytes()).decode()
    html = '''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Guilde · Batch V7 Pain/DeepBreath</title><style>body{font:16px system-ui;max-width:1100px;margin:32px auto;padding:0 24px;background:#141d2b;color:#edf4fa}section{padding:22px;background:#232f3c;border-radius:14px;margin:24px 0}img{max-width:100%;image-rendering:pixelated}.note{border-left:3px solid #f4c477;padding:14px}h2{margin:0}</style><h1>Guilde · premier lot des 124 manquantes (V7)</h1><p class="note">Douze cycles (Pain + DeepBreath pour six membres), huit directions. Chaque pixel visible est une copie translatée d'une frame native épinglée (Hurt pour Pain, Idle pour DeepBreath) : aucune anatomie inventée, aucun accessoire masqué, pas de recoloration. États techniques, pas une validation artistique ni runtime.</p>'''
    for key in report['actions']:
        prefix = key.replace('/', '_')
        html += f'<section><h2>{key}</h2><p>Feuille native : {report["actions"][key]["native_sheet"]}</p><img alt="{key}" src="{uri(OUT/"review"/(prefix+"_8directions.gif"))}"></section>'
    (ROOT/'apercu_guilde_actions_v7.html').write_text(html)


if __name__ == '__main__':
    main()
