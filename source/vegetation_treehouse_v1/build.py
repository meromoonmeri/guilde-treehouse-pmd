"""Generated plants -> alpha/native palette -> anchored wind poses -> 8px tilesheets.
Ground vegetation, not portrait/sprite actor sheets or a claimed PMDO runtime import.
"""
from pathlib import Path
import json,math,base64,hashlib,sys,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];SRC=Path(__file__).parent;OUT=ROOT/'exports/vegetation_treehouse_v1'
REF=ROOT/'source/amp_plains_fleurie_v1/references'
# Native Halcyon foliage values, plus restrained authored bark/gold/berry accents.
PALETTE=np.array([(57,74,41),(74,90,49),(82,107,57),(99,123,66),(99,132,82),(123,156,74),(165,189,115),(99,74,41),(156,107,49),(206,156,74),(181,74,198),(207,94,198),(222,148,247),(247,206,231),(247,181,115),(247,222,115),(215,173,66),(181,74,66),(231,107,87),(41,57,25)],dtype=np.int32)
ASSETS=[
 dict(id='grass_fine',label='Herbe fine',file='grasses_ferns',grid=[3,2],row=0,columns=[0,1,2],target=[16,20],anchor='bottom'),
 dict(id='fern',label='Fougere',file='grasses_ferns',grid=[3,2],row=1,columns=[0,1,2],target=[24,18],anchor='bottom'),
 dict(id='violet_bells',label='Cloches violettes',file='flowers',grid=[6,2],row=0,columns=[0,1,2],target=[22,24],anchor='bottom'),
 dict(id='golden_flowers',label='Fleurs dorees',file='flowers',grid=[6,2],row=1,columns=[0,1,2],target=[22,24],anchor='bottom'),
 dict(id='round_bush',label='Buisson rond',file='bushes',grid=[3,2],row=0,columns=[0,1,2],target=[28,24],anchor='bottom'),
 dict(id='berry_bush',label='Buisson a baies',file='bushes',grid=[3,2],row=1,columns=[0,1,2],target=[26,24],anchor='bottom'),
 dict(id='leafy_branch',label='Branche feuillue',file='branches',grid=[5,2],row=0,columns=[0],target=[24,24],anchor='bottom'),
 dict(id='hanging_ivy',label='Lierre suspendu',file='branches',grid=[5,2],row=1,columns=[0],target=[24,24],anchor='top'),
]
SEQUENCE=[0,1,0,2];TICKS=[14]*4
GIF_MS=[230,240,230,230];TILED_MS=[233,234,233,233]

def key(im,allow_purple=False):
 a=np.array(im.convert('RGBA'));r,g,b=a[:,:,:3].astype(np.int32).transpose(2,0,1)
 if allow_purple:
  # Remove magenta matte/fringe, not ordinary violet petals with substantial green/blue bias.
  matte=(np.minimum(r,b)>65)&(np.minimum(r,b)>g*2.4)&(np.abs(r-b)<35)
 else:
  matte=(np.minimum(r,b)>55)&(r>g*1.45)&(b>g*1.45)
 a[matte]=0;a[~matte,3]=255
 return Image.fromarray(a)

def extract(spec):
 raw=Image.open(SRC/'generation'/f"{spec['file']}.png");cols,rows=spec['grid'];frames=[];anchors=[];boxes=[]
 for c in spec['columns']:
  box=(round(c*raw.width/cols)+6,round(spec['row']*raw.height/rows)+6,round((c+1)*raw.width/cols)-6,round((spec['row']+1)*raw.height/rows)-6)
  im=key(raw.crop(box),spec['id']=='violet_bells');bounds=im.getbbox();assert bounds is not None
  a=np.array(im);ys,xs=np.where(a[:,:,3]>0)
  if spec['anchor']=='bottom':anchor=(float(np.median(xs[ys>=ys.max()-3])),int(ys.max()))
  else:anchor=(float(np.median(xs[ys<=ys.min()+3])),int(ys.min()))
  frames.append(im);anchors.append(anchor);boxes.append(bounds)
 left=max(an[0]-b[0] for an,b in zip(anchors,boxes));right=max(b[2]-1-an[0] for an,b in zip(anchors,boxes))
 scale=min(spec['target'][0]/max(b[2]-b[0] for b in boxes),spec['target'][1]/max(b[3]-b[1] for b in boxes),14/max(1,left),14/max(1,right))
 target=(16,28) if spec['anchor']=='bottom' else (16,3);clean=[]
 for im,anchor in zip(frames,anchors):
  w=max(1,round(im.width*scale));h=max(1,round(im.height*scale));small=im.resize((w,h),Image.Resampling.NEAREST)
  pos=(target[0]-round(anchor[0]*w/im.width),target[1]-round(anchor[1]*h/im.height));canvas=Image.new('RGBA',(32,32));canvas.alpha_composite(small,pos)
  a=np.array(canvas);opaque=a[:,:,3]>0;rgb=a[:,:,:3].astype(np.int32)
  allowed=list(range(10))+[19]
  if spec['id']=='violet_bells':allowed+=list(range(10,14))
  elif spec['id']=='golden_flowers':allowed+=list(range(14,17))
  elif spec['id']=='berry_bush':allowed+=list(range(17,19))
  palette=PALETTE[allowed]
  a[:,:,:3]=palette[np.argmin(((rgb[:,:,None,:]-palette[None,None,:,:])**2).sum(axis=3),axis=2)];a[~opaque]=0;clean.append(Image.fromarray(a))
 # Rebuild branch/ivy movement from one neutral design: generated extra poses inverted topology.
 authored_wind=len(clean)==1 or spec['id']=='golden_flowers'
 if authored_wind:
  # Generated golden flowers swapped relative stem heights; retain the neutral topology.
  original=np.array(clean[0]);clean=[clean[0]]
  for direction in [1,-1]:
   result=np.zeros_like(original)
   for y in range(32):
    weight=max(0,min(1,(26-y)/22)) if spec['anchor']=='bottom' else max(0,min(1,(y-5)/22))
    shift=round(direction*2*weight)
    if shift>=0:result[y,shift:]=original[y,:32-shift]
    else:result[y,:shift]=original[y,-shift:]
   clean.append(Image.fromarray(result))
 # Fixed contact region, shared palette, binary alpha. Never move the whole plant.
 neutral=np.array(clean[0]);result=[]
 for im in clean:
  a=np.array(im)
  if spec['anchor']=='bottom':a[26:]=neutral[26:]
  else:a[:6]=neutral[:6]
  a[a[:,:,3]==0]=0;result.append(Image.fromarray(a))
 assert len({im.tobytes() for im in result})==3,(spec['id'],'three distinct wind drawings required')
 return result,{'source_layout':spec['grid'],'source_columns':spec['columns'],'source_row':spec['row'],'source_crop_bounds':boxes,'source_anchors':anchors,'scale':scale,'fixed_anchor':target,'anchor_mode':spec['anchor'],'motion':'Native-scale row articulation from generated neutral; mirrored/inconsistent raw poses discarded' if authored_wind else 'Three generated wind poses, individually registered then native palette and fixed-contact cleanup'}

def animated(frames,path,duration=GIF_MS):
 frames[0].save(path,save_all=True,append_images=frames[1:],duration=duration,loop=0,disposal=2)

def main():
 for folder in ['tilesheets','plants','editable','review']:(OUT/folder).mkdir(parents=True,exist_ok=True)
 assets=[];sheets=[Image.new('RGBA',(128,64)) for _ in range(4)];boards=[]
 for i,spec in enumerate(ASSETS):
  poses,info=extract(spec);x=i%4*32;y=i//4*32
  for p,im in enumerate(poses):im.save(OUT/'editable'/f"VT1_{spec['id']}_pose_{p}.png")
  preview=[]
  for f,p in enumerate(SEQUENCE):
   im=poses[p];sheets[f].paste(im,(x,y));im.save(OUT/'plants'/f"VT1_{spec['id']}_phase_{f}.png")
   bg=Image.new('RGBA',(32,32),(28,39,32,255));bg.alpha_composite(im);preview.append(bg.convert('RGB').resize((192,192),Image.Resampling.NEAREST))
  animated(preview,OUT/'review'/f"VT1_{spec['id']}.gif")
  assets.append({**spec,**info,'rect':[x,y,32,32],'placement_tile_size':8,'subtiles':[4,4],'sequence':SEQUENCE,'durations_game_ticks':TICKS,'phase_offset_suggestion':i%4,'art_approved':False})
 atlas=Image.new('RGBA',(512,64))
 for f,im in enumerate(sheets):im.save(OUT/'tilesheets'/f'VT1_vegetation_phase_{f}.png');atlas.paste(im,(f*128,0))
 atlas.save(OUT/'tilesheets/VT1_vegetation_animated_atlas.png')
 for f,sheet in enumerate(sheets):
  board=Image.new('RGB',(640,400),(28,39,32));draw=ImageDraw.Draw(board)
  for i,spec in enumerate(ASSETS):
   x=i%4*160;y=i//4*200;tile=Image.new('RGBA',(32,32),(28,39,32,255));tile.alpha_composite(sheet.crop((i%4*32,i//4*32,i%4*32+32,i//4*32+32)));board.paste(tile.convert('RGB').resize((160,160),Image.Resampling.NEAREST),(x,y+28));draw.text((x+5,y+6),spec['label'],fill='white')
  boards.append(board)
 boards[0].save(OUT/'review/VT1_contact_neutral.png');animated(boards,OUT/'review/VT1_all_plants.gif')
 all_poses=Image.new('RGB',(640,1120),(28,39,32));draw=ImageDraw.Draw(all_poses)
 for i,asset in enumerate(assets):
  x,y,w,h=asset['rect']
  for f,sheet in enumerate(sheets):
   tile=Image.new('RGBA',(32,32),(28,39,32,255));tile.alpha_composite(sheet.crop((x,y,x+w,y+h)));all_poses.paste(tile.convert('RGB').resize((128,128),Image.Resampling.NEAREST),(f*160,i*140+12));draw.text((f*160+3,i*140),asset['id']+' / '+str(f),fill='white')
 all_poses.save(OUT/'review/VT1_all_phases.png')
 # Placement demo on an existing native ground texture; not a finished map or building.
 grass=Image.open(REF/'vast_herbe_48.png').convert('RGBA');scene_frames=[];sites=[(15,55),(72,35),(125,48),(201,30),(38,112),(132,107),(190,112)]
 for f in range(4):
  scene=Image.new('RGBA',(256,160))
  for y in range(0,160,48):
   for x in range(0,256,48):scene.alpha_composite(grass,(x,y))
  for i,(x,y) in enumerate(sites):
   idx=[0,1,2,3,4,5,0][i];r=assets[idx]['rect'];phase=(f+i)%4;scene.alpha_composite(sheets[phase].crop((r[0],r[1],r[0]+32,r[1]+32)),(x,y-28))
  scene_frames.append(scene.convert('RGB').resize((768,480),Image.Resampling.NEAREST))
 animated(scene_frames,OUT/'review/VT1_ground_demo.gif')
 native=Image.open(REF/'Vast_Steppe_Flower_Animations.png').convert('RGBA');reference=[]
 for p in SEQUENCE:
  im=Image.new('RGBA',(24,24),(28,39,32,255));im.alpha_composite(native.crop((p*24,0,p*24+24,24)));reference.append(im.convert('RGB').resize((144,144),Image.Resampling.NEAREST))
 animated(reference,OUT/'review/Halcyon_flower_reference.gif')
 # Animated Tiled tileset at real 8px grid; every base subtile participates, including empty ones.
 ts=ET.Element('tileset',version='1.10',tiledversion='1.10.2',name='VT1_vegetation',tilewidth='8',tileheight='8',tilecount='512',columns='64')
 ET.SubElement(ts,'image',source='VT1_vegetation_animated_atlas.png',width='512',height='64')
 for y in range(8):
  for x in range(16):
   tile=ET.SubElement(ts,'tile',id=str(y*64+x));animation=ET.SubElement(tile,'animation')
   for f,ms in enumerate(TILED_MS):ET.SubElement(animation,'frame',tileid=str(y*64+x+f*16),duration=str(ms))
 ET.indent(ts);ET.ElementTree(ts).write(OUT/'tilesheets/VT1_vegetation_8px.tsx',encoding='utf-8',xml_declaration=True)
 placements=[]
 for asset in assets:
  x,y,w,h=asset['rect'];cells=[]
  for dy in range(4):
   for dx in range(4):cells.append({'local_cell':[dx,dy],'frames':[{'Sheet':f'VT1_vegetation_phase_{f}','TexLoc':{'X':x//8+dx,'Y':y//8+dy}} for f in range(4)],'duration_game_frames':14})
  placements.append({'id':asset['id'],'anchor':asset['fixed_anchor'],'cells':cells})
 (OUT/'placement_recipe.json').write_text(json.dumps({'grid_pixels':8,'scope':'Placement recipe only; not an imported PMDO map or compiled .tile asset','objects':placements},indent=2)+'\n')
 native_prov=json.loads((REF/'provenance.json').read_text());native_prov=[p for p in native_prov if p['path'].endswith(('Vast_Steppe_Flower_Animations.tile','Vast_Steppe_Objects.tile','Vast_Steppe_Base.tile'))]
 report={'scope':'First animated vegetation kit for PMD-style treehouse surroundings, eight original plant designs. Structures not produced in this lot.','workflow':'Native Halcyon reference -> generator on magenta -> alpha -> native-size palette/registration -> fixed contact cleanup -> wind cycle -> tilesheets/GIFs','source_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (SRC/'generation').glob('*.png')},'native_reference_provenance':native_prov,'palette':PALETTE.tolist(),'palette_note':'Seven foliage values from native Halcyon flower/leaf reference; remaining deep shade and bark/flower/berry accents adapted for this kit. Not a portrait15-color constraint.','assets':assets,'phase_sheet_size':[128,64],'animated_atlas_size':[512,64],'grid':8,'phase_count':4,'unique_pose_count':3,'sequence':SEQUENCE,'duration_game_ticks':TICKS,'gif_duration_ms':GIF_MS,'tiled_duration_ms':TILED_MS,'runtime_PMDO':'NOT TESTED','runtime_Tiled':'NOT TESTED','art_approved':False,'technical_precheck':'PENDING TESTS'}
 (OUT/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 sys.path.insert(0,str(ROOT))
 from source.vegetation_treehouse_v1.verify import verify
 verify();report['technical_precheck']='PASS';gallery(report)
 print('Eight plants, four phase sheets, three unique wind poses each; roots/pivots fixed.')

def gallery(report):
 def uri(p):return 'data:image/'+('gif' if p.suffix=='.gif' else 'png')+';base64,'+base64.b64encode(p.read_bytes()).decode()
 html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Végétation animée · Kit treehouse PMD</title><style>body{font:16px system-ui;max-width:1100px;margin:32px auto;padding:0 24px;background:#17271f;color:#eef5e8}h1{font-size:34px}p,li{color:#b9cfb2;line-height:1.7}section{background:#20372a;padding:22px;border-radius:16px;margin:24px 0}img{max-width:100%;image-rendering:pixelated}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:18px}.note{border-left:3px solid #e1c879;padding:16px}code{color:#f0dfaf}</style><h1>Végétation animée pour la guilde treehouse</h1><p>Premier lot : huit éléments indépendants, palette végétale PMD, grille8px, racines ou attache fixes et vent discret. Trois poses en boucle0/1/0/2, à14ticks par étape, suivant la cadence de la référence Halcyon inspectée.</p><section><h2>Les huit plantes</h2><img alt="Végétation animée complète" src="'''+uri(OUT/'review/VT1_all_plants.gif')+'"></section><section><h2>Essai de placement sur herbe native</h2><img alt="Démo de végétation sur texture PMD" src="'+uri(OUT/'review/VT1_ground_demo.gif')+'"><p>Décalages de phase entre les touffes. Ce n’est pas une map finale ni une scène intégrée dans PMDO.</p></section><div class="grid">'
 for a in report['assets']:html+='<section><h3>'+a['label']+'</h3><img alt="'+a['label']+' au vent" src="'+uri(OUT/'review'/f"VT1_{a['id']}.gif")+'"></section>'
 html+='</div><section><h2>Référence native Halcyon</h2><img alt="Fleurs Halcyon natives" src="'+uri(OUT/'review/Halcyon_flower_reference.gif')+'"><p>Vast Steppe, ressource native attribuée à Halcyon et ses artistes, pas notre création. Sert de référence de palette, d’échelle et de rythme.</p></section><section><h2>Tilesheets livrées</h2><p>4PNG de phases128×64, atlas animé512×64,32PNG individuels, calques de poses, tileset Tiled8px avec animations et recette de placement PMDO. Aucun faux binaire .tile.</p><img alt="Atlas des quatre phases" src="'+uri(OUT/'tilesheets/VT1_vegetation_animated_atlas.png')+'"></section><p class="note">Lot candidat : contrôle local de géométrie, alpha et ancrages ; art et import/runtime PMDO/Tiled non approuvés. QG treehouse et annexes restent à dessiner. Les autres travaux de guilde ne sont pas annulés.</p></html>'
 (ROOT/'apercu_vegetation_treehouse_v1.html').write_text(html)
if __name__=='__main__':main()
