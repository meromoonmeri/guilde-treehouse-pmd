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
# Comme source/sharpedo de la branche auditée, le reconstructeur final ne
# découpe pas une composition : il consomme ce pack de plans natives préparés.
PLANES = ROOT / "source" / "references_exterieures" / "plans"
# Ces six backplates ont été demandés séparément au générateur, un par scène
# et ambiance. Ils constituent les vrais 00_ciel du pack de calques.
GENERATOR_PLANES = ROOT / "source" / "references_exterieures" / "generator_planes"
GENERATOR_SKY_SIZES = {"cascades": (816, 1300), "prairie_maritime": (1376, 768), "cap_cotier": (1376, 768)}

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


def generated_sky(scene_id: str, mode: str, size: tuple[int, int]) -> Image.Image:
    """Normalise un backplate produit directement par le générateur d'images."""
    path = GENERATOR_PLANES / f"{scene_id}_{mode}_00_ciel.png"
    assert path.is_file(), f"Backplate généré absent : {path}"
    with Image.open(path) as opened:
        sky = opened.convert("RGBA")
    # Les sorties image du générateur gardent le ratio demandé (x2) ; la
    # normalisation est entière, comme les rendus de composition complets.
    assert sky.size == GENERATOR_SKY_SIZES[scene_id], f"Taille de backplate inattendue : {path} = {sky.size}"
    return sky.resize(size, Image.Resampling.NEAREST)


def compose_initial(layers: list[Image.Image], size: tuple[int, int]) -> Image.Image:
    image = Image.new("RGBA", size)
    for layer in layers:
        image.alpha_composite(layer)
    return image


def prepare_semantic_planes() -> dict:
    """Écrit les sources de calques, avant tout export de livraison.

    C'est l'équivalent du pack ``source/sharpedo/*_native.png`` de la branche
    auditée : le constructeur ne connaîtra ensuite plus les heuristiques de
    préparation et lira seulement ces PNG nommés, un par plan sémantique.
    """
    # Import local tardif : ce module définit les règles de préparation, sans
    # déclencher sa fonction build grâce à son garde __main__.
    from rebuild_references_exterieures import SCENES, load as load_native, make_layers

    result = {}
    if PLANES.exists():
        import shutil
        shutil.rmtree(PLANES)
    for scene in SCENES:
        definitions = scene["layers"]
        scene_result = {}
        for mode, filename in scene["natives"].items():
            # La native normalisée de génération sert à placer les plans de
            # terrain. 00_ciel, lui, vient d'un appel générateur autonome :
            # c'est l'actif de fond éditable, non un inpainting de secours.
            layout_native = load_native(NATIVES / filename, scene["dimensions"])
            layers = make_layers(scene["id"], layout_native, mode)
            layers[0] = generated_sky(scene["id"], mode, scene["dimensions"])
            target = PLANES / scene["id"] / mode
            for definition, layer in zip(definitions, layers):
                save(layer, target / f"{definition[0]}.png")
            # La native de livraison est la recomposition des sources générées
            # et préparées. Elle devient le contrat d'image 0 de l'export.
            save(compose_initial(layers, scene["dimensions"]), NATIVES / filename)
            scene_result[mode] = [definition[0] for definition in definitions]
        result[scene["id"]] = scene_result
    (PLANES / "kit.json").write_text(json.dumps({
        "methode": "plans_natives_prepares_avant_export_comme_sharpedo",
        "scenes": result,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


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

    semantic_planes = prepare_semantic_planes()
    generator_planes_report = {
        path.name: {"sha256": digest(path), "dimensions": list(Image.open(path).size), "role": "00_ciel"}
        for path in sorted(GENERATOR_PLANES.glob("*_00_ciel.png"))
    }
    assert len(generator_planes_report) == 6, "Six backplates générés sont requis"
    report = {
        "methode": "generation_image_referencee_puis_normalisation_et_preparation_de_plans_natives",
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
        "generation_des_calques": generator_planes_report,
        "plans_natives": semantic_planes,
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
