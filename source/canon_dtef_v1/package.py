"""Package CANON1 as one autonomous ZIP and verify what the archive really holds.

The repository keeps scripts, manifests and direct previews; the heavy export tree
regenerates with `build.py`, so the archive is the delivered artefact. Verification
re-reads the ZIP: CRC, member list, byte-identity of a sample of members against
the working tree, and the recorded SHA-256.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / 'renders/canon_dtef_v1'
NAME = 'Canonia_DTEF_v1.zip'


def members():
    include = ['DTEF', 'cartes', 'manifests', 'PMDO', 'layouts', 'manifest.json', 'verification.json',
               'README_import.md', 'README.md']
    scripts = ['autotile.py', 'build.py', 'layouts.py', 'native.py', 'package.py', 'pmdo_ground.py',
               'serve.py', 'verify.py']
    paths = []
    for top in include:
        p = OUT / top
        if p.is_dir():
            paths += [q for q in sorted(p.rglob('*')) if q.is_file()]
        elif p.is_file():
            paths.append(p)
    for name in scripts:
        paths.append(HERE / name)
    paths += [HERE / 'layouts' / f'{m}.txt' for m in sorted(p.stem for p in (HERE / 'layouts').glob('*.txt'))]
    paths += sorted(p for p in (OUT / 'apercus').glob('*.png'))
    paths += sorted((OUT / 'apercus').glob('*_cycle.webp'))
    seen, unique = set(), []
    for path in paths:
        if path.exists() and path not in seen:
            seen.add(path)
            unique.append(path)
    return unique


def build():
    paths = members()
    archive = OUT / NAME
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in paths:
            if path.is_relative_to(HERE):
                arc = Path('scripts') / path.relative_to(HERE)
            else:
                arc = path.relative_to(OUT)
            z.write(path, arc.as_posix())
    with zipfile.ZipFile(archive) as z:
        bad = z.testzip()
        assert bad is None, f'membre corrompu : {bad}'
        names = set(z.namelist())
        sample = sorted(n for n in names if n.endswith(('.png', '.rsground', '.json', '.txt')))
        checks = 0
        for name in sample[::max(1, len(sample) // 60)]:
            source = OUT / name if not name.startswith('scripts/') else HERE / name[len('scripts/'):]
            if source.exists():
                assert hashlib.sha256(z.read(name)).hexdigest() == hashlib.sha256(source.read_bytes()).hexdigest(), name
                checks += 1
        # the delivered Ground maps and their banks must both be inside
        manifest = json.loads((OUT / 'manifest.json').read_text())
        for map_id, info in manifest['maps'].items():
            for mode in ('jour', 'nuit'):
                asset = info['modes'][mode]['ground']['asset']
                bank = info['modes'][mode]['ground']['bank']
                assert f'PMDO/Data/Ground/{asset}.rsground' in names, (map_id, mode, 'rsground')
                assert f'PMDO/Content/Tile/{bank}.tile' in names, (map_id, mode, 'tile')
        for theme, info_t in manifest['themes'].items():
            for mode in ('jour', 'nuit'):
                assert f"DTEF/{info_t['source']}_{mode}/tileset_0.png" in names, (theme, mode)
        for required in ('PMDO/INSTALLER.py', 'PMDO/Mod.xml', 'PMDO/Content/Tile/index.idx',
                         'README_import.md', 'README.md', 'verification.json'):
            assert required in names, required
    sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    out = {'archive': NAME, 'bytes': archive.stat().st_size, 'members': len(names),
           'sha256': sha, 'sample_bytes_verified': checks, 'sampled': len(sample[::max(1, len(sample) // 60)])}
    (OUT / 'pack_verification.json').write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return out


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    build()
