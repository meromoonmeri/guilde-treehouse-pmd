"""Echantillonnage strict d'une reference canonique -> pack de configuration generateur.

Sorties par reference (dans packs/<nom>/) :
  palette.png      : pastilles triees par frequence avec codes hex
  patch_board.png  : planche de patchs de textures par couleur (extraits originaux)
  patch_*.png      : patchs individuels + coordonnees source
  samples.json     : couleurs hex + comptes + rects + mesures d'echelle
  prompt.txt       : prompt strict pret a l'emploi (palette verrouillee + contraintes)

Usage :
  .venv/bin/python source/reference_sampler/sample.py REF.png packs/<nom> --layout "..." --title "..."
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd


def hexof(rgb):
    return '#%02X%02X%02X' % tuple(int(v) for v in rgb)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('ref')
    ap.add_argument('out')
    ap.add_argument('--layout', required=True)
    ap.add_argument('--title', required=True)
    ap.add_argument('--colors', type=int, default=20)
    ap.add_argument('--min_frac', type=float, default=0.004)
    a = ap.parse_args()

    R = Path(__file__).resolve().parents[2]
    ref = Image.open(R / a.ref).convert('RGB')
    W, H = ref.size
    arr = np.array(ref)
    out = R / a.out
    out.mkdir(parents=True, exist_ok=True)

    q = ref.quantize(colors=a.colors, method=Image.MEDIANCUT)
    pal = np.array(q.getpalette()[:a.colors * 3]).reshape(-1, 3)
    lab = np.array(q)
    counts = np.bincount(lab.ravel(), minlength=a.colors)
    total = counts.sum()
    order = sorted(range(a.colors), key=lambda i: -counts[i])
    kept = [i for i in order if counts[i] / total >= a.min_frac]

    # Patch exemple par couleur : plus gros composant connexe -> bbox paddee
    patches = []
    for i in kept:
        m = lab == i
        blobs, n = nd.label(m)
        if n == 0:
            continue
        sizes = np.bincount(blobs.ravel())
        sizes[0] = 0
        b = int(sizes.argmax())
        yy, xx = np.where(blobs == b)
        x0, y0 = max(0, int(xx.min()) - 6), max(0, int(yy.min()) - 6)
        x1, y1 = min(W, int(xx.max()) + 7), min(H, int(yy.max()) + 7)
        if x1 - x0 < 16 or y1 - y0 < 16:  # trop petit : fenetre elargie autour du centroide
            cx, cy = int(xx.mean()), int(yy.mean())
            x0, y0 = max(0, cx - 16), max(0, cy - 16)
            x1, y1 = min(W, x0 + 32), min(H, y0 + 32)
        fn = f'patch_{len(patches):02d}_{hexof(pal[i]).lstrip("#")}.png'
        ref.crop((x0, y0, x1, y1)).save(out / fn)
        # grain : taille mediane des taches de cette couleur
        patches.append(dict(color=hexof(pal[i]), count=int(counts[i]),
                            frac=round(float(counts[i] / total), 4),
                            rect=[x0, y0, x1, y1], file=fn))

    # palette.png
    sw, sh, cols = 64, 64, 5
    rows = (len(patches) + cols - 1) // cols
    board = Image.new('RGB', (cols * (sw + 8) + 8, rows * (sh + 20) + 8), (24, 24, 24))
    d = ImageDraw.Draw(board)
    for k, p in enumerate(patches):
        x, y = 8 + (k % cols) * (sw + 8), 8 + (k // cols) * (sh + 20)
        rgb = tuple(int(p['color'][i:i + 2], 16) for i in (1, 3, 5))
        d.rectangle([x, y, x + sw, y + sh], fill=rgb, outline=(255, 255, 255))
        d.text((x, y + sh + 2), f"{p['color']} {p['frac'] * 100:.1f}%", fill=(255, 255, 255))
    board.save(out / 'palette.png')

    # patch_board.png : patchs + etiquettes
    tw, th = 96, 96
    pb = Image.new('RGB', (cols * (tw + 8) + 8, rows * (th + 20) + 8), (24, 24, 24))
    d = ImageDraw.Draw(pb)
    for k, p in enumerate(patches):
        x, y = 8 + (k % cols) * (tw + 8), 8 + (k // cols) * (th + 20)
        im = Image.open(out / p['file']).convert('RGB')
        im.thumbnail((tw, th), Image.NEAREST)
        pb.paste(im, (x, y))
        d.text((x, y + th + 2), f"{p['color']} {p['rect'][0]},{p['rect'][1]}", fill=(255, 255, 255))
    pb.save(out / 'patch_board.png')

    hexes = [p['color'] for p in patches]
    samples = dict(reference=a.ref, size=[W, H], title=a.title, layout=a.layout,
                   colors=patches, palette_hex=hexes,
                   scale_note=f'reference {W}x{H}, grille moteur 8px ; reproduire les proportions (pas de zoom global)')
    (out / 'samples.json').write_text(json.dumps(samples, indent=1), encoding='utf-8')

    prompt = (
        f"Strict Pokemon Mystery Dungeon Explorers of Sky pixel-art map background "
        f"({a.title}). Layout: {a.layout}. "
        f"LOCKED PALETTE — use ONLY these {len(hexes)} reference colors, sampled from the canonical reference, "
        f"no invented hues: {', '.join(hexes[:16])}. "
        f"Match the texture patches of the second reference image exactly in grain and contrast "
        f"(flat crisp square pixels, same dither density, no blur, no smooth gradients). "
        f"Native tile scale (PMDO 8px grid), same proportions as the first reference, portrait orientation. "
        f"Solid flat magenta #FF00FF background filling every empty area. "
        f"No sky, no clouds, no characters, no text, no watermark."
    )
    (out / 'prompt.txt').write_text(prompt, encoding='utf-8')
    print('OK', a.out, len(patches), 'couleurs,', out.name)


if __name__ == '__main__':
    main()
