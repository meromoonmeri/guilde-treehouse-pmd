"""Contrôles reproductibles de la zone glaciale / grotte boréale V1.

Ces contrôles valident les fichiers et la cohérence des calques; ils ne
remplacent pas la revue artistique, l'import ou le test runtime PMDO.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

from build import (
    AURORA_BRUT,
    FRAME_MS,
    FRAMES,
    GRID,
    H,
    OUT,
    ROOT,
    SKY_BRUT,
    SKY_SOURCE_H,
    TERRAIN_BRUT,
    TERRAIN_SOURCE_H,
    TERRAIN_Y,
    W,
    compose,
    deform_indices,
    extract_aurora,
    full_canvas,
    indexed_aurora,
    palette_for_frame,
    render_indexed,
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def alpha_composite(images: list[Image.Image]) -> Image.Image:
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for image in images:
        canvas.alpha_composite(image)
    return canvas


def check(condition: bool, label: str, checks: list[dict], **details: object) -> None:
    entry = {"name": label, "pass": bool(condition), **details}
    checks.append(entry)
    if not condition:
        raise AssertionError(f"Échec : {label} · {details}")


def check_js_syntax(viewer: Path) -> dict:
    text = viewer.read_text(encoding="utf-8")
    scripts = re.findall(r"<script>(.*?)</script>", text, re.DOTALL | re.IGNORECASE)
    if not scripts:
        raise AssertionError("Aucun script dans le viewer")
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
        handle.write("\n".join(scripts))
        temporary = Path(handle.name)
    try:
        completed = subprocess.run(["node", "--check", str(temporary)], capture_output=True, text=True, check=False)
        if completed.returncode:
            raise AssertionError(completed.stderr.strip() or completed.stdout.strip())
        return {"node": "--check PASS"}
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    checks: list[dict] = []
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    check(manifest["canvas_px"] == [W, H], "canevas déclaré", checks, actual=manifest["canvas_px"])
    check(W % GRID == 0 and H % GRID == 0, "canevas divisible par la grille", checks, grid=GRID, cells=[W // GRID, H // GRID])
    check(manifest["grid_cells"] == [W // GRID, H // GRID], "cellules déclarées", checks, actual=manifest["grid_cells"])

    expected_sources = {TERRAIN_BRUT, SKY_BRUT, AURORA_BRUT}
    seen_sources = {ROOT / item["file"] for item in manifest["sources"]}
    check(seen_sources == expected_sources, "provenance des trois bruts", checks, sources=sorted(str(p.relative_to(ROOT)) for p in seen_sources))
    for item in manifest["sources"]:
        source = ROOT / item["file"]
        check(item["sha256"] == digest(source), f"hash brut {source.name}", checks, sha256=item["sha256"])

    static_paths = [
        OUT / "calques" / "ZoneGlacialeV1_00_ciel_nuit.png",
        OUT / "calques" / "ZoneGlacialeV1_00b_etoiles.png",
        OUT / "calques" / "ZoneGlacialeV1_01_sol_reconstitue.png",
        OUT / "calques" / "ZoneGlacialeV1_02_sol_vallee_visible.png",
        OUT / "calques" / "ZoneGlacialeV1_03_chemin_sud_nord.png",
        OUT / "calques" / "ZoneGlacialeV1_04_falaise_nord_glace.png",
        OUT / "calques" / "ZoneGlacialeV1_05_falaises_laterales.png",
        OUT / "calques" / "ZoneGlacialeV1_06_encadrement_grotte.png",
        OUT / "calques" / "ZoneGlacialeV1_07_obscurite_grotte.png",
        OUT / "calques" / "ZoneGlacialeV1_08_cristaux_rochers_avant.png",
    ]
    for path in static_paths:
        image = Image.open(path)
        check(image.size == (W, H), f"dimension {path.name}", checks, size=list(image.size))

    frame_paths = [OUT / "animation" / "frames" / f"ZoneGlacialeV1_Aurore_{frame:02d}.png" for frame in range(FRAMES)]
    check(all(path.is_file() for path in frame_paths), "les 16 calques d'aurore existent", checks, frames=len(frame_paths))
    frame_images = [load(path) for path in frame_paths]
    for path, image in zip(frame_paths, frame_images):
        check(image.size == (W, H), f"dimension {path.name}", checks, size=list(image.size))

    # Exactitude des pixels préservés après détourage du terrain. La translation
    # dans le canevas ne modifie pas le RGB de chaque pixel retenu.
    raw_terrain = np.asarray(Image.open(TERRAIN_BRUT).convert("RGB"))[:TERRAIN_SOURCE_H]
    detached = np.asarray(load(OUT / "review" / "terrain_detoure.png"))
    retained = detached[TERRAIN_Y:TERRAIN_Y + TERRAIN_SOURCE_H, :, 3] > 0
    rgb_equal = np.array_equal(detached[TERRAIN_Y:TERRAIN_Y + TERRAIN_SOURCE_H, :, :3][retained], raw_terrain[retained])
    check(rgb_equal, "pixels terrain conservés après détourage", checks, retained_pixels=int(retained.sum()))

    # Les sept plans visibles sont une partition exacte de la composition
    # générée; le sol reconstitué est volontairement une couche sous-jacente.
    semantic_paths = static_paths[3:]
    semantic = alpha_composite([load(path) for path in semantic_paths])
    semantic_arr = np.asarray(semantic)
    detached_arr = np.asarray(load(OUT / "review" / "terrain_detoure.png"))
    check(np.array_equal(semantic_arr, detached_arr), "partition/recomposition terrain exacte", checks, layers=len(semantic_paths))

    # Le calque de chemin est connecté du bord sud au seuil nord; ce test ne
    # transforme explicitement pas cette indication en collision moteur.
    corridor = np.asarray(Image.open(OUT / "masques" / "09_corridor_geometrique_sud_nord.png").convert("L")) > 0
    start = (H - 1, 632)
    goal = (TERRAIN_Y + 348, 632)
    labels, count = ndimage.label(corridor, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.uint8))
    connected = labels[start] != 0 and labels[start] == labels[goal]
    check(connected, "corridor géométrique continu sud→grotte", checks, start=[start[1], start[0]], goal=[goal[1], goal[0]], components=int(count))

    # L'asset indexé et alpha source rendent exactement la frame 0 et la frame
    # 16 virtuelle. La boucle ne dépend pas du GIF/WebP.
    indexed = Image.open(OUT / "animation" / "aurore_indexee.png")
    source_alpha = np.asarray(Image.open(OUT / "animation" / "aurore_alpha.png").convert("L"))
    index_arr = np.asarray(indexed)
    expected_images = []
    for phase in (0, FRAMES):
        warped_index, warped_alpha = deform_indices(index_arr, source_alpha, phase)
        expected_images.append(full_canvas(render_indexed(warped_index, warped_alpha, palette_for_frame(phase))))
    check(np.array_equal(np.asarray(expected_images[0]), np.asarray(frame_images[0])), "frame 0 issue des indices/palette", checks)
    check(np.array_equal(np.asarray(expected_images[0]), np.asarray(expected_images[1])), "fermeture mathématique frame 16 = frame 0", checks)
    alpha0 = np.asarray(frame_images[0])[:, :, 3] > 0
    alpha4 = np.asarray(frame_images[4])[:, :, 3] > 0
    intersection = int((alpha0 & alpha4).sum())
    union = int((alpha0 | alpha4).sum())
    iou = intersection / union if union else 1.0
    check(iou < 0.995, "onde non rigide entre frames 0 et 4", checks, alpha_iou=round(iou, 6))
    check(any(not np.array_equal(np.asarray(frame_images[0]), np.asarray(image)) for image in frame_images[1:]), "animation contient des phases distinctes", checks)
    check(indexed.mode == "P", "aurore source indexée", checks, mode=indexed.mode)
    check(source_alpha.shape == (600, W), "alpha de l'asset auroral aligné", checks, size=[int(source_alpha.shape[1]), int(source_alpha.shape[0])])

    # Aucun fragment de fond magenta ne doit survivre dans les 16 overlays.
    magenta_counts = []
    for image in frame_images:
        arr = np.asarray(image)
        r, g, b, a = np.moveaxis(arr, -1, 0)
        residual = (a > 0) & (r > 220) & (b > 198) & (g < 36) & (np.abs(r.astype(np.int16) - b.astype(np.int16)) < 68)
        magenta_counts.append(int(residual.sum()))
    check(max(magenta_counts) == 0, "aucun magenta de fond dans l'aurore", checks, per_frame=magenta_counts)

    # Recomposition de scène phase 0 : le PNG final est reproductible depuis
    # le ciel, étoiles, overlay et calques, sans fusion cachée.
    composition = alpha_composite([load(path) for path in static_paths[:2]] + [frame_images[0]] + [load(path) for path in static_paths[2:]])
    delivered = load(OUT / "COMPOSITION.png")
    check(np.array_equal(np.asarray(composition), np.asarray(delivered)), "recomposition exacte de la scène phase 0", checks)

    # Les sorties animées ont les 16 phases attendues.
    for path, label in [(OUT / "animation" / "aurore_16frames.webp", "WebP"), (OUT / "review" / "aurore_16frames.gif", "GIF aurore"), (OUT / "review" / "animation_complete.gif", "GIF scène")]:
        with Image.open(path) as animated:
            check(getattr(animated, "n_frames", 1) == FRAMES, f"{label} animé", checks, frames=getattr(animated, "n_frames", 1))

    # ORA éditable : toutes les couches et son mimetype sont présents.
    ora = OUT / "zone_glaciale_grotte_boreale_v1.ora"
    with zipfile.ZipFile(ora) as archive:
        names = archive.namelist()
        stack = archive.read("stack.xml")
        check(names[0] == "mimetype" and archive.read("mimetype") == b"image/openraster", "ORA mimetype", checks)
        check(sum(1 for name in names if name.startswith("data/layer")) == 11, "ORA contient 11 calques", checks)
        check(b"Aurore frame 00" in stack and b"profondeur de grotte" in stack, "ORA étiquette ses calques", checks)

    viewer = ROOT / "apercu_zone_glaciale_grotte_boreale_v1.html"
    viewer_text = viewer.read_text(encoding="utf-8")
    check("__DATA__" not in viewer_text and "ZoneGlacialeV1_Aurore" not in viewer_text, "viewer autonome embarqué", checks)
    js_info = check_js_syntax(viewer)
    check(True, "syntaxe JavaScript viewer", checks, **js_info)

    report = {
        "status": "PASS",
        "canvas_px": [W, H],
        "grid_px": GRID,
        "animation": {"frames": FRAMES, "frame_ms": FRAME_MS, "duration_s": FRAMES * FRAME_MS / 1000},
        "checks": checks,
        "scope": "contrôles de fichiers et de recomposition; ni revue artistique ni import/runtime PMDO",
    }
    (OUT / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS — {len(checks)} contrôles : {OUT.relative_to(ROOT)}/verification.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
