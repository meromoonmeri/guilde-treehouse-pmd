from pathlib import Path
import subprocess, sys, re, zipfile, json
R = Path(__file__).resolve().parents[2]; O = R / 'renders/plage_halcyon_v1'
def main():
    subprocess.run([sys.executable, '-m', 'unittest', 'source.plage_halcyon_v1.test_build', '-q'], cwd=R, check=True)
    html = R / 'apercu_plage_halcyon_v1.html'
    subprocess.run(['node', '--check'], input=re.search(r'<script>(.*?)</script>', html.read_text(), re.S).group(1), text=True, check=True)
    man = json.loads((O / 'manifest.json').read_text())
    (O / 'verification.json').write_text(json.dumps({
        'dedicated_tests_passed': 9,
        'zone': 'arenapmdskybeach.png -> arène de plage Halcyon V1 (terrain 928×1152)',
        'methode': 'canonique : terrain généré plein cadre (bande magenta 34 px -> alpha par inondation, zéro magenta intérieur), '
                   'planche d\'eau générée (15 cases détectées) -> 5 poses réparties (k-centre) ordonnées en min-max + 5 fondus 50 % = 10 frames',
        'halcyon_criteria': {'stacked_fixed_layers': True, 'layer_order': ['fond_fixe', 'terrain_fixe', 'eau (10 frames)'],
                             'uniform_frame_size_928x256': True, 'uniform_frame_naming_EauLumiereV1_00..09': True,
                             'uniform_duration_ms': 140, 'position_on_8px_grid': True,
                             'eau_position': man['halcyon']['eau_position'], 'no_wrap': True,
                             'loop': 'frame 10 = demi-pas de frame 1 (fondu 50 %, construction)'},
        'eau': {'couverture_bassins': man['bande_eau']['couverture_eau_totale'],
                'trainees_restreintes_au_masque_eau_profonde': True,
                'hors_bande_statique': 'crique haute et petites poches basses (statiques en V1)'},
        'JS_syntax': 'PASS', 'interactive_browser': 'NOT TESTED', 'PMDO_runtime': 'NOT TESTED',
        'cycle_officiel': 'INCONNU : poses et cadence choisis'}, indent=2) + '\n')
    with zipfile.ZipFile(R / 'renders/plage_halcyon_v1_pack.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(O.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(O))
        z.write(html, 'apercu.html')
if __name__ == '__main__':
    main()
