#!/usr/bin/env python3
"""Safe installer for the Glacier Cliff Aurora PMDO pack.

It merges Content/Tile/index.idx rather than replacing a user's index, and
refuses to overwrite any existing file whose bytes differ.
"""
from __future__ import annotations

import argparse
import os
import shutil
import struct
import tempfile
from pathlib import Path
import re
import xml.etree.ElementTree as ET


def read_exact(f, n):
    data = f.read(n)
    if len(data) != n:
        raise ValueError("truncated PMDO index")
    return data


def read_var_string(f):
    size = 0
    shift = 0
    while True:
        b = read_exact(f, 1)[0]
        size |= (b & 127) << shift
        if b < 128:
            break
        shift += 7
        if shift > 28:
            raise ValueError("invalid .NET string length")
    return read_exact(f, size).decode("utf-8")


def write_var_string(value):
    raw = value.encode("utf-8")
    n = len(raw)
    out = bytearray()
    while n >= 128:
        out.append((n & 127) | 128)
        n >>= 7
    out.append(n)
    return bytes(out) + raw


def read_node(f):
    header = read_exact(f, 8)
    tile_size, count = struct.unpack("<ii", header)
    if tile_size <= 0 or count < 0 or count > 10_000_000:
        raise ValueError("invalid TileIndexNode")
    return header + read_exact(f, count * 16)


def read_index(path):
    if not path.exists():
        return {}
    with path.open("rb") as f:
        count = struct.unpack("<i", read_exact(f, 4))[0]
        if count < 0 or count > 100_000:
            raise ValueError("invalid PMDO tile index count")
        result = {}
        for _ in range(count):
            name = read_var_string(f)
            result[name] = read_node(f)
        if f.read(1):
            raise ValueError("unexpected bytes after PMDO tile index")
        return result


def encode_index(nodes):
    return struct.pack("<i", len(nodes)) + b"".join(
        write_var_string(name) + nodes[name] for name in sorted(nodes)
    )


def install(source: Path, target: Path, dry_run=False):
    source = source.resolve()
    target = target.resolve()
    header = target / "Mod.xml"
    if not header.is_file():
        raise ValueError("target must be the root of a PMDO mod containing Mod.xml")
    namespace = ET.parse(header).getroot().findtext("Namespace")
    if namespace and not re.fullmatch(r"[A-Za-z0-9_]+", namespace):
        raise ValueError("invalid target Lua namespace")

    copies = {}
    for top in ("Data", "Content"):
        for src in (source / top).rglob("*"):
            if not src.is_file():
                continue
            relative = src.relative_to(source)
            # The standalone index is intentionally not copied: it must be
            # merged with the user's existing native index below.
            if relative.as_posix() == "Content/Tile/index.idx":
                continue
            copies[target / relative] = src
            if namespace and relative.parts[:3] == ("Data", "Script", "ground"):
                copies[target / "Data/Script" / namespace / Path(*relative.parts[2:])] = src

    if not list((source / "Data/Ground").glob("*.rsground")):
        raise ValueError("pack is incomplete: no GroundMap found")

    conflicts = [str(dst) for dst, src in copies.items()
                 if dst.exists() and (not dst.is_file() or dst.read_bytes() != src.read_bytes())]
    if conflicts:
        raise ValueError("installation stopped; edited/conflicting files:\n" + "\n".join(conflicts))

    index_path = target / "Content/Tile/index.idx"
    nodes = read_index(index_path)
    for tile in sorted((target / "Content/Tile").glob("*.tile")):
        with tile.open("rb") as f:
            nodes[tile.stem] = read_node(f)
    for tile in sorted((source / "Content/Tile").glob("*.tile")):
        with tile.open("rb") as f:
            nodes[tile.stem] = read_node(f)
    new_index = encode_index(nodes)

    print(f"{len(copies)} files; merged tile index: {len(nodes)} entries")
    if dry_run:
        print("dry-run: no files changed")
        return

    for dst, src in copies.items():
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            with dst.open("xb") as out, src.open("rb") as incoming:
                shutil.copyfileobj(incoming, out)

    index_path.parent.mkdir(parents=True, exist_ok=True)
    if index_path.exists() and index_path.read_bytes() != new_index:
        with tempfile.NamedTemporaryFile(prefix="index.before_glacier.", suffix=".bak",
                                         dir=index_path.parent, delete=False) as backup:
            backup.write(index_path.read_bytes())
            print("index backup:", backup.name)
    if not index_path.exists() or index_path.read_bytes() != new_index:
        with tempfile.NamedTemporaryFile(prefix="index.glacier.", suffix=".tmp",
                                         dir=index_path.parent, delete=False) as tmp:
            tmp.write(new_index)
            temp_name = tmp.name
        os.replace(temp_name, index_path)
    print("installation complete; restart PMDO and enable the target mod")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mod", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        install(Path(__file__).resolve().parent, args.mod, args.dry_run)
    except (ValueError, OSError, ET.ParseError) as exc:
        parser.exit(1, f"installation stopped: {exc}\n")
