"""Global SpriteCollab missing-resource inventory, not an artwork completion claim.
Input: pinned, flattened upstream tracker. Dictionary values are lock flags.
Non-required slots and optional actions are kept visible, not silently omitted.
"""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import html
import json

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'exports/spritecollab_global'
STATES = ['to_produce', 'generated', 'technical_pass', 'art_approved', 'runtime_verified']


def classify(row, contract):
    sprite = row.get('sprite_files') or {}
    portraits = row.get('portrait_files') or {}
    required = contract['portrait']['required_full']
    pending = bool(row.get('sprite_pending') or row.get('portrait_pending'))
    missing = [name for name in required if name not in portraits]
    required_sprite = bool(row['sprite_required'])
    required_portrait = bool(row['portrait_required'])
    absent = required_sprite and not sprite
    incomplete = required_sprite and bool(sprite) and row['sprite_complete'] < 2
    needs_work = absent or incomplete or (required_portrait and bool(missing))
    return {
        'slot': row['path'], 'name': row['name'], 'canonical': row['canonical'],
        'base': row['base'], 'sprite_required': required_sprite,
        'portrait_required': required_portrait,
        'sprite_upstream_level': row['sprite_complete'],
        'portrait_upstream_level': row['portrait_complete'],
        'sprite_entirely_absent': absent,
        'sprite_incomplete_upstream': incomplete,
        'existing_actions': list(sprite), 'existing_portraits': list(portraits),
        'missing_required_portraits': missing,
        'missing_reverse_portraits': [n + '^' for n in required if n + '^' not in portraits],
        'optional_special_portraits_absent': [n for n in contract['portrait']['emotions'] if n not in required and n not in portraits],
        'project_full_action_gaps_not_upstream_requirements': [n for n in contract['sprite']['completion_levels']['full'] if n not in sprite],
        'sprite_pending': row.get('sprite_pending') or {},
        'portrait_pending': row.get('portrait_pending') or {},
        'coordination_required': pending,
        'needs_work': needs_work,
        'production_state': 'to_produce' if needs_work else 'no_core_gap_detected',
        'gate': 'coordinate_upstream_pending' if pending else ('reference_and_art_review' if needs_work else 'optional_variants_review'),
    }


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    audit_path = ROOT / 'source/sprite_audit_v2/audit.json'
    audit = json.loads(audit_path.read_text())
    contract = json.loads((ROOT / 'source/pmd_character_pipeline/contract.json').read_text())
    rows = [classify(r, contract) for r in audit['all_slots']]
    assert len(rows) == len({r['slot'] for r in rows}) == audit['slots']
    counts = {
        'slots_inventoried': len(rows),
        'required_sprite_slots': sum(r['sprite_required'] for r in rows),
        'required_portrait_slots': sum(r['portrait_required'] for r in rows),
        'entirely_absent_required_sprite_sets': sum(r['sprite_entirely_absent'] for r in rows),
        'incomplete_existing_required_sprite_sets': sum(r['sprite_incomplete_upstream'] for r in rows),
        'required_portrait_slots_with_missing_emotions': sum(r['portrait_required'] and bool(r['missing_required_portraits']) for r in rows),
        'missing_required_normal_orientation_portraits': sum(len(r['missing_required_portraits']) for r in rows if r['portrait_required']),
        'missing_reverse_portraits_candidates_not_automatic_flips': sum(len(r['missing_reverse_portraits']) for r in rows if r['portrait_required']),
        'slots_with_core_work': sum(r['needs_work'] for r in rows),
        'slots_with_pending_upstream_submissions': sum(r['coordination_required'] for r in rows),
        'new_completed_assets_from_this_audit': 0,
    }
    report = {
        'scope': 'ALL SpriteCollab slots, species/forms/genders/shinies and noncanonical entries; overrides previous project-only choice',
        'date': '2026-09-17', 'commit': audit['commit'],
        'upstream_head_checked': '2026-09-17 using gh api; same commit as pinned audit',
        'input_audit_sha256': hashlib.sha256(audit_path.read_bytes()).hexdigest(),
        'tracker_sha256': audit['tracker_sha256'], 'counts': counts,
        'production_states': STATES,
        'rules': [
            'Presence means dictionary keys, never truthiness of lock values.',
            'No existing native file may be overwritten by this queue.',
            'No catalogue entry silently excluded; required=false is visible and needs applicability review.',
            'Sprite completion follows upstream level<2, not the project-specific 32-action profile.',
            'The 32-action project gaps are informational, NOT proof of a missing upstream-required action.',
            '16 required portrait emotions are the project contract. Four Special expressions are optional and recorded separately.',
            'Reverse portraits need asymmetry review; no blind horizontal flipping.',
            'Pending upstream submissions require coordination before competing production.',
            'Generated drafts and previously delivered local work are not automatically treated as upstream-complete.',
            'This manifest is an inventory, not a running background production job.',
        ], 'slots': rows,
    }
    (OUT / 'backlog.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    with (OUT / 'backlog.csv').open('w', newline='') as f:
        columns = ['slot', 'name', 'canonical', 'sprite_required', 'portrait_required', 'sprite_entirely_absent', 'sprite_incomplete_upstream', 'missing_required_portraits', 'missing_reverse_portraits', 'coordination_required', 'production_state']
        writer = csv.DictWriter(f, columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: ';'.join(row[k]) if isinstance(row[k], list) else row[k] for k in columns})
    text = '# SpriteCollab — périmètre global confirmé\n\n'
    text += '**Toute la collection**, et non plus seulement la liste du projet. Révision vérifiée : `' + audit['commit'] + '`.\n\n'
    text += '| Inventaire | Nombre |\n|---|---:|\n'
    labels = ['Entrées inventoriées (formes, genres, shinies compris)', 'Entrées déclarées requises pour les sprites', 'Entrées déclarées requises pour les portraits', 'Jeux de sprites requis entièrement absents', 'Jeux de sprites existants mais incomplets selon le tracker', 'Entrées portrait requises avec émotions manquantes', 'Portraits manquants parmi les 16 émotions du contrat', 'Vues inverses manquantes à examiner séparément', 'Entrées avec travail principal identifié', 'Entrées avec propositions upstream en attente', 'Créations terminées par cet inventaire']
    for label, count in zip(labels, counts.values()): text += f'| {label} | {count} |\n'
    text += '\n## Lecture et limites\n\nLes totaux incluent les variantes : ce ne sont pas des nombres de Pokémon distincts. Toutes les 5 640 entrées figurent dans le JSON/CSV, y compris celles marquées non requises. Ces dernières nécessitent un examen de pertinence avant de fabriquer des doublons. Les quatre expressions Special et les vues inverses sont suivies séparément.\n\nLes manques du profil **32 actions du projet** ne sont pas les exigences officielles de chaque sprite SpriteCollab ; ils sont donc informatifs, pas comptés comme autant de créations obligatoires absentes. Les niveaux de complétion du tracker sont conservés. Les valeurs des dictionnaires sont des verrous, jamais des indicateurs de présence.\n\n## Production\n\nProgression distincte : à produire → généré → validation technique → validation artistique → test moteur. Aucun passage automatique de généré à terminé. Les propositions upstream en attente bloquent une production concurrente sans coordination. Les originaux, crédits et portraits approuvés sont conservés. Les essais locaux Zarude/Stellaire/Méga-Raichu en cours restent des brouillons, pas des trous déclarés comblés.\n\nFichiers : `backlog.json` (détail), `backlog.csv` (tableur), `apercu_spritecollab_global.html` à la racine (recherche et filtres). Reconstruction : `python source/sprite_audit_v2/global_backlog.py`. Ce plan ne lance pas de production autonome en arrière-plan.\n'
    (OUT / 'README.md').write_text(text)
    compact = [{k: r[k] for k in ['slot', 'name', 'sprite_entirely_absent', 'sprite_incomplete_upstream', 'missing_required_portraits', 'portrait_required', 'coordination_required', 'needs_work']} for r in rows]
    page = '''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SpriteCollab — production globale</title><style>body{background:#121b29;color:#e8f1f8;font:16px system-ui;margin:30px auto;max-width:1200px;padding:0 20px}h1{font-size:36px}p{color:#b2c5d5;line-height:1.6}input,select{font:inherit;padding:12px;margin:6px 8px 16px 0;background:#213047;color:white;border:1px solid #52647a;border-radius:6px}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:12px;border-bottom:1px solid #354255;font-size:14px}th{color:#a1dccd}a{color:#a1dccd}.note{padding:16px;border-left:3px solid #e4b779;background:#202b39}</style><h1>SpriteCollab · toute la collection</h1><p>Inventaire global : Pokémon, formes, genres et shinies. Les ressources existantes restent intactes. Ce tableau décrit le travail à faire, pas des créations déjà terminées.</p><p class="note">Les expressions listées utilisent le contrat de 16 émotions. « Incomplet » suit le niveau du tracker ; il ne signifie pas que les 32 actions du projet sont obligatoires partout. Les entrées non requises restent dans l’inventaire.</p><input id="search" placeholder="Pokémon, forme ou numéro…" aria-label="Rechercher"><select id="filter" aria-label="Filtrer"><option value="work">Travail principal identifié</option><option value="all">Toutes les entrées</option><option value="absent">Sprites entièrement absents</option><option value="partial">Sprites existants incomplets</option><option value="portrait">Portraits manquants</option><option value="pending">Propositions en attente</option></select><p id="count"></p><table><thead><tr><th>Slot</th><th>Pokémon / forme</th><th>Sprites</th><th>Émotions manquantes</th><th>Coordination</th></tr></thead><tbody id="rows"></tbody></table><script>'''
    page += 'const DATA=' + json.dumps(compact, ensure_ascii=False).replace('<', '\\u003c') + ';'
    page += '''function update(){const q=document.getElementById('search').value.toLocaleLowerCase(),f=document.getElementById('filter').value;const rows=DATA.filter(r=>(r.slot+' '+r.name).toLocaleLowerCase().includes(q)&&(f==='all'||f==='work'&&r.needs_work||f==='absent'&&r.sprite_entirely_absent||f==='partial'&&r.sprite_incomplete_upstream||f==='portrait'&&r.portrait_required&&r.missing_required_portraits.length||f==='pending'&&r.coordination_required));document.getElementById('count').textContent=rows.length+' entrées correspondantes · '+Math.min(rows.length,200)+' affichées (affiner la recherche pour les suivantes)';const body=document.getElementById('rows');body.replaceChildren();rows.slice(0,200).forEach(r=>{let tr=document.createElement('tr');[r.slot,r.name,r.sprite_entirely_absent?'Absent':r.sprite_incomplete_upstream?'Incomplet':'Voir inventaire',r.portrait_required?r.missing_required_portraits.join(', '):'Non requis selon tracker',r.coordination_required?'Proposition en attente':'—'].forEach(v=>{let td=document.createElement('td');td.textContent=v;tr.append(td)});body.append(tr)})}document.getElementById('search').oninput=update;document.getElementById('filter').onchange=update;update();</script></html>'''
    (ROOT / 'apercu_spritecollab_global.html').write_text(page)
    print(json.dumps(counts, indent=2))


if __name__ == '__main__':
    build()
