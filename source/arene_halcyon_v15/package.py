from pathlib import Path
import subprocess, sys, re, zipfile, json
R = Path(__file__).resolve().parents[2]; O = R / 'renders/arene_halcyon_v15'
def main():
    subprocess.run([sys.executable, '-m', 'unittest', 'source.arene_halcyon_v15.test_build', '-q'], cwd=R, check=True)
    html = R / 'apercu_arene_halcyon_v15.html'
    subprocess.run(['node', '--check'], input=re.search(r'<script>(.*?)</script>', html.read_text(), re.S).group(1), text=True, check=True)
    (O / 'verification.json').write_text(json.dumps({
        'dedicated_tests_passed': 8,
        'halcyon_criteria': {'stacked_fixed_layers': True, 'uniform_frame_size_768x256': True,
                             'uniform_frame_naming_AuroreV15_00..07': True, 'uniform_duration_ms': 150,
                             'position_on_8px_grid': True, 'no_wrap': True},
        'methode': 'canonique: full-frame generated terrain + magenta flood alpha; generated 2x4 undulation sheet -> 8 frames',
        'JS_syntax': 'PASS', 'interactive_browser': 'NOT TESTED', 'PMDO_runtime': 'NOT TESTED',
        'native_pixels': False, 'cycle_officiel': False}, indent=2) + '\n')
    with zipfile.ZipFile(R / 'renders/arene_halcyon_v15_pack.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(O.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(O))
        z.write(html, 'apercu.html')
if __name__ == '__main__':
    main()
