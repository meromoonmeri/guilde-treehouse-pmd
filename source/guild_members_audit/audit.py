"""Read-only, pinned SpriteCollab inventory for the nine PMDO quest guild members.
Audits tracker keys + actual directory listings + AnimData.xml (including CopyOf).
No generated art, no inference of actual PMDO import/runtime success.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import base64, csv, hashlib, json, subprocess, urllib.request
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[2]
SRC=Path(__file__).parent
OUT=ROOT/'exports/guild_members_audit'
CACHE=ROOT/'.cache/guild_members_audit'
MEMBERS=[('0282','Gardevoir','Gardevoir'),('0083',"Farfetch’d",'Canarticho'),('0674','Pancham','Pandespiègle'),('0371','Bagon','Draby'),('0285','Shroomish','Balignon'),('0440','Happiny','Ptiravi'),('0417','Pachirisu','Pachirisu'),('0461','Weavile','Dimoret'),('0186','Politoed','Tarpaud')]
EXTRA=['0282/0002','0461/0001','0417/0000/0000/0002']
AUDIT=json.loads((ROOT/'source/sprite_audit_v2/audit.json').read_text())
PIN=AUDIT['commit']
ROWS={r['path']:r for r in AUDIT['all_slots']}
CONTRACT=json.loads((ROOT/'source/pmd_character_pipeline/contract.json').read_text())
EMOTIONS=CONTRACT['portrait']['required_full']
DUNGEON=CONTRACT['sprite']['completion_levels']['dungeon']
FULL=CONTRACT['sprite']['completion_levels']['full']


def listing(kind,slot):
    cache=CACHE/PIN/kind/slot/'listing.json'
    if not cache.exists():
        cache.parent.mkdir(parents=True,exist_ok=True)
        data=subprocess.check_output(['gh','api',f'repos/PMDCollab/SpriteCollab/contents/{kind}/{slot}?ref={PIN}'])
        cache.write_bytes(data)
    return {r['name']:r for r in json.loads(cache.read_text()) if r['type']=='file'}


def download(kind,slot,name,files):
    dest=SRC/'references'/slot/kind/name
    if name not in files:return None
    if not dest.exists():
        dest.parent.mkdir(parents=True,exist_ok=True)
        blob=json.loads(subprocess.check_output(['gh','api',f"repos/PMDCollab/SpriteCollab/git/blobs/{files[name]['sha']}"]))
        assert blob['encoding']=='base64'
        dest.write_bytes(base64.b64decode(blob['content']))
    raw=dest.read_bytes()
    assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==files[name]['sha'],str(dest)
    return dest


def xml_actions(path,files):
    root=ET.parse(path).getroot()
    nodes={n.findtext('Name'):n for n in root.findall('./Anims/Anim')}
    def resolve(name,trail=()):
        if name in trail:raise ValueError('CopyOf cycle: '+name)
        if name not in nodes:raise ValueError('CopyOf missing target: '+name)
        node=nodes[name];alias=node.findtext('CopyOf')
        return resolve(alias,trail+(name,)) if alias else (name,node)
    actions={}
    for name in nodes:
        try:
            target,n=resolve(name)
            triple=[f'{target}-{kind}.png' for kind in ['Anim','Offsets','Shadow']]
            missing=[p for p in triple if p not in files]
            actions[name]={'source_action':target,'copy_of':nodes[name].findtext('CopyOf'),'png_triple_present':not missing,'missing_files':missing,'cell':[int(n.findtext('FrameWidth')),int(n.findtext('FrameHeight'))],'durations_ticks':[int(d.text) for d in n.findall('./Durations/Duration')]}
        except (ValueError,TypeError) as e:actions[name]={'error':str(e),'png_triple_present':False}
    return actions


def inspect(slot):
    sprite=listing('sprite',slot)
    xml=download('sprite',slot,'AnimData.xml',sprite)
    download('sprite',slot,'credits.txt',sprite)
    actions=xml_actions(xml,sprite) if xml else {}
    base=slot in [p[0] for p in MEMBERS]
    portraits=listing('portrait',slot) if base else {}
    if base:
        download('portrait',slot,'credits.txt',portraits)
        for name in (['Normal.png','Inspired.png','Shouting.png','Surprised.png'] if slot=='0186' else ['Normal.png']):
            download('portrait',slot,name,portraits)
    idle=actions.get('Idle',{}).get('source_action','Idle')
    idle_sizes={}
    for kind in ['Anim','Offsets','Shadow']:
        p=download('sprite',slot,f'{idle}-{kind}.png',sprite)
        if p:
            with Image.open(p) as im:idle_sizes[kind]=list(im.size)
    idle_info=actions.get('Idle',{})
    idle_ok=len(idle_sizes)==3 and len({tuple(v) for v in idle_sizes.values()})==1
    if idle_ok:
        iw,ih=idle_sizes['Anim'];cw,ch=idle_info['cell']
        idle_ok=iw==cw*len(idle_info['durations_ticks']) and ih%ch==0 and ih//ch in (1,8)
    assert idle_ok, (slot,'Idle PNG geometry disagrees with XML')
    files=set(portraits)
    normal_missing=[n for n in EMOTIONS if n+'.png' not in files] if base else None
    report={'slot':slot,'name':ROWS[slot]['name'],'sprite_tracker_level':ROWS[slot]['sprite_complete'],'sprite_tracker_actions':list(ROWS[slot]['sprite_files']),'xml_actions':actions,'action_count':len(actions),'declared_actions_with_missing_triples':[n for n,a in actions.items() if not a['png_triple_present']],'missing_dungeon_actions':[n for n in DUNGEON if n not in actions or not actions[n]['png_triple_present']],'missing_project_full_actions':[n for n in FULL if n not in actions or not actions[n]['png_triple_present']],'idle_sheet_dimensions':idle_sizes,'idle_triple_geometry_verified':idle_ok,'portrait_files':sorted(files),'missing_required_portraits':normal_missing,'missing_reverse_portraits':[n+'^' for n in EMOTIONS if n+'^.png' not in files] if base else None,'optional_special_portraits':[n for n in ['Special0','Special1','Special2','Special3'] if n+'.png' in files],'sprite_pending':ROWS[slot]['sprite_pending'],'portrait_pending':ROWS[slot]['portrait_pending'],'proof_scope':'Directory existence for all declared triples; XML alias/frame declarations; actual decoding of representative Idle triple only. Not full frame-by-frame artwork or PMDO runtime verification.'}
    return slot,report


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    actual_head=subprocess.check_output(['gh','api','repos/PMDCollab/SpriteCollab/commits/master','--jq','.sha'],text=True).strip()
    if actual_head!=PIN:raise RuntimeError('Upstream changed; refresh source tracker before publishing a current audit')
    slots=[p[0] for p in MEMBERS]+EXTRA
    with ThreadPoolExecutor(max_workers=4) as pool:reports=dict(pool.map(inspect,slots))
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (SRC/'references').rglob('*') if p.is_file()}
    # Current quest integration cannot be inferred from generic source art presence.
    result={'date':'2026-09-17','commit':PIN,'upstream_head_matches_pin':True,'scope':'Nine explicitly named guild members, standard/base slots. Relevant cutscene and female variants inspected separately; no identity/gender decision invented.','contract_note':'The ten-action dungeon and 32-action full profiles are project targets. Missing full actions are not automatically requirements of every quest scene or upstream submission.','members':[{'english_name':en,'french_name':fr,**reports[slot]} for slot,en,fr in MEMBERS],'related_variants':[reports[s] for s in EXTRA],'other_variant_inventory':[{k:r[k] for k in ['path','name','sprite_required','portrait_required','sprite_files','portrait_files']} for r in AUDIT['all_slots'] if any(r['path'].startswith(s+'/') for s,_,_ in MEMBERS)],'reference_hashes':hashes,'downloaded_git_blobs_match_pinned_directory_shas':True,'PMDO_runtime':'NOT TESTED','quest_scene_action_requirements':'Not supplied / not mapped to scene scripts in this audit','generated_assets':0}
    result['recommended_work_order']=['Produce only the 12 missing Politoed portraits, preserving existing portraits.', 'Inspect/reuse Gardevoir and Weavile Cutscene assets before new scene drawings.', 'For the six scene-incomplete base slots, prioritize Nod/Pose/LookUp/Sit if called by guild dialogue scenes.', 'Add other scene actions only against the quest requirements; do not regenerate the three full-profile members.', 'Verify exact forms/genders and actual Ground/Dungeon integration.']
    result['totals']={'members':9,'missing_required_portraits':sum(len(r['missing_required_portraits']) for r in result['members']),'missing_dungeon_actions':sum(len(r['missing_dungeon_actions']) for r in result['members']),'missing_base_project_full_actions':sum(len(r['missing_project_full_actions']) for r in result['members']),'broken_declared_triples':sum(len(r['declared_actions_with_missing_triples']) for r in result['members'])}
    (OUT/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    with (OUT/'summary.csv').open('w',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['slot','pokemon','fr','portraits_present_of_16','missing_portraits','xml_actions','missing_dungeon','missing_project_full','missing_reverse_candidates'])
        for r in result['members']:
            w.writerow([r['slot'],r['english_name'],r['french_name'],16-len(r['missing_required_portraits']),';'.join(r['missing_required_portraits']),r['action_count'],';'.join(r['missing_dungeon_actions']),';'.join(r['missing_project_full_actions']),';'.join(r['missing_reverse_portraits'])])
    write_report(result)
    print(json.dumps(result['totals'],indent=2))


def write_report(result):
    text='# Guilde PMDO — audit prioritaire des neuf membres\n\n'
    text+='**17 septembre 2026 · formes standard/base.** SpriteCollab HEAD revérifié : `'+PIN+'`. Portraits existants et crédits conservés ; aucune génération ni modification de sprite.\n\n'
    text+='## Conclusion\n\n'
    text+='- **Priorité portrait : Politoed / Tarpaud**, seul membre auquel il manque des émotions parmi les 16du contrat. Ne pas refaire ses quatre portraits existants ni ceux des huit autres membres.\n'
    text+='- Les neuf membres ont les 10actions du profil donjon du projet. Aucun nouveau sprite de base/Idle/Walk n’est à créer simplement pour combler une absence.\n'
    text+='- Pour un jeu de 32 actions incluant les scènes, Bagon, Happiny et Pachirisu (slot de base) sont complets. Les six autres ont des lacunes de scènes à comparer aux besoins réels de la quête.\n\n'
    text+='| Membre | Portraits /16 | Actions XML disponibles | Donjon /10 | Manques du profil 32 |\n|---|---:|---:|---:|---:|\n'
    for r in result['members']:
        text+=f"| {r['english_name']} ({r['french_name']}) | {16-len(r['missing_required_portraits'])}/16 | {r['action_count']} | {10-len(r['missing_dungeon_actions'])}/10 | {len(r['missing_project_full_actions'])} |\n"
    pol=next(r for r in result['members'] if r['slot']=='0186')
    text+='\n## P1 — Tarpaud : émotions à produire\n\n**Déjà disponibles :** '+', '.join(n[:-4] for n in pol['portrait_files'] if n.endswith('.png') and not n.endswith('^.png'))+'.\n\n**Manquants :** '+', '.join(pol['missing_required_portraits'])+'.\n\nPartir du Normal natif, conserver son anatomie et produire des expressions animales naturelles sur les fonds canoniques correspondants. Les quatre portraits existants restent intacts. Les autres membres n’ont pas besoin de nouveaux portraits pour couvrir les 16émotions.\n'
    text+='\n## P2 — Scènes de guilde à compléter selon le scénario\n\n'
    for r in result['members']:
        if r['missing_project_full_actions']:
            text+=f"### {r['english_name']} / {r['french_name']}\n\n"+', '.join(r['missing_project_full_actions'])+'.\n\n'
    text+='Le total des manques des **slots de base** est '+str(result['totals']['missing_base_project_full_actions'])+' actions pour ce profil 32. Ce n’est pas une preuve que la quête utilise toutes ces actions ni qu’il faut toutes les générer : établir la correspondance avec les scènes avant production. Un `CopyOf` valide compte comme disponible, mais pas comme un dessin d’animation distinct. Les replis automatiques du moteur ne constituent pas une animation spécifique créée.\n'
    text+='\n## Ressources à réutiliser avant de générer\n\n'
    for r in result['related_variants']:
        extra=[n for n in r['xml_actions'] if n not in result['members'][[m['slot'] for m in result['members']].index(r['slot'].split('/')[0])]['xml_actions']]
        text+=f"- **{r['name']} (`{r['slot']}`)** : {r['action_count']} actions déclarées ; ajouts par rapport à la base : "+(', '.join(extra) or 'aucun')+'. '
        if 'Female' in r['name']:text+='Cette variante femelle n’a pas nécessairement les mêmes scènes que la base ; vérifier le sexe voulu du membre. '
        text+='Ne pas substituer silencieusement cette variante : comparer apparence, direction, repères et crédits.\n'
    text+='\nGardevoir possède notamment un dossier Cutscene ; Weavile aussi. Farfetch’d est ici la forme standard, pas celle de Galar. Les variantes shiny, femelles, alternatives et Méga restent listées en annexe JSON, mais ne sont pas choisies à la place des membres sans indication.\n'
    text+='\n## Vues inversées des portraits\n\n'
    for r in result['members']:
        text+=f"- {r['english_name']} : {16-len(r['missing_reverse_portraits'])}/16 fichiers `^` présents.\n"
    text+='\nAbsence de fichier `^` ne signifie pas automatiquement portrait obligatoire manquant : vérifier l’asymétrie, les accessoires (poireau/feuille notamment) et le rendu côté dialogue. Ne pas fabriquer des miroirs automatiques présentés comme des dessins vérifiés. Les Special sont optionnels, hors total 16.\n'
    text+='\n### Ordre conseillé pour les animations\n\nAprès vérification des variantes Cutscene, commencer par les gestes de dialogue **Nod, Pose, LookUp** et la posture **Sit** si les scènes de guilde les appellent. Ensuite seulement les repas/sommeil/chutes et autres actions spécifiques au scénario. Ne pas recréer ces ressources pour Draby, Ptiravi ou Pachirisu de base : elles existent déjà.\n'
    text+='\n## P3 — Intégration dans la quête\n\nVérifier les IDs Pokémon/formes/genres, les noms de portraits et actions appelés par les scripts, puis les ancrages, directions, collisions et déclenchements Ground/Dungeon dans PMDO. **Aucun test en jeu n’a été effectué pour ces neuf membres.**\n\nCet audit contrôle les clés du tracker (les valeurs sont des verrous), les listings réels, les XML et leurs alias ainsi que la présence des triples de PNG déclarés. Seuls les triples Idle représentatifs ont été téléchargés et décodés : ce n’est pas une validation graphique image par image de toutes les animations. Les XML, crédits et Normal natifs sont conservés sous `source/guild_members_audit/references/`, avec hashes dans `audit.json`.\n'
    text+='\n## Correction Carapagos conservée\n\nLes portraits approuvés à bouche ouverte sont réussis car ils suivent une référence canonique **sans dents visibles** : ils restent inchangés. La règle est la fidélité anatomique, pas une interdiction générale d’ouvrir le bec. Les paupières seules convenaient au dernier lot fermé ; une ouverture naturelle du bec est autorisée lorsque l’émotion et la référence la justifient.\n'
    (OUT/'README.md').write_text(text)
    # Native portraits only, copied visually without altering credited files.
    board=Image.new('RGB',(720,480),(20,29,43));draw=ImageDraw.Draw(board)
    for i,r in enumerate(result['members']):
        x=i%3*240;y=i//3*160
        p=SRC/'references'/r['slot']/'portrait/Normal.png'
        if p.exists():board.paste(Image.open(p).convert('RGB').resize((120,120),Image.Resampling.NEAREST),(x+8,y+28))
        draw.text((x+8,y+6),r['english_name'],fill='white')
        draw.text((x+137,y+50),f"{16-len(r['missing_required_portraits'])}/16",fill=(173,224,208))
        draw.text((x+137,y+70),'portraits',fill=(180,199,214))
    board.save(OUT/'native_normal_overview.png')

if __name__=='__main__':main()
