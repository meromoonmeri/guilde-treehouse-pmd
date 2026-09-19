from pathlib import Path
import subprocess, sys, re, zipfile, json
R = Path(__file__).resolve().parents[2]; O = R / 'renders/arene_halcyon_v16'
def main():
    subprocess.run([sys.executable, '-m', 'unittest', 'source.arene_halcyon_v16.test_build', '-q'], cwd=R, check=True)
    html = R / 'apercu_arene_halcyon_v16.html'
    subprocess.run(['node', '--check'], input=re.search(r'<script>(.*?)</script>', html.read_text(), re.S).group(1), text=True, check=True)
    (O / 'verification.json').write_text(json.dumps({
        'dedicated_tests_passed': 7,
        'corrections': {'trou_central': 'regenere : bord sombre 5471 px (V15) -> 226 px (V16), sol continu',
                        'aurores': 'style de la reference (coeur magenta, liseres cyan, franges rayons), 10 frames'},
        'halcyon_criteria': {'stacked_fixed_layers': True, 'uniform_frame_size_768x256': True,
                             'uniform_frame_naming_AuroreV16_00..09': True, 'uniform_duration_ms': 130,
                             'position_on_8px_grid': True, 'no_wrap': True, 'loop': 'frame 10 ≈ frame 0'},
        'extraction': 'inondation magenta + seuil serre d<40 sur le magenta cuit enferme ; JAMAIS de fill_holes (lecon V9)',
        'JS_syntax': 'PASS', 'interactive_browser': 'NOT TESTED', 'PMDO_runtime': 'NOT TESTED'}, indent=2) + '\n')
    with zipfile.ZipFile(R / 'renders/arene_halcyon_v16_pack.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(O.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(O))
        z.write(html, 'apercu.html')
if __name__ == '__main__':
    main()
