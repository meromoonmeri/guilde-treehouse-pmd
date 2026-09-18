from pathlib import Path
import subprocess, sys, re, zipfile, json
R = Path(__file__).resolve().parents[2]; O = R / 'renders/arene_guide_couches_v13'
def main():
    subprocess.run([sys.executable, '-m', 'unittest', 'source.arene_guide_couches_v13.test_build', '-q'], cwd=R, check=True)
    html = R / 'apercu_arene_guide_couches_v13.html'
    subprocess.run(['node', '--check'], input=re.search(r'<script>(.*?)</script>', html.read_text(), re.S).group(1), text=True, check=True)
    (O / 'verification.json').write_text(json.dumps({
        'dedicated_tests_passed': 8, 'calques': ['ciel_fixe', 'etoiles_fixes', 'aurore_8frames', 'terrain_fixe'],
        'aurore': 'palette cycling 8 frames from guide true colours, frame0 exact, geometry locked',
        'independante_du_ciel': True, 'frame0_egale_guide': True, 'JS_syntax': 'PASS',
        'interactive_browser': 'NOT TESTED', 'PMDO_runtime': 'NOT TESTED'}, indent=2) + '\n')
    with zipfile.ZipFile(R / 'renders/arene_guide_couches_v13_pack.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(O.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(O))
        z.write(html, 'apercu.html')
if __name__ == '__main__':
    main()
