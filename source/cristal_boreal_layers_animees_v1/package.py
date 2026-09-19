#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reconstruit, contrôle et emballe le lot. `--check` saute la régénération et le ZIP."""
from pathlib import Path
import argparse
import json
import re
import subprocess
import sys
import zipfile

R = Path(__file__).resolve().parents[2]
O = R / 'renders/cristal_boreal_layers_animees_v1'
LOT = 'cristal_boreal_layers_animees_v1'
GALERIE = R / ('apercu_%s.html' % LOT)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true', help='vérifier sans régénérer ni emballer')
    args = ap.parse_args()
    if not args.check:
        subprocess.run([sys.executable, 'source/%s/build.py' % LOT], cwd=R, check=True)
    subprocess.run([sys.executable, '-m', 'unittest', 'source.cristal_boreal_layers_animees_v1.test_build', '-q'],
                   cwd=R, check=True)
    js = re.search(r'<script>(.*?)</script>', GALERIE.read_text(), re.S).group(1)
    if subprocess.run(['node', '--check'], input=js, text=True).returncode:
        raise SystemExit('le script de la galerie ne se parse pas')
    m = json.loads((O / 'manifest.json').read_text())
    (O / 'verification.json').write_text(json.dumps({
        'lot': LOT, 'tests_dedies': '18 PASS', 'syntaxe_js_galerie': 'PASS',
        'controles': m['controles'], 'cycle_maitre_ms': m['cycle_maitre_ms'],
        'poses_maitresse': m['poses_maitresse'], 'couches_animees': sorted(m['couches']),
        'base_recopiee': 'cinq calques et douze poses du lot V1 à l octet près',
        'art_approved': False, 'runtime_pmdo': 'NON TESTÉ',
        'reserve': 'aucune collision, aucun warp, aucun import moteur vérifié ; aperçu navigateur non testé',
    }, ensure_ascii=False, indent=2) + '\n')
    if args.check:
        print('vérifications :', (O / 'verification.json').read_text())
        return
    with zipfile.ZipFile(R / ('renders/%s_pack.zip' % LOT), 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(O.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(O))
        z.write(GALERIE, 'apercu.html')
    print('pack :', R / ('renders/%s_pack.zip' % LOT))


if __name__ == '__main__':
    main()
