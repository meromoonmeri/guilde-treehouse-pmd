#!/usr/bin/env python3
"""Prépare les natives générées depuis les références ajoutées le 11-09-2026.

Les entrées de ``entrees/`` servent uniquement de guides de layout, de palette
et de lecture PMD. Les six images de ``generation/`` sont les rendus créés par
le générateur d'images pour cette livraison. Cette étape ne recontacte aucun
service : elle fixe leurs dimensions de production par un redimensionnement
entier au plus proche voisin, sans masque ni collage de fragments.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ENTREES = ROOT / "source" / "references_exterieures" / "entrees"
GENERATED = ROOT / "source" / "references_exterieures" / "generation"
NATIVES = ROOT / "source" / "references_exterieures" / "natives"

# Les deux rendus paysage sortent en 1376×768 et sont divisés par deux. Le
# sanctuaire de cascades est volontairement un layout vertical, 816×1300 / 2.
GENERATED_OUTPUTS = (
    ("cascades_jour.png", "cascades_jour_generee.png", (816, 1300), (408, 648)),
    ("cascades_nuit.png", "cascades_nuit_generee.png", (816, 1300), (408, 648)),
    ("prairie_maritime_jour.png", "prairie_maritime_jour_generee.png", (1376, 768), (688, 384)),
    ("prairie_maritime_nuit.png", "prairie_maritime_nuit_generee.png", (1376, 768), (688, 384)),
    ("cap_cotier_jour.png", "cap_cotier_jour_generee.png", (1376, 768), (688, 384)),
    ("cap_cotier_nuit.png", "cap_cotier_nuit_generee.png", (1376, 768), (688, 384)),
)
CASCADE_CROP = (1, 0, 297, 224)  # panneau de référence, sans séparateur ni plan magenta


def save(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGBA").save(path, optimize=True)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_guides() -> None:
    """Conserve les deux aides de lecture fabriquées depuis les entrées brutes."""
    with Image.open(ENTREES / "232024.png") as original:
        panel = original.convert("RGBA").crop(CASCADE_CROP)
    save(panel, ENTREES / "cascade_reference_recadree.png")

    with Image.open(ENTREES / "2cwdrrs469f61.gif") as animated:
        assert animated.n_frames == 4 and animated.size == (504, 504)
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


def prepare() -> dict:
    NATIVES.mkdir(parents=True, exist_ok=True)
    prepare_guides()
    generated_report = {}
    for destination, source, source_size, native_size in GENERATED_OUTPUTS:
        path = GENERATED / source
        with Image.open(path) as opened:
            rendered = opened.convert("RGBA")
        assert rendered.size == source_size, f"Taille inattendue : {source} = {rendered.size}, attendu {source_size}"
        assert rendered.getchannel("A").getextrema() == (255, 255), f"Rendu non opaque : {source}"
        native = rendered.resize(native_size, Image.Resampling.NEAREST)
        save(native, NATIVES / destination)
        generated_report[source] = {
            "sha256": digest(path), "dimensions_source": list(source_size),
            "native": destination, "dimensions_native": list(native_size), "reduction": "plus_proche_voisin",
        }

    report = {
        "methode": "generation_image_referencee_puis_normalisation_entierement_reproductible",
        "branche_references": "arena/01a082db-guilde-treehouse-pmd",
        "commits_entrees": {
            "cascade_et_gif": "6cf427cdcc59874411172e57f53fb47011de7941",
            "etang_et_cap": "bc3afc6676d62e1a5d811e129070ed3443162946",
        },
        "entrees": {
            path.name: {"sha256": digest(path), "octets": path.stat().st_size}
            for path in sorted(ENTREES.glob("*")) if path.is_file()
        },
        "generation": generated_report,
        "natives": {
            path.name: {"sha256": digest(path), "dimensions": list(Image.open(path).size)}
            for path in sorted(NATIVES.glob("*.png"))
        },
        "regle_jour_nuit": "Chaque nuit est générée à partir de son rendu jour afin de conserver le même layout ; aucune nuit n'est un filtre runtime.",
        "guide_cascade": {"recadrage_source_px": list(CASCADE_CROP)},
        "guide_gif": {"frames": 4, "dimensions": [504, 504]},
    }
    (ROOT / "source" / "references_exterieures" / "provenance.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("Natives générées prêtes : cascades, prairie maritime et cap côtier, en jour/nuit.")
    return report


if __name__ == "__main__":
    prepare()
