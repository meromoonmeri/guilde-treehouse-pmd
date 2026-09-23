"""Empaquette Jungle V1 : verifie les tests puis archive ZIP avec controle CRC/identite."""
import subprocess
import sys
import zipfile
from pathlib import Path

R = Path(__file__).resolve().parents[2]
O = R / 'exports' / 'jungle_cascades_v1'
Z = R / 'exports' / 'jungle_cascades_v1_pack.zip'


def main():
    r = subprocess.run([sys.executable, '-m', 'unittest', 'source.jungle_cascades_v1.test_build'],
                       cwd=R, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-2000:]
    if Z.exists():
        Z.unlink()
    with zipfile.ZipFile(Z, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(O.rglob('*')):
            if f.is_file():
                z.write(f, f'jungle_cascades_v1/{f.relative_to(O)}')
        z.write(R / 'apercu_jungle_cascades_v1.html', 'jungle_cascades_v1/apercu_jungle_cascades_v1.html')
        z.write(R / 'source/jungle_cascades_v1/build.py', 'jungle_cascades_v1/source_build.py')
    zf = zipfile.ZipFile(Z)
    assert zf.testzip() is None
    names = zf.namelist()
    for must in ('jungle_cascades_v1/manifest.json', 'jungle_cascades_v1/JungleV1_5_calques.ora',
                 'jungle_cascades_v1/JungleV1_animation.gif',
                 'jungle_cascades_v1/apercu_jungle_cascades_v1.html'):
        assert must in names, must
    print('OK', Z.name, len(names), 'fichiers,', Z.stat().st_size, 'octets')


if __name__ == '__main__':
    main()
