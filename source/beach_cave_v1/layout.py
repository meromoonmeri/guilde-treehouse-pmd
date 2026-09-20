"""Layout contract for the canonical Beach Cave pit reference.

The requested rule is strict: the final map reuses the reference map's native
24px cells and its composition. This module records the layout decision only;
it does not generate or alter artwork.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REF = HERE / "references" / "ExplorersOfSkyOrigins"
OUT = ROOT / "renders" / "beach_cave_v1"


def build_spec() -> dict:
    source = json.loads((REF / "beach_cave_pit.rsground").read_text(encoding="utf-8-sig"))
    obj = source["Object"]
    cells = [len(obj["Layers"][0]["Tiles"]), len(obj["Layers"][0]["Tiles"][0])]
    tex_size = obj["TexSize"]
    cell_px = tex_size * 8
    return {
        "id": "beach_cave_anse_des_marees",
        "title": "Beach Cave — l’Anse des Marées",
        "kind": "reconstruction canonique de l'entrée Beach Cave",
        "reference_map": "source/beach_cave_v1/references/ExplorersOfSkyOrigins/beach_cave_pit.rsground",
        "grid_px": cell_px,
        "tex_size": tex_size,
        "grid_cells": cells,
        "size_px": [cells[0] * cell_px, cells[1] * cell_px],
        "function": "vestibule aquatique de donjon, arrivée au sud et cavité au nord",
        "layout_decision": "conserver la composition canonique auditée plutôt que réinventer sa géométrie",
        "depth_order": ["parois rocheuses", "eau et écume", "plage et seuil"],
        "edges": {"north": "cavité rocheuse", "south": "arrivée canonique", "west": "paroi et bassin", "east": "paroi et bassin"},
        "entrance": {"name": "Entrance", "xy": [244, 364], "direction": 4},
        "dungeon_threshold": {"name": "donjon_seuil", "xy": [220, 4], "direction": 0, "width_px": 48},
        "canonical_only": True,
        "generated_guide_used_as_pixels": False,
        "source_version": source["Version"],
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "layout.json").write_text(json.dumps(build_spec(), ensure_ascii=False, indent=2) + "\n")
    print("Wrote canonical Beach Cave layout contract; no artwork generated or modified.")


if __name__ == "__main__":
    main()
