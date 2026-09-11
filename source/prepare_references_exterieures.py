#!/usr/bin/env python3
"""Prépare les natives complètes à partir des références ajoutées le 11-09-2026.

Le but de cette étape est de conserver les layouts de référence avant leur
séparation technique. Elle ne dessine pas une nouvelle carte :
- la planche 232024 est recadrée sur un seul panneau de cascades ;
- les deux images côtières sont réduites par un facteur entier ;
- seule la nuit de la planche de cascades est une palette dédiée appliquée à
  la même géométrie, avec un petit ciel étoilé local.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ENTREES = ROOT / "source" / "references_exterieures" / "entrees"
NATIVES = ROOT / "source" / "references_exterieures" / "natives"

CASCADE_CROP = (1, 0, 297, 224)  # un panneau, sans séparateur noir ni plan magenta
CASCADE_SIZE = (592, 448)       # x2, grille 8 px
CAP_SIZE = (960, 600)           # 3840×2400 ÷ 4, grille 8 px


def save(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGBA").save(path, optimize=True)


def night_cascade(day: Image.Image) -> Image.Image:
    """Décline le panneau de jour sans déplacer aucun élément du layout."""
    pixels = np.asarray(day.convert("RGBA")).copy()
    rgb = pixels[:, :, :3].astype(np.float32)
    # Transformation chromatique fixe, plus froide mais laissant l'eau lisible.
    rgb = rgb * np.array([0.34, 0.41, 0.66], dtype=np.float32) + np.array([3, 6, 16], dtype=np.float32)
    water = (pixels[:, :, 2] > pixels[:, :, 0] * 1.15) & (pixels[:, :, 1] > pixels[:, :, 0] * 1.06)
    rgb[water] = np.minimum(255, rgb[water] + np.array([0, 10, 18], dtype=np.float32))
    pixels[:, :, :3] = np.rint(rgb).clip(0, 255).astype(np.uint8)
    image = Image.fromarray(pixels, "RGBA")
    draw = ImageDraw.Draw(image)
    # Astres ajoutés au fond, sans toucher aux éléments de terrain du layout.
    for x, y, r in [(round(image.width*f), y, r) for f, y, r in
                    [(.10, 50, 2), (.16, 89, 1), (.22, 31, 1), (.39, 50, 2),
                     (.73, 42, 1), (.85, 83, 1), (.92, 39, 2)]]:
        draw.rectangle((x-r, y-r, x+r, y+r), fill=(218, 235, 255, 255))
    return image


def night_prairie(day: Image.Image) -> Image.Image:
    """Variante nocturne du même layout de prairie maritime, sans déplacement."""
    pixels = np.asarray(day.convert("RGBA")).copy()
    rgb = pixels[:, :, :3].astype(np.float32)
    rgb = rgb * np.array([0.31, 0.39, 0.61], dtype=np.float32) + np.array([2, 6, 16], dtype=np.float32)
    pixels[:, :, :3] = np.rint(rgb).clip(0, 255).astype(np.uint8)
    image = Image.fromarray(pixels, "RGBA")
    draw = ImageDraw.Draw(image)
    for x, y in [(38, 28), (86, 63), (154, 39), (218, 74), (298, 32), (372, 58), (453, 24)]:
        draw.rectangle((x, y, x + 2, y + 2), fill=(218, 235, 255, 255))
    return image


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare() -> dict:
    NATIVES.mkdir(parents=True, exist_ok=True)

    with Image.open(ENTREES / "232024.png") as original:
        panel = original.convert("RGBA").crop(CASCADE_CROP)
    assert panel.getchannel("A").getextrema() == (255, 255)
    save(panel, ENTREES / "cascade_reference_recadree.png")
    cascade = panel.resize(CASCADE_SIZE, Image.Resampling.NEAREST)
    save(cascade, NATIVES / "cascades_jour.png")
    save(night_cascade(cascade), NATIVES / "cascades_nuit.png")

    # Le GIF est une référence de layout/mouvement ; la planche rend ses quatre
    # phases consultables sans traiter le GIF comme un calque de production.
    with Image.open(ENTREES / "2cwdrrs469f61.gif") as animated:
        assert animated.n_frames == 4 and animated.size == (504, 504)
        animated.seek(0)
        prairie = animated.convert("RGBA").copy()
        board = Image.new("RGBA", (480, 420), (19, 23, 42, 255))
        draw = ImageDraw.Draw(board)
        for index in range(animated.n_frames):
            animated.seek(index)
            frame = animated.convert("RGBA")
            frame.thumbnail((240, 180), Image.Resampling.NEAREST)
            x, y = (index % 2) * 240, (index // 2) * 210
            board.alpha_composite(frame, (x + (240 - frame.width) // 2, y + 24))
            draw.text((x + 8, y + 6), f"Image {index}", fill=(246, 239, 216, 255))
    save(board, ENTREES / "animation_reference_planche.png")
    save(prairie, NATIVES / "prairie_maritime_jour.png")
    save(night_prairie(prairie), NATIVES / "prairie_maritime_nuit.png")

    for mode, filename in (("jour", "falaise_cotiere_jour_reference.jpg"), ("nuit", "falaise_cotiere_nuit_reference.png")):
        with Image.open(ENTREES / filename) as original:
            image = original.convert("RGBA")
        assert image.size == (3840, 2400), f"Référence côtière inattendue: {image.size}"
        native = image.resize(CAP_SIZE, Image.Resampling.NEAREST)
        assert native.getchannel("A").getextrema() == (255, 255)
        save(native, NATIVES / f"cap_cotier_{mode}.png")

    report = {
        "entrees": {
            path.name: {"sha256": digest(path), "octets": path.stat().st_size}
            for path in sorted(ENTREES.glob("*")) if path.is_file()
        },
        "natives": {
            path.name: {"sha256": digest(path), "dimensions": list(Image.open(path).size)}
            for path in sorted(NATIVES.glob("*.png"))
        },
        "cascade": {"recadrage_source_px": list(CASCADE_CROP), "dimensions": list(CASCADE_SIZE)},
        "prairie_maritime": {"image_source": 0, "dimensions": [504, 504], "animation_source": 4},
        "cap_cotier": {"reduction": "3840×2400 / 4 au plus proche voisin", "dimensions": list(CAP_SIZE)},
        "nuit_cascades": "palette fixe et astres locaux, géométrie de jour inchangée",
        "nuit_prairie_maritime": "palette fixe et étoiles locales, géométrie de jour inchangée",
    }
    (ROOT / "source" / "references_exterieures" / "provenance.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("Natives prêtes : cascade, prairie maritime et cap côtier, tous en jour/nuit.")
    return report


if __name__ == "__main__":
    prepare()
