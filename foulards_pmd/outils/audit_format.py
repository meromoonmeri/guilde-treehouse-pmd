import os, json, sys
from collections import Counter, defaultdict
import xml.etree.ElementTree as ET
from PIL import Image
import numpy as np

SC = "/home/user/sc_tmp/sprite"
rep = {"pokemon": {}, "global": {}}
anim_names = Counter(); copyof = Counter(); fw = Counter(); fh = Counter()
shadow_sizes = Counter(); dir_rows = Counter(); off_colors = Counter()
palette_sizes = []; anim_modes = Counter()

def marker_colors(arr):
    """arr HxWx4 RGBA -> Counter of opaque colors"""
    m = arr[...,3] > 0
    return Counter(map(tuple, arr[m][:, :3].tolist()))

for pid in sorted(os.listdir(SC)):
    d = os.path.join(SC, pid)
    xml = os.path.join(d, "AnimData.xml")
    if not os.path.isfile(xml): continue
    root = ET.parse(xml).getroot()
    ss = root.findtext("ShadowSize"); shadow_sizes[ss] += 1
    info = {"shadow_size": int(ss), "anims": {}, "forms": []}
    for f in sorted(os.listdir(d)):
        if os.path.isdir(os.path.join(d, f)): info["forms"].append(f)
    for a in root.find("Anims"):
        nm = a.findtext("Name"); anim_names[nm] += 1
        co = a.findtext("CopyOf")
        e = {"index": a.findtext("Index"), "copy_of": co}
        if co: copyof[nm] += 1
        else:
            w = int(a.findtext("FrameWidth")); h = int(a.findtext("FrameHeight"))
            fw[w] += 1; fh[h] += 1
            durs = [int(x.text) for x in a.find("Durations")]
            e.update(frame_w=w, frame_h=h, n_frames=len(durs), durations=durs,
                     rush=a.findtext("RushFrame"), hit=a.findtext("HitFrame"),
                     ret=a.findtext("ReturnFrame"))
            ap = os.path.join(d, f"{nm}-Anim.png")
            op = os.path.join(d, f"{nm}-Offsets.png")
            sp = os.path.join(d, f"{nm}-Shadow.png")
            if os.path.isfile(ap):
                im = Image.open(ap); W, H = im.size
                e["sheet"] = [W, H]; e["cols"] = W // w; e["rows"] = H // h
                e["exact_grid"] = (W % w == 0 and H % h == 0)
                e["cols_eq_frames"] = (W // w == len(durs))
                dir_rows[H // h] += 1
                anim_modes[im.mode] += 1
                if im.mode == "P":
                    pal = im.getpalette()
                    palette_sizes.append(len(set(map(tuple, np.array(pal).reshape(-1,3).tolist()))))
                arr = np.array(im.convert("RGBA"))
                e["n_colors"] = len(marker_colors(arr))
            if os.path.isfile(op):
                arr = np.array(Image.open(op).convert("RGBA"))
                c = marker_colors(arr); off_colors.update(c)
                e["offset_colors"] = {str(k): v for k, v in c.most_common()}
            if os.path.isfile(sp):
                arr = np.array(Image.open(sp).convert("RGBA"))
                e["shadow_colors"] = {str(k): v for k, v in marker_colors(arr).most_common()}
        info["anims"][nm] = e
    rep["pokemon"][pid] = info

rep["global"] = {
    "n_pokemon": len(rep["pokemon"]),
    "anim_name_freq": anim_names.most_common(),
    "copyof_freq": copyof.most_common(),
    "frame_widths": sorted(fw.items()),
    "frame_heights": sorted(fh.items()),
    "shadow_size_freq": shadow_sizes.most_common(),
    "direction_row_counts": sorted(dir_rows.items()),
    "offset_marker_colors": [(str(k), v) for k, v in off_colors.most_common(12)],
    "anim_png_modes": anim_modes.most_common(),
    "palette_unique_colors": sorted(Counter(palette_sizes).items()),
}
json.dump(rep, open("/home/user/guilde-treehouse-pmd/foulards_pmd/outils/audit_spritecollab.json","w"), indent=1)
print(json.dumps(rep["global"], indent=1))
