"""Finalise V4 : registre programme, verification.json, ZIP."""
from pathlib import Path
import json
import zipfile

R = Path(__file__).resolve().parents[2]
O = R / 'exports/zones_south_north_v4'


def main():
    prev = json.loads((R / 'exports/zones_south_north_v3/FULL_PROGRAMME_STATUS.json').read_text())
    new = {'entrancearidedungeonpmdsky.png': 'exports/zones_south_north_v4/arid_dungeon_entrance',
           'roadundergound.png': 'exports/zones_south_north_v4/violet_underground_road'}
    for r in prev['references']:
        if r['file'] in new:
            r['state'] = 'south_north_candidate'
            r['deliverable'] = new[r['file']]
    prev['counts'] = {'south_north_candidates': 4,
                      'BG_layout_candidates': 1,
                      'references_without_new_layout_meeting_current_direction': 16,
                      'duplicates': 1, 'not_a_map': 1}
    prev['latest_v4'] = ('Arid 408x560 + violet 504x488, PNG layers jour/nuit + paquet natif '
                         '.rsground/.tile pixel-identique. 16 layouts restants.')
    (O / 'FULL_PROGRAMME_STATUS.json').write_text(json.dumps(prev, ensure_ascii=False, indent=2) + '\n')
    report = {'batch_tests': 66 + 4,
              'checks': ['66 controles PNG (provenance/recomposition/nuit/chemin)',
                         '4 rendus .rsground natifs pixel-identiques aux composites (diff 0)'],
              'runtime': 'NOT TESTED',
              'limits': ('Chemin/connexite hors moteur uniquement ; collisions premiere passe ; '
                         'aucune destination de donjon liee ; pas d approbation artistique.'),
              'all_work_complete': False}
    (O / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    with zipfile.ZipFile(R / 'exports/zones_south_north_v4_pack.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(O.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(O))
    print('Registre, verification et ZIP V4 écrits.')


if __name__ == '__main__':
    main()
