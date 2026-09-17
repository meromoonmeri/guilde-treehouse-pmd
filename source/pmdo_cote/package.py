#!/usr/bin/env python3
"""Rebuild, independently verify, and package both native Ground maps."""
import argparse
from pathlib import Path
import shutil
import zipfile

from build import build
from verify import verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path.home() / 'cote_metano_v2_pmdo.zip')
    args = parser.parse_args()
    staging = Path.home() / '.cache/cote_pmdo_pack'
    source = Path(__file__).resolve().parent
    build(staging)
    shutil.copyfile(source / 'INSTALLER.py', staging / 'INSTALLER.py')
    shutil.copyfile(source / 'README.md', staging / 'README.md')
    verify(staging)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    files = [p for p in staging.rglob('*') if p.is_file()]
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(files):
            # Fixed timestamps make repeated builds byte-reproducible.
            info = zipfile.ZipInfo(path.relative_to(staging).as_posix(), (2026, 9, 12, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compresslevel=9)
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert len([n for n in archive.namelist() if n.endswith('.rsground')]) == 2
        assert not any(n.endswith('index.idx') for n in archive.namelist())
    print(f'Archive valide : {output} ({output.stat().st_size / 2**20:.2f} MiB)')


if __name__ == '__main__':
    main()
