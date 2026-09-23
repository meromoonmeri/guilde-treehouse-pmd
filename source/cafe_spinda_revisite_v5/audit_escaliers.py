"""Audit N/S placements using the chosen entrance, not the rejected lateral study.
Exports are reproducible from V4. Raster continuity is NOT engine collision validation.
"""
from pathlib import Path
import sys,json,hashlib,copy
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[2];O=R/'renders/cafe_spinda_revisite_v5/audit';sys.path.insert(0,str(R))
from source.cafe_spinda_reseau_v4.build import base
SOURCES={'accueil':'accueil_spinda_fidele','casino':'casino_spinda_fidele','cafe':'cafe_spinda_corrige'}
LEVELS={'accueil':0,'casino':-1,'salon_bas':-1,'cafe':1,'salon_haut':1}
TITLES={'accueil':'Accueil · RDC (0)','casino':'Casino · sous-sol (−1)','cafe':'Café · étage (+1)'}

def port(direction,action,target,target_port,trigger,spawn):
 return {'direction':direction,'action':action,'target':target,'target_port':target_port,'trigger':trigger,'arrival_spawn':spawn,'arrival_facing':'S' if direction=='N' else 'N'}
PORTS={
 'accueil':{'N':port('N','montee','cafe','S',[304,64],[304,160]),'S':port('S','descente','casino','N',[304,376],[304,304])},
 'casino':{'N':port('N','montee','accueil','S',[304,64],[304,160])},
 'cafe':{'S':port('S','descente','accueil','N',[304,384],[304,312])}}

def graph_check(ports):
 assert sum(map(len,ports.values()))==4
 for room,ps in ports.items():
  for name,p in ps.items():
   assert name==p['direction'] and name in ('N','S')
   diff=LEVELS[p['target']]-LEVELS[room]
   assert diff==(1 if name=='N' else -1)
   assert p['action']==('montee' if diff==1 else 'descente')
   q=ports[p['target']][p['target_port']]
   assert q['target']==room and q['target_port']==name
   assert p['target_port']==('S' if name=='N' else 'N')
   assert p['direction']==q['arrival_facing']
   for x,y in [p['trigger'],p['arrival_spawn']]:assert x%8==y%8==0

def assets():
 original={k:base(k,v) for k,v in SOURCES.items()};src=Image.fromarray(original['accueil'])
 # Remove ONLY surrounding floor corners from this architectural module.
 # All actual tread pixels are kept at their existing V4 size, with no rotation.
 step=src.crop((232,316,368,396));mask=Image.new('L',step.size)
 ImageDraw.Draw(mask).polygon([(30,0),(106,0),(136,26),(136,80),(0,80),(0,26)],fill=255)
 a=np.array(step);a[np.array(mask)==0]=0;step=Image.fromarray(a)
 landing=src.crop((268,264,332,320));left=src.crop((248,336,264,392));right=src.crop((336,336,352,392))
 rooms={}
 for name,orig in original.items():
  a=orig.copy()
  if name in ('accueil','casino'):
   # Stop cutting at y128: cutting to y136 used to leave a magenta seam
   # between the last tread (ending y133) and the existing indoor floor.
   a[:128,268:332]=0;im=Image.fromarray(a)
   for asset,pos in [(landing,(268,0)),(left,(252,0)),(right,(332,0)),(step,(232,56))]:im.alpha_composite(asset,pos)
  else:
   # Open only the walking strip, not a broad polygon that cuts the shoulders.
   a[334:410,268:332]=0;im=Image.fromarray(a);im.alpha_composite(step,(232,324))
  rooms[name]=np.array(im)
 return original,rooms,step

def raster_check(original,rooms):
 src=original['accueil'];core=src[338:392,268:336]
 for name,a in rooms.items():
  assert a.shape==(448,600,4) and set(np.unique(a[:,:,3]))<={0,255}
  region=np.zeros((448,600),bool)
  if name in ('accueil','casino'):
   region[:136,232:368]=True
   assert np.array_equal(a[78:132,268:336],core),name+' N treads changed'
   assert np.all(a[:168,280:320,3]==255),name+' N walking strip has an alpha hole'
   assert np.array_equal(a[134:152,280:320],original[name][134:152,280:320]),name+' N foot must meet original floor'
   # The higher north landing and rock cheeks are present all the way to the edge.
   assert np.all(a[:56,268:332,3]==255)
   assert np.array_equal(a[:56,268:332],src[264:320,268:332])
   assert np.array_equal(a[56:134,280:320],src[316:394,280:320])
   assert np.all(a[:56,256:264,3]==255) and np.all(a[:56,336:344,3]==255)
  else:
   region[324:410,232:368]=True
   assert np.array_equal(a[346:400,268:336],core),'cafe S treads changed'
   assert np.all(a[304:400,280:320,3]==255),'cafe S walking strip has an alpha hole'
  assert np.array_equal(a[~region],original[name][~region]),name+' changed outside entrance area'
  for p in PORTS[name].values():
   for label in ('trigger','arrival_spawn'):
    x,y=p[label];assert np.all(a[y-8:y+8,x-8:x+8,3]==255),(name,label,'16px footprint')
 assert np.array_equal(rooms['accueil'][300:],src[300:]),'original south entrance must stay intact'
 assert np.array_equal(rooms['accueil'][338:392,268:336],core)
 assert np.all(rooms['accueil'][304:392,280:320,3]==255)

def illustration(rooms):
 font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
 font=lambda n:ImageFont.truetype(font_path,n)
 board=Image.new('RGB',(1800,650),'#211a14');d=ImageDraw.Draw(board)
 d.text((22,10),'AUDIT DES ACCÈS · NORD = MONTÉE / SUD = DESCENTE',font=font(25),fill='#f5d49b')
 d.text((22,47),'Même escalier de référence · aucun escalier latéral · repères non imprimés dans les exports PNG',font=font(16),fill='#d3c1a5')
 for i,name in enumerate(SOURCES):
  x=i*600;y=116;a=rooms[name];im=Image.new('RGBA',(600,448),'magenta');im.alpha_composite(Image.fromarray(a));board.paste(im,(x,y))
  d.text((x+18,80),TITLES[name],font=font(23),fill='#fff2d8')
  for side,p in PORTS[name].items():
   px,py=p['trigger'];px+=x;py+=y;color='#58e8d0'
   d.ellipse((px-9,py-9,px+9,py+9),outline=color,width=3)
   tip=py-33 if side=='N' else py+33
   d.line((px,py,px,tip),fill=color,width=3)
   back=tip+10 if side=='N' else tip-10
   d.polygon([(px,tip),(px-7,back),(px+7,back)],fill=color)
  texts=[]
  for side,p in PORTS[name].items():
   target={'cafe':'café +1','casino':'casino −1','accueil':'accueil 0'}[p['target']]
   texts.append(f"{side} : {p['action'].upper()} → {target}")
  for j,text in enumerate(texts):d.text((x+18,576+j*24),text,font=font(18),fill='#f6dfb8')
 d.text((22,629),'Placement et continuité d’image contrôlés. Warps, collisions et arrivée extérieure : non configurés dans PMDO.',font=font(15),fill='#d3c1a5')
 board.save(O/'Audit_escaliers_nord_sud.jpg',quality=82,optimize=True)

def main():
 O.mkdir(parents=True,exist_ok=True);exports=O/'exports';exports.mkdir(exist_ok=True)
 original,rooms,step=assets();graph_check(PORTS);raster_check(original,rooms)
 # Negative controls ensure the checker catches the earlier kinds of error.
 wrong=copy.deepcopy(PORTS);wrong['accueil']['N']['action']='descente'
 try:graph_check(wrong)
 except AssertionError:pass
 else:raise AssertionError('inverted ascent was not detected')
 broken={k:v.copy() for k,v in rooms.items()};broken['accueil'][134:136,280:320]=0
 try:raster_check(original,broken)
 except AssertionError:pass
 else:raise AssertionError('foot-of-stair hole was not detected')
 for name,a in rooms.items():
  im=Image.fromarray(a);im.save(exports/f'SpindaV5_audit_{name}_transparent.png',optimize=True)
  bg=Image.new('RGBA',im.size,'magenta');bg.alpha_composite(im);bg.save(exports/f'SpindaV5_audit_{name}_magenta.png',optimize=True)
  assert np.array_equal(np.array(Image.open(exports/f'SpindaV5_audit_{name}_transparent.png')),a)
 step.save(exports/'SpindaV5_escalier_reference.png',optimize=True)
 illustration(rooms)
 plan={'status':'Audited placement design, not installed PMDO warps','size':[600,448],'grid':8,'levels':LEVELS,'stairs':PORTS,'stair_links':[['accueil','N','cafe','S'],['accueil','S','casino','N']],'same_level_links':[['casino','E','salon_bas','W'],['cafe','E','salon_haut','W']],'external_access':'UNDEFINED: these two reception exits are inter-floor links, not an exterior entrance. Do not add a third exit without agreement.','reference':{'map':'renders/cafe_spinda_reseau_v4/bruts/accueil_spinda_fidele.webp','kind':'chosen generated entrance, NOT a certified native sprite','scene_scale':'existing V4 600x448','crop':[232,316,368,396],'actual_treads':[268,338,336,392],'north_position':[232,56],'cafe_south_position':[232,324],'rotation':0,'extra_resampling':False},'proposed_spawns':'16px opaque raster footprint only; collision/actor size must be tested in engine','decoration':'omitted to inspect architecture; other V5 furnishing work remains pending'}
 (O/'plan_escaliers.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
 report={'pass':True,'scope':'Four architectural stair placements, graph and raster continuity; NOT an engine collision or art approval test.','checks':['N always increases level by one; S always decreases it','both stair links reciprocal: accueil N ↔ café S, accueil S ↔ casino N','all four tread regions RGBA-identical to the reference; no rotation or stretching','reference accueil south entrance entirely unchanged','north landings and cheeks reach the edge; the final tread joins the original floor without a magenta seam','40px central strips continuously opaque and 16px trigger/spawn footprints on opaque surfaces','no changes outside the three entrance edit boxes; existing east/west corridors unaffected','inverted ascent and a deliberately inserted alpha seam correctly rejected'],'map_rgba_sha256':{name:hashlib.sha256(a.tobytes()).hexdigest() for name,a in rooms.items()},'limits':['No PMDO runtime, collision, warp or NPC test','No graphical browser test','Exterior access not defined','Full furnishing/decorative V5 delivery still pending']}
 (O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print('PASS: 4 N/S placements; 2 reciprocal stair links; reference treads exact; no alpha gaps; 2 negative controls. PMDO NOT TESTED.')
 print('Audit image bytes:',(O/'Audit_escaliers_nord_sud.jpg').stat().st_size)
if __name__=='__main__':main()
