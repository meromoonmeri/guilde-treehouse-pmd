"""Empaquette Jungle G2 : tests puis ZIP avec controle CRC/identite."""
import subprocess
import sys
import zipfile
from pathlib import Path

R = Path(__file__).resolve().parents[2]
O = R / 'renders/jungle_generee_v2'
Z = R / 'renders/jungle_generee_v2_pack.zip'


def main():
    r = subprocess.run([sys.executable, '-m', 'unittest', 'source.jungle_generee_v2.test_build'],
                       cwd=R, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-2000:]
    if Z.exists():
        Z.unlink()
    with zipfile.ZipFile(Z, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(O.rglob('*')):
            if f.is_file():
                z.write(f, f'jungle_generee_v2/{f.relative_to(O)}')
        z.write(R / 'apercu_jungle_generee_v2.html', 'jungle_generee_v2/apercu_jungle_generee_v2.html')
        z.write(R / 'source/jungle_generee_v2/build.py', 'jungle_generee_v2/source_build.py')
    zf = zipfile.ZipFile(Z)
    assert zf.testzip() is None
    names = zf.namelist()
    for must in ('jungle_generee_v2/manifest.json', 'jungle_generee_v2/JungleG2_5_calques.ora',
                 'jungle_generee_v2/JungleG2_animation.gif'):
        assert must in names, must
    print('OK', Z.name, len(names), 'fichiers,', Z.stat().st_size, 'octets')


if __name__ == '__main__':
    main()
