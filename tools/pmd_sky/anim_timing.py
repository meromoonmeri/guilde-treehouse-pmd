"""Timings RÉELS des animations d'un fond PMD Sky (ce que le port perd).
Usage : python tools/pmd_sky/anim_timing.py <dossier MAP_BG> <code> [<code> ...]  (ex. t01p02a d17p31a)
Requiert skytemple-files. Lit :
- BPL : palette animation (bpl.animation_specs : duration_per_frame + number_of_frames par palette 11-16) ;
- BPA : animation de tuiles (bpa.frame_info[i].duration_per_frame).
Les durées sont en frames jeu (60 fps) ; PMDO FrameLength est aussi en frames 60 fps -> copie 1:1.
"""
import sys, json, glob, os
from skytemple_files.common.types.file_types import FileType
base = sys.argv[1]; res = {}
for code in sys.argv[2:]:
    r = {"palette": [], "bpa": []}
    bpl = FileType.BPL.deserialize(open(f"{base}/{code}.bpl", "rb").read())
    if bpl.has_palette_animation:
        for i, s in enumerate(bpl.animation_specs):
            if s.number_of_frames:
                r["palette"].append({"ligne_palette": 10 + i, "frames": s.number_of_frames, "duree_frames_60fps": s.duration_per_frame,
                                     "ms": round(s.duration_per_frame * 1000 / 60, 1), "cycle_ms": round(s.number_of_frames * s.duration_per_frame * 1000 / 60)})
    for p in sorted(glob.glob(f"{base}/{code}[0-9].bpa")):
        b = FileType.BPA.deserialize(open(p, "rb").read())
        d = sorted({fi.duration_per_frame for fi in b.frame_info})
        r["bpa"].append({"fichier": os.path.basename(p), "slot": int(p[-5]) - 1, "tuiles_par_frame": b.number_of_tiles,
                         "frames": b.number_of_frames, "durees_frames_60fps": d, "ms": [round(x * 1000 / 60, 1) for x in d]})
    res[code] = r
print(json.dumps(res, ensure_ascii=False, indent=1))
