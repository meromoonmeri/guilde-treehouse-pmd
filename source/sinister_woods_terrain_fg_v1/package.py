#!/usr/bin/env python3
"""Run tests then pack the terrain+foreground variant.

NOTE (merge): scripts moved from source/sinister_woods_gen_v1/ to
source/sinister_woods_terrain_fg_v1/ to preserve both sibling pipelines.
Outputs (renders/sinister_woods_gen_v1/{bruts,work,layers}) unchanged.
"""
import os, subprocess, sys, zipfile
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "source", "sinister_woods_terrain_fg_v1")
subprocess.run([sys.executable, os.path.join(SRC, "test_build.py")], check=True, cwd=ROOT)
zpath = os.path.join(ROOT, "renders", "sinister_woods_v1_terrain_fg_pack.zip")
base = os.path.join(ROOT, "renders", "sinister_woods_gen_v1")
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
    for dirpath, _, files in os.walk(base):
        for f in sorted(files):
            if f.startswith("_small") or f.startswith("_zoom") or f.startswith("_view") or f.startswith("_holes"):
                continue
            p = os.path.join(dirpath, f)
            z.write(p, os.path.relpath(p, os.path.join(ROOT, "renders")))
print("OK ->", zpath, os.path.getsize(zpath), "bytes")
