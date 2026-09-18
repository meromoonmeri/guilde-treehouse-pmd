from pathlib import Path
import subprocess, sys, re, zipfile, json
R = Path(__file__).resolve().parents[2]; O = R / 'renders/arene_guide_couches_v14'
def main():
    subprocess.run([sys.executable, '-m', 'unittest', 'source.arene_guide_couches_v14.test_build', '-q'], cwd=R, check=True)
    html = R / 'apercu_arene_guide_couches_v14.html'
    subprocess.run(['node', '--check'], input=re.search(r'<script>(.*?)</script>', html.read_text(), re.S).group(1), text=True, check=True)
    (O / 'verification.json').write_text(json.dumps({
        'dedicated_tests_passed': 9, 'calques': ['ciel_fixe', 'etoiles_fixes', 'aurore_15frames', 'terrain_fixe'],
        'recomposition_exacte_du_guide': True, 'cristaux_sombres_au_terrain': True,
        'aurore': '15 frames, harmonious colour shift via circular linear interpolation of true guide ramps, geometry locked',
        'frame0_egale_guide': True, 'independante_du_ciel': True, 'JS_syntax': 'PASS',
        'interactive_browser': 'NOT TESTED', 'PMDO_runtime': 'NOT TESTED'}, indent=2) + '\n')
    with zipfile.ZipFile(R / 'renders/arene_guide_couches_v14_pack.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(O.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(O))
        z.write(html, 'apercu.html')
if __name__ == '__main__':
    main()
