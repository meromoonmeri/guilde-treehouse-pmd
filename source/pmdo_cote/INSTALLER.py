#!/usr/bin/env python3
"""Installer standard-library-only. Never overwrites maps/graphics with different bytes.
Merges the native tile index; backs up an existing index before changing it.
Close PMDO first. Usage: python INSTALLER.py /path/to/PMDO/MODS/my_mod
"""
import argparse
import io
import os
from pathlib import Path
import re
import shutil
import struct
import tempfile
import xml.etree.ElementTree as ET


def exact(stream, size):
    data = stream.read(size)
    if len(data) != size:
        raise ValueError('Fichier binaire tronque')
    return data


def read_string(stream):
    size = 0
    for shift in range(0, 35, 7):
        byte = exact(stream, 1)[0]
        size |= (byte & 127) << shift
        if byte < 128:
            return exact(stream, size).decode('utf-8')
    raise ValueError('Longueur .NET invalide')


def write_string(value):
    raw = value.encode('utf-8')
    size, header = len(raw), bytearray()
    while size >= 128:
        header.append((size & 127) | 128)
        size >>= 7
    return bytes(header) + bytes([size]) + raw


def read_node(stream):
    header = exact(stream, 8)
    tile_size, count = struct.unpack('<ii', header)
    if tile_size <= 0 or not 0 <= count <= 10_000_000:
        raise ValueError('En-tete TileIndexNode invalide')
    return header + exact(stream, count * 16)


def read_index(path):
    if not path.exists():
        return {}
    with path.open('rb') as f:
        count = struct.unpack('<i', exact(f, 4))[0]
        if not 0 <= count <= 100_000:
            raise ValueError('Index PMDO invalide')
        nodes = {}
        for _ in range(count):
            name = read_string(f)
            nodes[name] = read_node(f)
        if f.read(1):
            raise ValueError('Format index inattendu : installation annulee')
        return nodes


def encode_index(nodes):
    return struct.pack('<i', len(nodes)) + b''.join(write_string(k) + nodes[k] for k in sorted(nodes))


def install(source, target, dry_run=False, namespace=None):
    source, target = source.resolve(), target.resolve()
    header = target / 'Mod.xml'
    if not header.is_file():
        raise ValueError('Choisir la racine du mod contenant Mod.xml, pas la racine de PMDO.')
    if namespace is None:
        namespace = ET.parse(header).getroot().findtext('Namespace')
    if namespace and not re.fullmatch(r'[A-Za-z0-9_]+', namespace):
        raise ValueError('Namespace invalide : utiliser --namespace avec le nom Lua du mod.')
    copies = {}
    for top in ['Data', 'Content']:
        for src in (source / top).rglob('*'):
            if not src.is_file():
                continue
            relative = src.relative_to(source)
            # Keep legacy scripts and provide a namespaced copy for recent PMDO.
            copies[target / relative] = src
            if namespace and relative.parts[:3] == ('Data', 'Script', 'ground'):
                copies[target / 'Data/Script' / namespace / Path(*relative.parts[2:])] = src
    if not copies or not list((source / 'Data/Ground').glob('*.rsground')):
        raise ValueError('Extraire tout le ZIP avant de lancer INSTALLER.py.')
    conflicts = [str(dst) for dst, src in copies.items()
                 if dst.exists() and (not dst.is_file() or dst.read_bytes() != src.read_bytes())]
    if conflicts:
        raise ValueError('Aucun fichier copie. Conflits (cartes editees protegees) :\n' + '\n'.join(conflicts))
    index = target / 'Content/Tile/index.idx'
    nodes = read_index(index)  # Validate before copying anything.
    for tile in sorted((target / 'Content/Tile').glob('*.tile')):
        with tile.open('rb') as f:
            nodes[tile.stem] = read_node(f)
    for src in sorted((source / 'Content/Tile').glob('*.tile')):
        with src.open('rb') as f:
            nodes[src.stem] = read_node(f)
    new_index = encode_index(nodes)
    print(f'{len(copies)} fichiers proposes; index fusionne : {len(nodes)} tilesets.')
    print('Namespace :', namespace or 'aucun explicite (scripts legacy; voir README)')
    if dry_run:
        print('Simulation terminee : aucun fichier modifie.')
        return
    for dst, src in copies.items():
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive creation also protects against changes during installation.
            with dst.open('xb') as f, src.open('rb') as incoming:
                shutil.copyfileobj(incoming, f)
    index.parent.mkdir(parents=True, exist_ok=True)
    if index.exists() and index.read_bytes() != new_index:
        with tempfile.NamedTemporaryFile(prefix='index.avant_cote_v2.', suffix='.bak',
                                         dir=index.parent, delete=False) as backup:
            backup.write(index.read_bytes())
            print('Sauvegarde index :', backup.name)
    if not index.exists() or index.read_bytes() != new_index:
        with tempfile.NamedTemporaryFile(prefix='index.cote_v2.', suffix='.tmp',
                                         dir=index.parent, delete=False) as f:
            f.write(new_index)
            tmp = f.name
        os.replace(tmp, index)
    print('Installation terminee. Relancer PMDO, activer ce mod, puis ouvrir les Ground maps.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mod', type=Path)
    parser.add_argument('--namespace', help='Namespace Lua si absent de Mod.xml (PMDO recent)')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        install(Path(__file__).resolve().parent, args.mod, args.dry_run, args.namespace)
    except (ValueError, OSError, ET.ParseError) as exc:
        parser.exit(1, f'Installation arretee : {exc}\n')
