#!/usr/bin/env python3
"""Recover PMUniverse map-layer metadata from the public PMU server database.

This is a metadata audit: it reads tile IDs, layer slots, alpha classification and
map dimensions, but it never writes PMUniverse artwork to the project.  It also
does not persist player-house display names from the historical public database.

Inputs are local PMU-Client and PMU-Server checkouts.  Pillow is required only to
inspect PNG alpha channels already embedded inside the PMU .tile containers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import time
import zipfile
from collections import Counter, defaultdict
from io import BytesIO
from pathlib import Path
from typing import Any, Callable

try:
    from PIL import Image
except ImportError as error:  # pragma: no cover - depends on caller environment
    raise SystemExit("Pillow is required: pip install Pillow") from error

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
LAYERS: tuple[tuple[str, int, int, str], ...] = (
    ("ground", 3, 21, "ground_animation"),
    ("ground_animation", 4, 22, "ground"),
    ("mask", 5, 23, "mask_animation"),
    ("mask_animation", 6, 24, "mask"),
    ("mask_2", 7, 25, "mask_2_animation"),
    ("mask_2_animation", 8, 26, "mask_2"),
    ("fringe", 9, 27, "fringe_animation"),
    ("fringe_animation", 10, 28, "fringe"),
    ("fringe_2", 11, 29, "fringe_2_animation"),
    ("fringe_2_animation", 12, 30, "fringe_2"),
)
MAP_TABLES = {
    b"map_general",
    b"map_data",
    b"map_standard_data",
    b"map_house_data",
    b"map_instanced_data",
    b"map_rdungeon_data",
    b"map_tiles",
}
LAYER_NAMES = tuple(layer[0] for layer in LAYERS)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def to_int(value: str | None) -> int:
    try:
        return int(value or 0)
    except ValueError:
        return 0


def unescape_sql(value: bytes) -> str | None:
    """Decode a MySQL dump scalar; quote delimiters are removed by the parser."""
    value = value.strip()
    if value == b"NULL":
        return None
    return value.decode("latin1").replace("\\'", "'").replace("\\\\", "\\")


def alpha_mode(png: bytes) -> str:
    """Return one of opaque/mixed/empty from a 32-bit tile PNG."""
    with Image.open(BytesIO(png)) as image:
        minimum, maximum = image.convert("RGBA").getchannel("A").getextrema()
    if minimum == maximum == 255:
        return "opaque"
    if minimum == maximum == 0:
        return "empty"
    return "mixed"


def inspect_tilesets(client_repo: Path) -> tuple[dict[str, Any], dict[tuple[int, int], str]]:
    """Validate every indexed .tile payload and return its alpha-mode lookup."""
    tile_dir = client_repo / "resources/GFX/Tiles"
    alpha_by_reference: dict[tuple[int, int], str] = {}
    catalog: dict[str, Any] = {}
    for tile_file in sorted(tile_dir.glob("Tiles*.tile")):
        data = tile_file.read_bytes()
        match_name = tile_file.stem.removeprefix("Tiles")
        if not match_name.isdecimal():
            continue
        tileset = int(match_name)
        first_png = data.find(PNG_SIGNATURE)
        if first_png < 8 or (first_png - 8) % 12:
            raise ValueError(f"unrecognised .tile index layout: {tile_file}")
        tile_count = (first_png - 8) // 12
        alpha_counts: Counter[str] = Counter()
        for tile_index in range(tile_count):
            entry = 8 + tile_index * 12
            relative_offset, png_size = struct.unpack_from("<QI", data, entry)
            payload_offset = first_png + relative_offset
            payload = data[payload_offset : payload_offset + png_size]
            if len(payload) != png_size or not payload.startswith(PNG_SIGNATURE):
                raise ValueError(f"invalid PNG payload in {tile_file}, entry {tile_index}")
            mode = alpha_mode(payload)
            alpha_by_reference[(tileset, tile_index)] = mode
            alpha_counts[mode] += 1
        catalog[str(tileset)] = {
            "path": tile_file.relative_to(client_repo).as_posix(),
            "sha256": sha256(tile_file),
            "file_bytes": len(data),
            "embedded_png_tiles": tile_count,
            "tile_dimensions": [32, 32],
            "alpha_modes": dict(sorted(alpha_counts.items())),
        }
    expected = set(range(11))
    found = {int(key) for key in catalog}
    if found != expected:
        raise ValueError(f"expected Tiles0.tile through Tiles10.tile, found {sorted(found)}")
    return catalog, alpha_by_reference


def map_kind(map_id: str) -> str:
    if map_id.startswith("s") and map_id[1:].isdigit():
        return "standard"
    if map_id.startswith("h-"):
        return "house"
    if map_id.startswith("rd-"):
        return "random_dungeon"
    if map_id.startswith("i-"):
        return "instanced"
    return "other"


def fresh_layer_stats() -> dict[str, Any]:
    return {
        "nonzero_cells": 0,
        "tileset_cell_counts": Counter(),
        "distinct_tile_references": set(),
        "alpha_cell_counts": Counter(),
    }


def fresh_map_record() -> dict[str, Any]:
    return {
        "layers": {layer: fresh_layer_stats() for layer in LAYER_NAMES},
        "tile_rows": 0,
    }


def serialise_layer_stats(stats: dict[str, Any]) -> dict[str, Any]:
    return {
        "nonzero_cells": stats["nonzero_cells"],
        "tileset_cell_counts": dict(sorted(stats["tileset_cell_counts"].items())),
        "distinct_tile_references": len(stats["distinct_tile_references"]),
        "alpha_cell_counts": dict(sorted(stats["alpha_cell_counts"].items())),
    }


def consume_insert_rows(
    dump: zipfile.ZipExtFile,
    callback: Callable[[bytes, list[str | None]], None],
) -> None:
    """Stream the dump and call back rows in the seven map-bearing SQL tables.

    mysqldump serialises these enormous tables as INSERT ... VALUES (...) lines.
    This parser is deliberately streaming: it handles quoted commas and escaped
    apostrophes, but never materialises the 1.15 GB SQL dump in memory.
    """
    markers = {b"INSERT INTO `" + table + b"` VALUES ": table for table in MAP_TABLES}
    probe = bytearray()
    active_table: bytes | None = None
    in_row = False
    in_quote = False
    escaped = False
    fields: list[str | None] = []
    field = bytearray()

    while block := dump.read(1024 * 1024):
        for byte in block:
            if active_table is None:
                probe.append(byte)
                if len(probe) > 64:
                    del probe[:-64]
                for marker, table in markers.items():
                    if probe.endswith(marker):
                        active_table = table
                        probe.clear()
                        in_row = False
                        in_quote = False
                        escaped = False
                        fields = []
                        field.clear()
                        break
                continue

            if in_quote:
                if escaped:
                    field.append(byte)
                    escaped = False
                elif byte == 92:  # backslash
                    field.append(byte)
                    escaped = True
                elif byte == 39:  # apostrophe
                    in_quote = False
                else:
                    field.append(byte)
                continue

            if byte == 39:
                in_quote = True
            elif not in_row:
                if byte == 40:  # opening parenthesis
                    in_row = True
                    fields = []
                    field.clear()
                elif byte == 59:  # semicolon
                    active_table = None
                    probe.clear()
            elif byte == 44:  # comma
                fields.append(unescape_sql(bytes(field)))
                field.clear()
            elif byte == 41:  # closing parenthesis
                fields.append(unescape_sql(bytes(field)))
                field.clear()
                callback(active_table, fields)
                in_row = False
            else:
                field.append(byte)


def audit(server_repo: Path, client_repo: Path, output: Path, audit_date: str) -> None:
    tileset_catalog, alpha_by_reference = inspect_tilesets(client_repo)
    archive = server_repo / "Content_Data.zip"
    if not archive.is_file():
        raise FileNotFoundError(f"server archive not found: {archive}")

    maps: dict[str, dict[str, Any]] = {}
    table_types: defaultdict[str, set[str]] = defaultdict(set)
    official_target_names: dict[str, str] = {}
    # Populated before the map_tiles INSERT section in this mysqldump; keeping
    # it here lets the audit stream the 1.15 GB dump only once.
    target_cells: dict[str, dict[str, list[dict[str, Any]]]] = {}
    global_layers = {layer: fresh_layer_stats() for layer in LAYER_NAMES}
    invalid_references: Counter[str] = Counter()
    bad_rows: Counter[str] = Counter()

    def obtain_map(map_id: str) -> dict[str, Any]:
        record = maps.setdefault(map_id, {})
        if "layers" not in record:
            record.update(fresh_map_record())
        return record

    def register_reference(stats: dict[str, Any], tileset: int, tile: int) -> str:
        mode = alpha_by_reference.get((tileset, tile))
        if mode is None:
            invalid_references[f"{tileset}:{tile}"] += 1
            mode = "unresolved"
        stats["nonzero_cells"] += 1
        stats["tileset_cell_counts"][tileset] += 1
        stats["distinct_tile_references"].add((tileset, tile))
        stats["alpha_cell_counts"][mode] += 1
        return mode

    def row_callback(table: bytes, values: list[str | None]) -> None:
        if table == b"map_general":
            if len(values) != 5 or values[0] is None:
                bad_rows["map_general"] += 1
                return
            record = obtain_map(values[0])
            record["dimensions_cells"] = [to_int(values[3]) + 1, to_int(values[4]) + 1]
            record["revision"] = to_int(values[2])
            return

        if table == b"map_data":
            if len(values) != 14 or values[0] is None:
                bad_rows["map_data"] += 1
                return
            # Store only canonical map names relevant to the explicit waterfall,
            # water and bridge audit. Player-house names are intentionally omitted.
            map_id, display_name = values[0], values[1] or ""
            if map_kind(map_id) == "standard" and any(
                term in display_name.casefold() for term in ("water", "cascade", "bridge")
            ):
                official_target_names[map_id] = display_name
                target_cells.setdefault(map_id, {layer: [] for layer in LAYER_NAMES})
            return

        if table in {b"map_standard_data", b"map_house_data", b"map_instanced_data", b"map_rdungeon_data"}:
            if not values or values[0] is None:
                bad_rows[table.decode()] += 1
                return
            table_types[values[0]].add(table.decode())
            return

        if table != b"map_tiles":
            return
        if len(values) != 31 or values[0] is None:
            bad_rows["map_tiles"] += 1
            return
        map_id = values[0]
        record = obtain_map(map_id)
        record["tile_rows"] += 1
        for layer, tile_index, tileset_index, _pair in LAYERS:
            tile_number = to_int(values[tile_index])
            if tile_number == 0:
                continue
            tileset_number = to_int(values[tileset_index])
            mode = register_reference(record["layers"][layer], tileset_number, tile_number)
            register_reference(global_layers[layer], tileset_number, tile_number)
            if map_id in target_cells:
                target_cells[map_id][layer].append(
                    {
                        "x": to_int(values[1]),
                        "y": to_int(values[2]),
                        "tileset": tileset_number,
                        "tile": tile_number,
                        "alpha": mode,
                    }
                )

    started = time.monotonic()
    with zipfile.ZipFile(archive) as zip_file, zip_file.open("pmu_data.sql") as dump:
        consume_insert_rows(dump, row_callback)
    elapsed_seconds = round(time.monotonic() - started, 3)

    if bad_rows:
        raise ValueError(f"malformed or unexpected SQL rows: {dict(bad_rows)}")

    # The server dump is newer than several of the client .tile packages. Keep
    # those references explicit instead of discarding them or pretending a map
    # can be rendered perfectly from an incomplete asset snapshot.
    unresolved_by_tileset: Counter[int] = Counter()
    for reference, cell_count in invalid_references.items():
        unresolved_by_tileset[int(reference.split(":", 1)[0])] += cell_count

    target_ids = set(official_target_names)
    total_elapsed_seconds = elapsed_seconds

    serial_maps: dict[str, Any] = {}
    for map_id, record in sorted(maps.items()):
        # An empty sentinel row exists in the dump. It is not a map.
        if not map_id:
            continue
        serial_maps[map_id] = {
            "kind": map_kind(map_id),
            "database_types": sorted(table_types[map_id]),
            "dimensions_cells": record.get("dimensions_cells"),
            "revision": record.get("revision"),
            "tile_rows": record["tile_rows"],
            "layers": {layer: serialise_layer_stats(record["layers"][layer]) for layer in LAYER_NAMES},
        }

    target_maps: dict[str, Any] = {}
    for map_id in sorted(target_ids, key=lambda item: int(item[1:])):
        base = serial_maps.get(map_id)
        if base is None:
            continue
        target_maps[map_id] = {
            "official_display_name": official_target_names[map_id],
            **base,
            "rendering_contract": {
                "phase_0_static_slots": ["ground", "mask", "mask_2", "fringe", "fringe_2"],
                "phase_1_replacement_slots": [
                    "ground_animation", "mask_animation", "mask_2_animation", "fringe_animation", "fringe_2_animation"
                ],
                "phase_period_ms": 250,
                "note": "Each animation slot replaces its paired static slot only where a nonzero animation tile is present.",
            },
            "nonzero_cells_by_layer": target_cells[map_id],
        }

    kind_counts = Counter(record["kind"] for record in serial_maps.values())
    source = {
        "organization": "PMUniverse",
        "audit_date": audit_date,
        "server_repository": "PMUniverse/PMU-Server",
        "server_snapshot_commit": "8fb424a520e559e94cff4973def8172cf29d90a2",
        "client_repository": "PMUniverse/PMU-Client",
        "client_snapshot_commit": "c25c01f9879369647cd5a19731b2e4e5acd33e67",
        "archive_path": "Content_Data.zip",
        "archive_sha256": sha256(archive),
        "method": (
            "Streamed the public pmu_data.sql dump once; no SQL dump or image pixels are emitted. "
            "All .tile payloads were decoded only to classify alpha."
        ),
    }
    summary = {
        **source,
        "database": {
            "map_records_total": len(serial_maps),
            "map_records_with_tile_rows": sum(record["tile_rows"] > 0 for record in serial_maps.values()),
            "map_kind_counts": dict(sorted(kind_counts.items())),
            "map_tile_rows": sum(record["tile_rows"] for record in serial_maps.values()),
            "map_tile_rows_excluded_empty_map_id": maps.get("", {}).get("tile_rows", 0),
            "render_slots_in_order": list(LAYER_NAMES),
            "animation_pairs": [{"static": layer, "animation": pair} for layer, _, _, pair in LAYERS if not layer.endswith("animation")],
            "global_layer_usage": {layer: serialise_layer_stats(global_layers[layer]) for layer in LAYER_NAMES},
            "unresolved_tileset_references": {
                "distinct_references": len(invalid_references),
                "referencing_cells": sum(invalid_references.values()),
                "referencing_cells_by_tileset": dict(sorted(unresolved_by_tileset.items())),
                "first_100_references": [
                    {"tileset_tile": reference, "referencing_cells": count}
                    for reference, count in sorted(invalid_references.items())[:100]
                ],
                "meaning": "The server dump refers to tile indices absent from the 11 .tile files in this PMU-Client snapshot.",
            },
        },
        "tilesets": tileset_catalog,
        "water_and_bridge_standard_maps": {
            "count": len(target_maps),
            "map_ids": list(target_maps),
        },
        "parser_seconds_first_pass": elapsed_seconds,
        "parser_seconds_total": total_elapsed_seconds,
    }

    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / "all_maps_layer_catalog.json").write_text(
        json.dumps({**source, "maps": serial_maps}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (output / "waterfall_water_bridge_maps.json").write_text(
        json.dumps({**source, "maps": target_maps}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"PMUniverse map audit: {len(serial_maps)} maps, "
        f"{sum(record['tile_rows'] for record in serial_maps.values())} map cells, "
        f"{len(target_maps)} named water/bridge standard maps -> {output}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client-repo", type=Path, required=True, help="local PMU-Client checkout")
    parser.add_argument("--server-repo", type=Path, required=True, help="local PMU-Server checkout")
    parser.add_argument("--out", type=Path, default=Path("audit_pmuniverse_maps"), help="output directory")
    parser.add_argument("--audit-date", default="2026-09-13")
    args = parser.parse_args()
    audit(args.server_repo, args.client_repo, args.out, args.audit_date)


if __name__ == "__main__":
    main()
