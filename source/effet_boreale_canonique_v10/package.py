from pathlib import Path
import subprocess, sys, re, zipfile, json
R = Path(__file__).resolve().parents[2]; O = R / 'renders/effet_boreale_canonique_v10'
def main():
    subprocess.run([sys.executable, '-m', 'unittest', 'source.effet_boreale_canonique_v10.test_build', '-q'], cwd=R, check=True)
    html = R / 'apercu_effet_boreale_canonique_v10.html'
    subprocess.run(['node', '--check'], input=re.search(r'<script>(.*?)</script>', html.read_text(), re.S).group(1), text=True, check=True)
    (O / 'verification.json').write_text(json.dumps({
        'dedicated_tests_passed': 9, 'layers': 10, 'frame_ms': 160, 'cycle_s': 1.6,
        'texture': 'canonical aurorepmdsky.png recovered as-is, luminous ribbons extracted (stars/sky/peaks removed)',
        'no_baked_sky': True, 'wave_physics': 'pure transverse per-column vertical shift, travelling phase, exact 10-frame loop',
        'context_byte_identical': True, 'wrap': False, 'JS_syntax': 'PASS',
        'interactive_browser': 'NOT TESTED', 'PMDO_runtime': 'NOT TESTED',
        'native_cycle_extracted': False}, indent=2) + '\n')
    with zipfile.ZipFile(R / 'renders/effet_boreale_canonique_v10_pack.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(O.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(O))
        z.write(html, 'apercu.html')
if __name__ == '__main__':
    main()
