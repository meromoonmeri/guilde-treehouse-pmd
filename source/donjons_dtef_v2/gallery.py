from pathlib import Path
import json,base64,re
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];O=R/'renders/donjons_dtef_v2';m=json.loads((O/'manifest.json').read_text());v=json.loads((O/'verification.json').read_text());data={};relative={}
labels={'foret':'Forêt — Relic Forest / Treeshroud','jungle':'Jungle — Southern Jungle','marais':'Marais — Murky Forest','roche':'Roche — Southern Cavern','cristal':'Cristal — Crystal Cave','glace':'Glace — Vast Ice Mountain','volcan':'Volcan — Dark Crater','desert':'Désert — Quicksand Cave','ruines':'Ruines — Sealed Ruin','vapeur':'Vapeur — Steam Cave','illuminant_reference':'Référence — Illuminant / Sky Peak4'}
for e in m['themes']:
 for mode in ['jour','nuit']:
  id=f'd2_{e["id"]}_{mode}';images={};rel={}
  for f in e['files']:
   p=O/'RAW/TileDtef'/id/f;images[f]='data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode();rel[f]=f'RAW/TileDtef/{id}/{f}'
  entry={**e,'id':id,'title':labels[e['id']]+' · '+mode,'kind':'Tuiles natives ; texture bombing limité aux sols statiques V1/V2' if e['bomb_stamps'] else 'Référence native intacte, hors filtre nuit','images':images};data[id]=entry;relative[id]={**entry,'images':rel}
old=(R/'source/dungeon_autotiles_v1/gallery.py').read_text();h=old.split("h='''",1)[1].split("'''",1)[0]
h=h.replace('Autotiles de donjon · forêt, eau, sakura','Dix biomes — vrais gabarits DTEF PMDO')
h=h.replace('Six prototypes sur les gabarits natifs : trois variantes chromatiques et trois essais de matières générées. Tuiles24×24,47 configurations, variantes et couches animées distinctes. Les séquences sources gardent leur cadence indépendante.','Dix donjons existants, plus la référence Illuminant Riverbed. Géométries et animations natives conservées ; texture bombing localisé sur les variantes de certains sols. Même mapping DTEF que Sakura : mur / secondaire / sol,6×8cases par type. Jour et nuit Abyss.')
h=h.replace('47 masques,204 feuilles DTEF,2829 copies de tuiles/frames sources, alpha inchangé, bordures de4px protégées après recoloration, noms et cadences sans ambiguïté.',f'47masques, {v["dtef_pngs"]} feuilles DTEF jour/nuit, {v["native_tile_frame_records"]} références de tuiles/frames ; alpha et bordures4px conservés. Animations natives intactes de jour. Aucun test PMDO.')
h=h.replace('Sources : audinowho/DumpAsset (Apple Woods, Beach Cave) et RogueCollab/RogueEssence (importeur DTEF). Les matières inédites sont reprojetées dans les intérieurs des tuiles ; les géométries natives de raccord et les animations d’eau sont conservées. Les motifs générés ne sont pas des ressources canoniques originales.','Sources : zones Halcyon réellement inspectées, ressources natives DumpAsset et importeur RogueEssence. Relic Forest emploie Treeshroud Forest1 ; Illuminant Riverbed emploie Sky Peak4th Pass. Les patchs de sol adaptés ne sont pas des pixels canoniques intacts. Import DTEF24px via RAW/TileDtef ; pas le découpage générique8px de la V1.')
h=h.replace("themes.value='sakura_printemps'","themes.value='d2_foret_jour'")
h=h.replace('<option value="sheet">','<option value="before">Carte sans variations — V0 seule</option><option value="sheet">')
h=h.replace("mode==='map'?576:432","(mode==='map'||mode==='before')?576:432").replace("mode==='map'?432:192","(mode==='map'||mode==='before')?432:192")
h=h.replace("draw('tileset_'+v+'.png',sx,sy,x,y);anim(v,sx,sy,x,y)","const chosen=mode==='before'?0:v;draw('tileset_'+chosen+'.png',sx,sy,x,y);anim(chosen,sx,sy,x,y)")
(R/'apercu_donjons_dtef_v2.html').write_text(h.replace('__DATA__',json.dumps(data)))
(O/'apercu_dtef.html').write_text(h.replace('__DATA__',json.dumps(relative)))
board=Image.new('RGB',(1440,492),(23,28,36));d=ImageDraw.Draw(board)
for i,e in enumerate(m['themes'][:10]):
 x=i%5*288;y=i//5*246;d.text((x+5,y+6),e['id']+' / '+e['source'],fill='white');im=Image.open(O/'apercus'/f'd2_{e["id"]}_jour/COMPOSITION.png').convert('RGB').resize((288,216),Image.Resampling.NEAREST);board.paste(im,(x,y+30))
board.save(O/'VUE_10_DONJONS.png');print('Gallery built')
