from __future__ import annotations

"""Verifie que le .rsground et les index respectent le format RogueEssence/PMDO.

Le controle compare la structure produite a celle des vrais fichiers du depot
de reference Palikadude/Halcyon. Il echoue si une des erreurs qui empechaient
le chargement revient.
"""

from pathlib import Path
import json
import struct
import sys

ROOT = Path(__file__).resolve().parent
TILE_DIR = ROOT / "pmd" / "Content" / "Tile"
GROUND_DIR = ROOT / "pmd" / "Data" / "Ground"

from collections import Counter

FAILURES: Counter[str] = Counter()


def check(cond: bool, message: str) -> None:
    """Enregistre un echec. Les messages identiques sont comptes, pas repetes."""
    if not cond:
        FAILURES[message] += 1


def read_7bit(data: bytes, pos: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        byte = data[pos]
        pos += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, pos
        shift += 7


def tile_sheets() -> dict[str, tuple[int, set[tuple[int, int]]]]:
    sheets = {}
    for path in sorted(TILE_DIR.glob("*.tile")):
        data = path.read_bytes()
        tile_size, count = struct.unpack_from("<ii", data, 0)
        locs = set()
        for i in range(count):
            x, y, off = struct.unpack_from("<iiq", data, 8 + i * 16)
            check(0 < off < len(data), f"{path.name}: offset {off} hors fichier")
            png_len = struct.unpack_from("<q", data, off)[0]
            check(
                data[off + 8: off + 16] == b"\x89PNG\r\n\x1a\n",
                f"{path.name}: la cellule {x},{y} n'est pas un PNG",
            )
            check(off + 8 + png_len <= len(data), f"{path.name}: cellule {x},{y} tronquee")
            locs.add((x, y))
        sheets[path.stem] = (tile_size, locs)
    return sheets


def check_tile_index(sheets: dict) -> None:
    path = TILE_DIR / "index.idx"
    check(path.exists(), "Content/Tile/index.idx manquant")
    if not path.exists():
        return
    data = path.read_bytes()
    count = struct.unpack_from("<i", data, 0)[0]
    pos = 4
    indexed = {}
    for _ in range(count):
        length, pos = read_7bit(data, pos)
        name = data[pos: pos + length].decode("utf-8")
        pos += length
        tile_size, n = struct.unpack_from("<ii", data, pos)
        pos += 8
        locs = {}
        for _ in range(n):
            x, y, off = struct.unpack_from("<iiq", data, pos)
            pos += 16
            locs[(x, y)] = off
        indexed[name] = (tile_size, locs)
    check(pos == len(data), "index.idx: octets residuels apres lecture")
    check(
        set(indexed) == set(sheets),
        f"index.idx ne couvre pas les memes sheets: {set(sheets) ^ set(indexed)}",
    )
    for name, (tile_size, locs) in indexed.items():
        ref_size, ref_locs = sheets[name]
        check(tile_size == ref_size, f"{name}: TileSize {tile_size} != {ref_size}")
        check(set(locs) == ref_locs, f"{name}: cellules indexees differentes du .tile")
        # L'offset indexe doit pointer sur l'en-tete de longueur du PNG.
        raw = (TILE_DIR / f"{name}.tile").read_bytes()
        for loc, off in locs.items():
            check(
                raw[off + 8: off + 16] == b"\x89PNG\r\n\x1a\n",
                f"{name}: offset indexe de {loc} ne pointe pas sur un PNG",
            )


def check_ground(sheets: dict) -> None:
    path = GROUND_DIR / "luminous_spring_pmdo.rsground"
    check(path.exists(), "rsground manquant")
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8-sig")
    check(not text.startswith("\ufeff"), "le rsground ne doit pas etre vide")
    doc = json.loads(text)

    check("Version" in doc, "enveloppe SerializationContainer sans Version")
    check(set(doc) == {"Version", "Object"}, f"cles racine inattendues: {set(doc)}")
    o = doc["Object"]

    check(
        o.get("$type") == "RogueEssence.Ground.GroundMap, RogueEssence",
        f"$type incorrect: {o.get('$type')}",
    )
    check(isinstance(o.get("Name"), dict) and "DefaultText" in o.get("Name", {}),
          "Name doit etre un LocalText")
    check(isinstance(o.get("TexSize"), int) and o.get("TexSize", 0) >= 1, "TexSize invalide")
    check(isinstance(o.get("rand"), dict) and "$type" in o.get("rand", {}),
          "rand doit etre un IRandom serialise")
    check(isinstance(o.get("Status"), dict), "Status doit etre un dictionnaire")
    check(isinstance(o.get("Background"), dict), "Background doit etre un MapBG")
    check(isinstance(o.get("BlankBG"), dict), "BlankBG doit etre un AutoTile")
    check(isinstance(o.get("EdgeView"), int) and not isinstance(o.get("EdgeView"), bool),
          "EdgeView doit etre l'enum ScrollEdge (int)")
    check(o.get("ActiveChar") is None or isinstance(o.get("ActiveChar"), dict),
          "ActiveChar doit etre null ou un GroundChar")
    check(len(o["Decorations"]) >= 1, "il faut au moins une AnimLayer")
    check(len(o["Entities"]) >= 1, "il faut au moins une EntityLayer (ReloadEntLayer(0))")

    if o["Entities"]:
        ent = o["Entities"][0]
        for key in ("Name", "Visible", "MapChars", "GroundObjects", "Spawners", "Markers"):
            check(key in ent, f"EntityLayer sans champ {key}")
        check(len(ent.get("Markers", [])) >= 1,
              "aucun marqueur: GetEntryPoint(0) retomberait en (0,0)")

    width = len(o["Layers"][0]["Tiles"])
    height = len(o["Layers"][0]["Tiles"][0])
    check(width > 0 and height > 0, "carte vide")

    obst = o["obstacles"]
    check(
        len(obst) == width * o["TexSize"] and len(obst[0]) == height * o["TexSize"],
        f"obstacles {len(obst)}x{len(obst[0])} != {width * o['TexSize']}x{height * o['TexSize']}",
    )
    bad_walls = sum(
        1
        for col in obst
        for wall in col
        if not (isinstance(wall, dict) and "Bounds" in wall and "Tags" in wall)
    )
    check(bad_walls == 0,
          f"obstacles doit contenir des GroundWall, pas des entiers ({bad_walls} cases fautives)")

    for lay in o["Layers"]:
        check(len(lay["Tiles"]) == width and len(lay["Tiles"][0]) == height,
              f"calque {lay['Name']}: dimensions incoherentes")
        check(-1 <= lay["Layer"] <= 5, f"calque {lay['Name']}: DrawLayer {lay['Layer']} hors enum")
        for col in lay["Tiles"]:
            for tile in col:
                check(set(tile) == {"AutoTileset", "Associates", "Layers", "NeighborCode"},
                      f"calque {lay['Name']}: AutoTile incomplet {sorted(tile)}")
                for sub in tile["Layers"]:
                    check("FrameLength" in sub, f"calque {lay['Name']}: TileLayer sans FrameLength")
                    check(len(sub["Frames"]) >= 1, f"calque {lay['Name']}: TileLayer sans frame")
                    for frame in sub["Frames"]:
                        sheet = frame["Sheet"]
                        loc = (frame["TexLoc"]["X"], frame["TexLoc"]["Y"])
                        check(sheet in sheets, f"sheet inconnu reference: {sheet}")
                        if sheet in sheets:
                            check(loc in sheets[sheet][1],
                                  f"{sheet}: cellule {loc} absente du .tile")

    idx = GROUND_DIR / "index.idx"
    check(idx.exists(), "Data/Ground/index.idx manquant")
    if idx.exists():
        entries = json.loads(idx.read_text(encoding="utf-8-sig"))
        check("Version" in entries and "Object" in entries, "index.idx: enveloppe absente")
        check(o["AssetName"] in entries["Object"],
              f"index.idx ne contient pas {o['AssetName']}")


def main() -> int:
    sheets = tile_sheets()
    check_tile_index(sheets)
    check_ground(sheets)
    if FAILURES:
        for failure, count in FAILURES.items():
            suffix = f"  (x{count})" if count > 1 else ""
            print(f"ECHEC: {failure}{suffix}")
        return 1
    print("OK: rsground, Content/Tile/index.idx et Data/Ground/index.idx sont conformes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
