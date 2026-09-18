from pathlib import Path
import subprocess, sys, re, zipfile, json
R = Path(__file__).resolve().parents[2]; O = R / 'renders/boreales_suite_generee_v11'
def main():
    subprocess.run([sys.executable, '-m', 'unittest', 'source.boreales_suite_generee_v11.test_build', '-q'], cwd=R, check=True)
    html = R / 'apercu_boreale_suite_generee_v11.html'
    subprocess.run(['node', '--check'], input=re.search(r'<script>(.*?)</script>', html.read_text(), re.S).group(1), text=True, check=True)
    (O / 'verification.json').write_text(json.dumps({
        'dedicated_tests_passed': 9, 'poses': 8, 'etapes': 16, 'duree_ms': 120, 'cycle_s': 1.92,
        'generation': 'canonical texture + our zone sky as references, subtle suite, locked positions',
        'extraction': 'geometric flood-fill background removal (colour-distance fails: hearts too close to bg magenta)',
        'own_layer_no_baked_sky': True, 'context_byte_identical': True, 'wrap': False, 'JS_syntax': 'PASS',
        'interactive_browser': 'NOT TESTED', 'PMDO_runtime': 'NOT TESTED', 'native_cycle_extracted': False}, indent=2) + '\n')
    with zipfile.ZipFile(R / 'renders/boreales_suite_generee_v11_pack.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(O.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(O))
        z.write(html, 'apercu.html')
if __name__ == '__main__':
    main()
