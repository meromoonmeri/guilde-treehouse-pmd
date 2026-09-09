from __future__ import annotations

"""Convertit le .rsground "maquette" en vrai fichier RogueEssence/PMDO chargeable.

Pourquoi ce script existe
-------------------------
`build_pmdo_zone.py` écrivait un JSON *inspiré* du format PMDO, pas le format
réel attendu par `RogueEssence.Data.Serializer.DeserializeData()`. Les écarts
constatés en comparant avec les vrais fichiers de Palikadude/Halcyon
(`Data/Ground/luminous_spring.rsground`, `post_office.rsground`) :

  1. pas d'enveloppe `{"Version": ..., "Object": {...}}` ;
  2. `$type` = `RogueEssence.Dungeon.GroundScene` alors que la classe
     sérialisée est `RogueEssence.Ground.GroundMap, RogueEssence` ;
  3. `Name` = chaîne alors que `IEntryData.Name` est un `LocalText`
     (`{"DefaultText": ..., "LocalTexts": {}}`) ;
  4. `obstacles` = tableau d'entiers alors que c'est un `GroundWall[][]`
     (`{"Bounds": {X,Y,Width,Height}, "Tags": n}`) ;
  5. `rand` = 0 alors que c'est un `IRandom` polymorphe (`ReRandom`) ;
  6. `Status` = liste alors que c'est un `Dictionary<string, MapStatus>` ;
  7. `Background` = "" alors que c'est un `MapBG` ;
  8. `BlankBG` = true alors que c'est un `AutoTile` ;
  9. `EdgeView` = booléen alors que c'est l'enum `Map.ScrollEdge` (int) ;
 10. `ActiveChar` = une position alors que c'est un `GroundChar` (ou null) ;
 11. `Decorations` / `Entities` vides alors que le moteur exige au minimum
     une `AnimLayer` et une `EntityLayer` (`ReloadEntLayer(0)` sur
     `[OnDeserialized]`, `Entities[0].Markers` pour les points d'entrée) ;
 12. chaque cellule `AutoTile` doit porter `AutoTileset`, `Associates`,
     `NeighborCode`, et chaque `TileLayer` un `FrameLength` ;
 13. `TexSize` est exprimé en unités de 8 px (`TileSize = TexSize * 8`) :
     des cellules d'art de 8 px valent `TexSize = 1`, pas 8.

Le script régénère aussi les deux index binaires/JSON manquants :
  - `Content/Tile/index.idx`  (TileGuide, lu par GraphicsManager.LoadTileIndices)
  - `Data/Ground/index.idx`   (Dictionary<string, EntrySummary>)
Sans eux, `GraphicsManager.TileIndex.GetPosition()` renvoie 0 et toutes les
cellules sont dessinées avec la texture d'erreur, même si le .rsground charge.
"""

from pathlib import Path
import json
import struct

ROOT = Path(__file__).resolve().parent
PMD = ROOT / "pmd"
TILE_DIR = PMD / "Content" / "Tile"
GROUND_DIR = PMD / "Data" / "Ground"

# Version de format alignée sur les fichiers Halcyon les plus récents.
FORMAT_VERSION = "0.7.17.0"

# Graine par défaut de RogueElements.ReRandom(0), telle qu'écrite par l'éditeur.
RERANDOM_0 = {
    "$type": "RogueElements.ReRandom, RogueElements",
    "FirstSeed": 0,
    "s": [
        16294208416658607535,
        7960286522194355700,
        487617019471545679,
        17909611376780542444,
    ],
}

TEX_SIZE = 8  # GraphicsManager.TEX_SIZE

# Ordre de dessin PMDO (RogueEssence.Content.DrawLayer).
DRAW_UNDER, DRAW_BOTTOM, DRAW_BACK, DRAW_NORMAL, DRAW_FRONT, DRAW_TOP = -1, 0, 1, 2, 3, 4

# Les calques du pack, avec le DrawLayer réel de RogueEssence.
# Attention : la valeur n'est PAS un simple index d'empilement, c'est un enum.
LAYER_DRAW = {
    "Base": DRAW_BOTTOM,
    "River": DRAW_BOTTOM,
    "Cliffs": DRAW_BOTTOM,
    "Shadows": DRAW_BOTTOM,
    "Objects Under": DRAW_BOTTOM,
    "Objects": DRAW_BOTTOM,
    "Objects Over": DRAW_BOTTOM,
    "Fringe": DRAW_TOP,
    "River Animations": DRAW_BOTTOM,
}


def empty_autotile() -> dict:
    return {"AutoTileset": "", "Associates": [], "Layers": [], "NeighborCode": 0}


def normalize_autotile(tile: dict) -> dict:
    layers = []
    for lay in tile.get("Layers", []) or []:
        frames = [
            {"Sheet": f["Sheet"], "TexLoc": {"X": f["TexLoc"]["X"], "Y": f["TexLoc"]["Y"]}}
            for f in lay.get("Frames", [])
        ]
        layers.append({"Frames": frames, "FrameLength": int(lay.get("FrameLength", 60))})
    return {
        "AutoTileset": tile.get("AutoTileset", ""),
        "Associates": list(tile.get("Associates", [])),
        "Layers": layers,
        "NeighborCode": int(tile.get("NeighborCode", 0)),
    }


def map_bg() -> dict:
    return {
        "$type": "RogueEssence.Dungeon.MapBG, RogueEssence",
        "MapLoc": {"X": 0, "Y": 0},
        "BGAnim": {
            "AnimIndex": "",
            "FrameTime": 1,
            "StartFrame": -1,
            "EndFrame": -1,
            "AnimDir": -1,
            "Alpha": 255,
            "AnimFlip": 0,
        },
        "BGMovement": {"X": 0, "Y": 0},
        "Parallax": "0, 0",
        "RepeatX": False,
        "RepeatY": False,
    }


def blank_autotile() -> dict:
    return {"AutoTileset": "", "Associates": [], "Layers": [], "NeighborCode": -1}


def obstacles_grid(tex_w: int, tex_h: int) -> list:
    """GroundWall[][] : une case de collision par unité de 8 px."""
    return [
        [
            {
                "Bounds": {
                    "X": x * TEX_SIZE,
                    "Y": y * TEX_SIZE,
                    "Width": TEX_SIZE,
                    "Height": TEX_SIZE,
                },
                "Tags": 0,
            }
            for y in range(tex_h)
        ]
        for x in range(tex_w)
    ]


def convert(src: Path, dest: Path, asset_name: str, display_name: str) -> dict:
    raw = json.loads(src.read_text(encoding="utf-8-sig"))
    old = raw["Object"] if "Object" in raw else raw

    layers = []
    for lay in old["Layers"]:
        name = lay["Name"]
        tiles = [[normalize_autotile(t) for t in col] for col in lay["Tiles"]]
        layers.append(
            {
                "Name": name,
                "Layer": LAYER_DRAW.get(name, DRAW_BOTTOM),
                "Visible": bool(lay.get("Visible", True)),
                "Tiles": tiles,
            }
        )

    width = len(layers[0]["Tiles"])
    height = len(layers[0]["Tiles"][0])
    for lay in layers:
        assert len(lay["Tiles"]) == width and len(lay["Tiles"][0]) == height, lay["Name"]

    # Les cellules d'art font 8 px : TileSize = TexSize * 8 => TexSize = 1.
    tex_size = 1

    obj = {
        "$type": "RogueEssence.Ground.GroundMap, RogueEssence",
        "TexSize": tex_size,
        "Name": {"DefaultText": display_name, "LocalTexts": {}},
        "Released": bool(old.get("Released", True)),
        "Comment": old.get("Comment", ""),
        "obstacles": obstacles_grid(width * tex_size, height * tex_size),
        "rand": RERANDOM_0,
        "Status": {},
        "Background": map_bg(),
        "BlankBG": blank_autotile(),
        "Layers": layers,
        "AssetName": asset_name,
        "Music": old.get("Music", "") or "",
        # ScrollEdge.Clamp : la caméra ne sort pas de la carte.
        "EdgeView": 1,
        "NoSwitching": bool(old.get("NoSwitching", False)),
        "ViewCenter": None,
        "ViewOffset": {"X": 0, "Y": 0},
        "ActiveChar": None,
        "Decorations": [{"Name": "New Deco", "Layer": DRAW_BOTTOM, "Visible": True, "Anims": []}],
        "Entities": [
            {
                "Name": "New EntLayer",
                "Visible": True,
                "MapChars": [],
                "GroundObjects": [],
                "Spawners": [],
                # Point d'entrée 0 : sans marqueur, GetEntryPoint() retombe en (0,0).
                "Markers": [
                    {
                        "EntName": "entrance_south",
                        "Direction": 0,
                        "EntEnabled": True,
                        "triggerType": 0,
                        "Collider": {
                            "X": (width * tex_size * TEX_SIZE) // 2,
                            "Y": (height * tex_size * TEX_SIZE) - 6 * TEX_SIZE,
                            "Width": 16,
                            "Height": 16,
                        },
                    }
                ],
            }
        ],
    }

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        json.dumps({"Version": FORMAT_VERSION, "Object": obj}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    return obj


def write_tile_index(tile_dir: Path) -> dict:
    """Reconstruit Content/Tile/index.idx (format TileGuide binaire)."""
    nodes = {}
    for path in sorted(tile_dir.glob("*.tile")):
        data = path.read_bytes()
        tile_size, count = struct.unpack_from("<ii", data, 0)
        positions = []
        for i in range(count):
            x, y, off = struct.unpack_from("<iiq", data, 8 + i * 16)
            positions.append((x, y, off))
        nodes[path.stem] = (tile_size, positions)

    out = bytearray()
    out += struct.pack("<i", len(nodes))
    for name, (tile_size, positions) in nodes.items():
        encoded = name.encode("utf-8")
        # BinaryWriter.Write(string) : longueur en 7-bit encoded int
        length = len(encoded)
        while True:
            byte = length & 0x7F
            length >>= 7
            out += bytes([byte | (0x80 if length else 0)])
            if not length:
                break
        out += encoded
        out += struct.pack("<ii", tile_size, len(positions))
        for x, y, off in positions:
            out += struct.pack("<iiq", x, y, off)
    (tile_dir / "index.idx").write_bytes(bytes(out))
    return {n: len(p) for n, (_, p) in nodes.items()}


def write_ground_index(ground_dir: Path, entries: dict) -> None:
    """Data/Ground/index.idx : Dictionary<string, EntrySummary> sérialisé."""
    payload = {
        "Version": FORMAT_VERSION,
        "Object": {
            "$type": "System.Collections.Generic.Dictionary`2[[System.String, System.Private.CoreLib],"
            "[RogueEssence.Data.EntrySummary, RogueEssence]], System.Private.CoreLib",
            **{
                key: {
                    "Name": {"DefaultText": summary["name"], "LocalTexts": {}},
                    "Released": summary["released"],
                    "Comment": summary["comment"],
                    "SortOrder": 0,
                }
                for key, summary in entries.items()
            },
        },
    }
    (ground_dir / "index.idx").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8"
    )


def main() -> None:
    src = GROUND_DIR / "luminous_spring_pmdo.rsground"
    obj = convert(src, src, "luminous_spring_pmdo", "Luminous Spring")
    counts = write_tile_index(TILE_DIR)
    write_ground_index(
        GROUND_DIR,
        {
            "luminous_spring_pmdo": {
                "name": "Luminous Spring",
                "released": obj["Released"],
                "comment": obj["Comment"],
            }
        },
    )
    print(f"rsground reecrit : {src}")
    print(f"  {len(obj['Layers'])} calques, {len(obj['Layers'][0]['Tiles'])}x"
          f"{len(obj['Layers'][0]['Tiles'][0])} cellules, TexSize={obj['TexSize']}")
    print(f"Content/Tile/index.idx : {len(counts)} sheets, {sum(counts.values())} cellules")
    print("Data/Ground/index.idx  : 1 entree")


if __name__ == "__main__":
    main()
