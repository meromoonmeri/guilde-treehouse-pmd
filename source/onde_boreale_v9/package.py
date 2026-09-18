from pathlib import Path
import subprocess, sys, re, zipfile, json
R = Path(__file__).resolve().parents[2]; O = R / 'renders/onde_boreale_v9'
def main():
    subprocess.run([sys.executable, '-m', 'unittest', 'source.onde_boreale_v9.test_build', '-q'], cwd=R, check=True)
    html = R / 'apercu_onde_boreale_v9.html'
    subprocess.run(['node', '--check'], input=re.search(r'<script>(.*?)</script>', html.read_text(), re.S).group(1), text=True, check=True)
    (O / 'verification.json').write_text(json.dumps({
        'dedicated_tests_passed': 10, 'layers': 10, 'frame_ms': 160, 'cycle_s': 1.6,
        'wave_physics': 'pure transverse wave: per-column vertical shift only, phase travelling horizontally, integer periods, exact loop',
        'master_extraction': 'magenta/white/lavender backgrounds removed by connected components, veil filled only in closed dark core',
        'context_byte_identical': True, 'wrap': False, 'JS_syntax': 'PASS',
        'interactive_browser': 'NOT TESTED', 'PMDO_runtime': 'NOT TESTED',
        'native_pixels': False, 'native_cycle_extracted': False}, indent=2) + '\n')
    with zipfile.ZipFile(R / 'renders/onde_boreale_v9_pack.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(O.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(O))
        z.write(html, 'apercu.html')
if __name__ == '__main__':
    main()
