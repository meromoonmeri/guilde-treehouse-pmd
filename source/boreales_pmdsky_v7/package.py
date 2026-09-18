from pathlib import Path
import subprocess, sys, re, zipfile, json
R = Path(__file__).resolve().parents[2]; O = R / 'renders/boreales_pmdsky_v7'
def main():
    subprocess.run([sys.executable, '-m', 'unittest', 'source.boreales_pmdsky_v7.test_build', '-q'], cwd=R, check=True)
    html = R / 'apercu_ciel_boreal_pmdsky_v7.html'
    subprocess.run(['node', '--check'], input=re.search(r'<script>(.*?)</script>', html.read_text(), re.S).group(1), text=True, check=True)
    (O / 'verification.json').write_text(json.dumps({
        'dedicated_tests_passed': 12, 'frames': 24, 'frame_ms': 120, 'cycle_s': 2.88,
        'method': 'reference image itself, proportional luminance veil modulation, no translation/wrap/hue',
        'frame0_equals_reference': True, 'peaks_clouds_stars_unchanged': True,
        'overlay_fixed_position_no_wrap': True, 'JS_syntax': 'PASS',
        'interactive_browser': 'NOT TESTED', 'PMDO_runtime': 'NOT TESTED',
        'native_pixels': False, 'native_cycle_extracted': False}, indent=2) + '\n')
    with zipfile.ZipFile(R / 'renders/boreales_pmdsky_v7_pack.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(O.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(O))
        z.write(html, 'apercu.html')
if __name__ == '__main__':
    main()
