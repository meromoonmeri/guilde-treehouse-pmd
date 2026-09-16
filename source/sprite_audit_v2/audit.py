"""Audit pinned tracker; *_files values are locks, NOT presence flags."""
import json, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'.cache/mega/tracker.json'
t=json.loads(p.read_text()); rows=[]
def walk(groups,path=(),names=()):
 for key,n in groups.items():
  ids=path+(key,); ns=names+(n['name'],)
  rows.append(dict(path='/'.join(ids),name=' / '.join(filter(None,ns)),canonical=n['canon'],base=len(ids)==1 and key!='0000',**{k:n.get(k) for k in ['sprite_required','sprite_complete','sprite_files','sprite_pending','portrait_required','portrait_complete','portrait_files','portrait_pending']}))
  walk(n['subgroups'],ids,ns)
walk(t)
missing=[r for r in rows if r['base'] and r['canonical'] and r['sprite_required'] and not r['sprite_files']]
portraits=[r for r in rows if r['base'] and r['canonical'] and r['portrait_required'] and 'Normal' not in r['portrait_files']]
result={'commit':'3609a86be2a4c8ad7cf255bd2255f044daafe24f','tracker_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'slots':len(rows),'base_missing_sprites':missing,'base_missing_normal_portrait':portraits,'all_slots':rows}
out=Path(__file__).parent
(out/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
(out/'README.md').write_text('# Audit SpriteCollab — 16 septembre 2026\n\nRévision `'+result['commit']+'`. Présence = clés des dictionnaires, valeurs = verrous.\n\n'+f'{len(rows)} slots (formes, genres et shinies inclus). {len(missing)} espèces de base sans sprite ; {len(portraits)} sans portrait Normal. Les émotions manquantes restent à produire même si Normal existe. Aucun fichier existant remplacé.\n\n'+ '\n'.join(f"- {r['path']} {r['name']}"+(' — proposition en attente, ne pas concurrencer' if r['sprite_pending'] else '') for r in missing)+'\n\nAbsence dans le tracker ≠ absence de travail privé. Le JSON contient les actions/émotions présentes et les propositions en attente pour chaque slot.\n')
print(len(rows),len(missing),len(portraits))
