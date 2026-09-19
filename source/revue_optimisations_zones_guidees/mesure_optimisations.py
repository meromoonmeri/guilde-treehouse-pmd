"""Revue : réplique EN MÉMOIRE la sélection de build_zones_guidees.py et mesure
l effet des optimisations proposées. Écrit uniquement dans resultats/. Ne touche jamais sprites/.
Lancer depuis la racine : .venv/bin/python source/revue_optimisations_zones_guidees/mesure_optimisations.py
"""
import sys, json, hashlib, time
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from scipy.ndimage import uniform_filter
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from zones_guidees.native_tools import Bank, ROOT, BASE, CLIFF

OUT = Path(__file__).resolve().parent / 'resultats'; OUT.mkdir(parents=True, exist_ok=True)
W, H = 2048, 1536; GW, GH = 256, 192
bank = Bank()

def rock(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return (r > g + 9) & (r > 90) & (g > 45) & (b < g * 1.15)

def feature(a):
    rgb = a.reshape(-1, 4, 2, 4, 2, 3).mean(axis=(2, 4)).reshape(-1, 48) / 255
    mask = rock(a).reshape(-1, 64).astype(np.float32)
    return np.concatenate([rgb * .45, mask * 1.2], axis=1).astype(np.float32)

# ---- vocabulary, identical to the build script ----
allowed = set(range(57, 93)) | set(range(114, 122)) | set(range(162, 189))
candidates = []; refs = []; by_coord = {}; by_pixels = {}
grass0 = bank.image(bank.get(BASE, 0, 80))
for (x, y), raw in sorted(bank.sources[CLIFF].items()):
    if x not in allowed or y < (26 if x < 93 else 38 if x >= 162 else 54): continue
    if raw.getbbox() is None: continue
    gid = bank.get(CLIFF, x, y); img = Image.alpha_composite(grass0, bank.image(gid))
    rgb = np.asarray(img)[:, :, :3].astype(np.float32)
    if not rock(rgb).any(): continue
    sig = raw.tobytes()
    if sig not in by_pixels:
        by_pixels[sig] = len(refs); candidates.append(rgb); refs.append((x, y, gid))
    by_coord[x, y] = by_pixels[sig]
C = np.stack(candidates); MASK = rock(C); TREE = cKDTree(feature(C))
print('vocabulary:', len(C), 'distinct tiles')

# native adjacency pairs (by candidate index) present in the Métano cliff layer, for the audit metric
coord_to_ci = dict(by_coord)
native_h = set(); native_v = set()
for (x, y), ci in coord_to_ci.items():
    if (x + 1, y) in coord_to_ci: native_h.add((ci, coord_to_ci[x + 1, y]))
    if (x, y + 1) in coord_to_ci: native_v.add((ci, coord_to_ci[x, y + 1]))

def load_zone(z):
    p = ROOT / f'source/zones_guidees/generateur_{z:02}.png'
    guide = Image.open(p).convert('RGB')
    resized = np.asarray(guide.resize((W, H), Image.Resampling.NEAREST)).astype(np.float32)
    patches = resized.reshape(GH, 8, GW, 8, 3).transpose(0, 2, 1, 3, 4).reshape(-1, 8, 8, 3)
    fractions = rock(patches).mean(axis=(1, 2)); active = np.flatnonzero(fractions >= 2 / 64)
    m = rock(patches)
    blue = (patches[:, :, :, 2] * m).mean(axis=(1, 2)).reshape(GH, GW)
    green = (patches[:, :, :, 1] * m).mean(axis=(1, 2)).reshape(GH, GW)
    tone = uniform_filter(blue, size=(5, 3)) / (uniform_filter(green, size=(5, 3)) + 1e-6)
    _, nearest = TREE.query(feature(patches[active]), k=min(20, len(C)), workers=1)
    return patches, fractions, active, tone, nearest

def interior_choice(i, tone, mode, zname):
    ratio = tone[i // GW, i % GW]
    if mode == 'baseline':
        sx = 85 if ratio > .80 else 86 if ratio > .70 else 92 if ratio > .64 else 114 + (i % GW) % 8
    elif mode == 'hash':      # Problème 3 as proposed
        seed = int(hashlib.md5(f'{i}_{zname}'.encode()).hexdigest()[:8], 16)
        sx = [85, 86, 87, 92][seed % 4]
    elif mode == 'module':    # contiguous native run, source order preserved
        sx = 85 + (i % GW) % 7 if ratio > .64 else 114 + (i % GW) % 8
    return by_coord[(sx, 59 + (i // GW) % 6)]

def select(zone, edge_w=.10, dirs=2, passes=1, interior='baseline', zname='z'):
    patches, fractions, active, tone, nearest = zone
    chosen = np.full(GW * GH, -1, dtype=np.int32)
    terms = []  # (color, mask, edge) of the winning option, first pass, boundary cells
    is_int = np.zeros(GW * GH, bool)
    for p in range(passes):
        changed = 0
        for at, i in enumerate(active):
            if fractions[i] >= .95:
                ci = interior_choice(i, tone, interior, zname); chosen[i] = ci; is_int[i] = True; continue
            options = list(nearest[at]); neighbors = []
            cand = [(i - 1, 'L')] if i % GW else []
            cand += [(i - GW, 'U')] if i >= GW else []
            if dirs == 4:
                cand += [(i + 1, 'R')] if (i + 1) % GW else []
                cand += [(i + GW, 'D')] if i + GW < GW * GH else []
            for prev, side in cand:
                ci = chosen[prev]
                if ci >= 0:
                    sx, sy, _ = refs[ci]
                    sug = {'L': (sx + 1, sy), 'U': (sx, sy + 1), 'R': (sx - 1, sy), 'D': (sx, sy - 1)}[side]
                    s = by_coord.get(sug)
                    if s is not None: options.append(s)
                    neighbors.append((side, ci))
            options = np.array(sorted(set(options))); a = C[options]; target = patches[i]
            col = ((a - target) ** 2).mean(axis=(1, 2, 3)) / (255 ** 2) * .5
            msk = ((MASK[options] != rock(target)).mean(axis=(1, 2))) * 1.4
            edg = np.zeros(len(options))
            for side, ci in neighbors:
                if side == 'L': e = a[:, :, 0, :] - C[ci][:, -1, :]
                elif side == 'U': e = a[:, 0, :, :] - C[ci][-1, :, :]
                elif side == 'R': e = a[:, :, -1, :] - C[ci][:, 0, :]
                else: e = a[:, -1, :, :] - C[ci][0, :, :]
                edg += (e ** 2).mean(axis=(1, 2)) / (255 ** 2) * edge_w
            k = int(np.argmin(col + msk + edg)); ci = int(options[k])
            if p == 0: terms.append((col[k], msk[k], edg[k]))
            if chosen[i] != ci: changed += 1
            chosen[i] = ci
        if passes > 1: print(f'    pass {p + 1}: {changed} cells changed')
    return chosen, is_int, np.array(terms)

def metrics(chosen, is_int, zone):
    patches, fractions, active, tone, nearest = zone
    placed = chosen >= 0
    res = {}
    for name, step, nat in [('h', 1, native_h), ('v', GW, native_v)]:
        idx = np.flatnonzero(placed)
        idx = idx[(idx % GW < GW - 1)] if step == 1 else idx[idx < GW * (GH - 1)]
        j = idx + step; ok = placed[j]; idx, j = idx[ok], j[ok]
        A = C[chosen[idx]]; B = C[chosen[j]]
        mse = ((A[:, :, -1, :] - B[:, :, 0, :]) ** 2).mean(axis=(1, 2)) if step == 1 else ((A[:, -1, :, :] - B[:, 0, :, :]) ** 2).mean(axis=(1, 2))
        both_int = is_int[idx] & is_int[j]
        pairs = set(zip(chosen[idx].tolist(), chosen[j].tolist()))
        absent = sum(1 for pr in zip(chosen[idx].tolist(), chosen[j].tolist()) if pr not in nat) / len(idx)
        res[name] = dict(n=int(len(idx)), mse_mean=float(mse.mean()), mse_p90=float(np.percentile(mse, 90)),
                         pct_over_500=float((mse > 500).mean() * 100),
                         interior_mse=float(mse[both_int].mean()) if both_int.any() else None,
                         boundary_mse=float(mse[~both_int].mean()),
                         pairs_absent_from_native_pct=float(absent * 100))
    # fidelity to the guide (boundary cells only; interiors are pattern-driven)
    b = active[fractions[active] < .95]
    res['boundary_mask_err'] = float((MASK[chosen[b]] != rock(patches[b])).mean())
    res['boundary_color_mse'] = float(((C[chosen[b]] - patches[b]) ** 2).mean())
    return res

def render_crop(chosen, box, path, scale=3):
    x0, y0, x1, y1 = box
    im = Image.new('RGBA', ((x1 - x0) * 8, (y1 - y0) * 8), (0, 0, 0, 0))
    for y in range(y0, y1):
        for x in range(x0, x1):
            i = y * GW + x; ci = chosen[i]
            base = bank.image(bank.get(BASE, x % 16, 80 + y % 16))
            im.alpha_composite(base, ((x - x0) * 8, (y - y0) * 8))
            if ci >= 0: im.alpha_composite(bank.image(refs[ci][2]), ((x - x0) * 8, (y - y0) * 8))
    im.resize((im.width * scale, im.height * scale), Image.NEAREST).save(path)

if __name__ == '__main__':
    report = {}
    for z, zname in [(1, '01_cirque'), (2, '02_terrasses')]:
        zone = load_zone(z); report[zname] = {}
        print(f'\n=== {zname}: {len(zone[2])} active cells ===')
        variants = {
            'baseline (w=.10, L+U)': dict(edge_w=.10, dirs=2, passes=1, interior='baseline'),
            'P1a edge w=.25 (L+U)': dict(edge_w=.25, dirs=2, passes=1, interior='baseline'),
            'P1b 4-dir ICM w=.25 x3': dict(edge_w=.25, dirs=4, passes=3, interior='baseline'),
            'P3 hash [85,86,87,92]': dict(edge_w=.10, dirs=2, passes=1, interior='hash'),
            'ALT module 85..91 in order': dict(edge_w=.10, dirs=2, passes=1, interior='module'),
            'ALT module + 4-dir ICM w=.25 x3': dict(edge_w=.25, dirs=4, passes=3, interior='module'),
        }
        base = None
        for name, kw in variants.items():
            t = time.time(); chosen, is_int, terms = select(zone, zname=zname, **kw); dt = time.time() - t
            m = metrics(chosen, is_int, zone); m['seconds'] = round(dt, 1)
            if base is None: base = chosen
            m['cells_changed_vs_baseline'] = int((chosen != base).sum())
            if name.startswith('baseline'):
                m['winning_terms_median'] = dict(color=float(np.median(terms[:, 0])), mask=float(np.median(terms[:, 1])), edge=float(np.median(terms[:, 2])))
                m['winning_terms_p90'] = dict(color=float(np.percentile(terms[:, 0], 90)), mask=float(np.percentile(terms[:, 1], 90)), edge=float(np.percentile(terms[:, 2], 90)))
            report[zname][name] = m
            print(f'  {name:36s} h-seam mean {m["h"]["mse_mean"]:7.1f} (int {m["h"]["interior_mse"] or 0:7.1f} / bnd {m["h"]["boundary_mse"]:6.1f}) '
                  f'v-seam mean {m["v"]["mse_mean"]:6.1f}  >500: h {m["h"]["pct_over_500"]:4.1f}% v {m["v"]["pct_over_500"]:4.1f}%  '
                  f'absent-native h {m["h"]["pairs_absent_from_native_pct"]:4.1f}%  mask-err {m["boundary_mask_err"]:.3f}  changed {m["cells_changed_vs_baseline"]:5d}  {dt:4.1f}s')
            if z == 1 and name in ('baseline (w=.10, L+U)', 'P3 hash [85,86,87,92]', 'ALT module 85..91 in order', 'P1b 4-dir ICM w=.25 x3'):
                # crop around a dense interior region + its boundary: find the densest 48x32-cell window
                fr = zone[1].reshape(GH, GW); best = None
                for yy in range(0, GH - 32, 4):
                    for xx in range(0, GW - 48, 4):
                        s = (fr[yy:yy + 32, xx:xx + 48] >= .95).mean()
                        if best is None or s > best[0]: best = (s, xx, yy)
                _, xx, yy = best
                tag = name.split(' ')[0]
                render_crop(chosen, (xx, yy, xx + 48, yy + 32), OUT / f'crop_{tag}.png')
                print(f'    crop rendered at cells ({xx},{yy}) -> crop_{tag}.png')
        # what a MUCH larger seam weight would do (for the record: it degrades the mask, interiors stay untouched)
        fr = zone[1]; act = zone[2]
        report[zname]['_interior_share_pct'] = round(float((fr[act] >= .95).mean() * 100), 1)
        for w in (1.0, 3.0):
            ch, ii, _ = select(zone, edge_w=w, dirs=4, passes=3, interior='baseline', zname=zname)
            m = metrics(ch, ii, zone); m['cells_changed_vs_baseline'] = int((ch != base).sum())
            report[zname][f'P1c 4-dir ICM w={w} x3'] = m
            print(f'  {"P1c 4-dir ICM w=" + str(w) + " x3":36s} h-seam mean {m["h"]["mse_mean"]:7.1f} (bnd {m["h"]["boundary_mse"]:6.1f})  mask-err {m["boundary_mask_err"]:.3f}')
    (OUT / 'report.json').write_text(json.dumps(report, indent=2))
    # montage of the four crops (zone 01, densest 48x32-cell window)
    from PIL import ImageDraw
    names = ['baseline', 'P1b', 'P3', 'ALT']; ims = [Image.open(OUT / f'crop_{n}.png') for n in names]
    w, h = ims[0].size; S = Image.new('RGB', (w * 2 + 30, h * 2 + 60), (20, 20, 20)); d = ImageDraw.Draw(S)
    labels = {'baseline': 'baseline actuel (colonnes 85/86/92 repetees + bloc 114-121)', 'P1b': 'P1b : 4 directions ICM, poids .25',
              'P3': 'P3 : hash sur [85,86,87,92]', 'ALT': 'ALT : module contigu 85..91 dans l ordre source'}
    for k, (n, im) in enumerate(zip(names, ims)):
        x = (k % 2) * (w + 30); y = (k // 2) * (h + 30) + 20; S.paste(im, (x, y)); d.text((x, y - 14), labels[n], fill=(255, 255, 0))
    S.save(OUT / 'comparaison_crops.png')
    # evidence renders of the source sheet: x ranges are MAP positions of the Metano cliff layer
    from zones_guidees.native_tools import straight
    def sheet(x0, x1, y0, y1, scale, names):
        im = Image.new('RGBA', ((x1 - x0) * 8, (y1 - y0) * 8), (255, 0, 255, 255))
        for name in names:
            for (x, y), raw in bank.sources[name].items():
                if x0 <= x < x1 and y0 <= y < y1: im.alpha_composite(straight(raw), ((x - x0) * 8, (y - y0) * 8))
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        cv = Image.new('RGB', (im.width, im.height + 28), (20, 20, 20)); cv.paste(im, (0, 28)); dd = ImageDraw.Draw(cv)
        for x in range(x0, x1):
            if x % 4 == 0: dd.text(((x - x0) * 8 * scale, 2), str(x), fill=(255, 255, 0))
        return cv
    sheet(55, 125, 20, 68, 3, [BASE, CLIFF]).save(OUT / 'plage_93_113_escaliers_grotte.png')
    a = sheet(83, 94, 57, 67, 6, [CLIFF]); c = sheet(113, 123, 57, 67, 6, [CLIFF])
    big = Image.new('RGB', (a.width + c.width + 40, max(a.height, c.height)), (20, 20, 20)); big.paste(a, (0, 0)); big.paste(c, (a.width + 40, 0))
    big.save(OUT / 'colonnes_interieur_85_92_114_121.png')
    print('\nreport ->', OUT / 'report.json')
