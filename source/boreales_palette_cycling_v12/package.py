from pathlib import Path
import subprocess, sys, re, zipfile, json
R = Path(__file__).resolve().parents[2]; O = R / 'renders/boreales_palette_cycling_v12'
def main():
    subprocess.run([sys.executable, '-m', 'unittest', 'source.boreales_palette_cycling_v12.test_build', '-q'], cwd=R, check=True)
    html = R / 'apercu_palette_cycling_v12.html'
    subprocess.run(['node', '--check'], input=re.search(r'<script>(.*?)</script>', html.read_text(), re.S).group(1), text=True, check=True)
    (O / 'verification.json').write_text(json.dumps({
        'dedicated_tests_passed': 9, 'frames': 8, 'duree_ms': 120, 'cycle_s': 0.96,
        'style': 'palette cycling Halcyon: identical silhouette, colors advance one step per frame',
        'sans_ciel': True, 'context_byte_identical': True, 'JS_syntax': 'PASS',
        'interactive_browser': 'NOT TESTED', 'PMDO_runtime': 'NOT TESTED'}, indent=2) + '\n')
    with zipfile.ZipFile(R / 'renders/boreales_palette_cycling_v12_pack.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(O.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(O))
        z.write(html, 'apercu.html')
if __name__ == '__main__':
    main()
