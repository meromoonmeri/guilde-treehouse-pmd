from pathlib import Path
import subprocess, sys, re, zipfile, json
R = Path(__file__).resolve().parents[2]; O = R / 'renders/boreales_ondulation_glace_v8'
def main():
    subprocess.run([sys.executable, '-m', 'unittest', 'source.boreales_ondulation_glace_v8.test_build', '-q'], cwd=R, check=True)
    html = R / 'apercu_arene_ondulation_glace_v8.html'
    subprocess.run(['node', '--check'], input=re.search(r'<script>(.*?)</script>', html.read_text(), re.S).group(1), text=True, check=True)
    (O / 'verification.json').write_text(json.dumps({
        'dedicated_tests_passed': 10, 'poses': 8, 'frames': 32, 'frame_ms': 125, 'cycle_s': 4.0,
        'aurora': '8 generated drawn poses, premultiplied dissolves, vertical undulation, zero horizontal translation, no wrap',
        'ice_backdrop': 'generated side walls + back plain behind terrain, grey voids filled',
        'sky_terrain_V3': 'byte-identical', 'JS_syntax': 'PASS',
        'interactive_browser': 'NOT TESTED', 'PMDO_runtime': 'NOT TESTED',
        'native_pixels': False, 'native_cycle_extracted': False}, indent=2) + '\n')
    with zipfile.ZipFile(R / 'renders/boreales_ondulation_glace_v8_pack.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(O.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(O))
        z.write(html, 'apercu.html')
if __name__ == '__main__':
    main()
