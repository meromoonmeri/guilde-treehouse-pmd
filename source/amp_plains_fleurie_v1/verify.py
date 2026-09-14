"""Independent pixel, geometry and timeline checks; not PMDO runtime validation."""
from pathlib import Path
import json,io,zipfile,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from scipy import ndimage as nd
R=Path(__file__).resolve().parents[2];O=R/'renders/amp_plains_fleurie_v1';P=O/'amp_plains_fleurie';REF=Path(__file__).parent/'references';m=json.loads((O/'manifest.json').read_text())
def a(p):return np.array(Image.open(p).convert('RGBA'))
for p in P.glob('*.png'):assert Image.open(p).size==(456,408),p
original=a(R/'Amp_Plains_entrance_TD.png');rr,gg,bb=original[:,:,:3].astype(float).transpose(2,0,1);gray=(bb>=rr)&(bb>=.86*gg);dead=a(O/'MASQUE_ANCIENS_ARBRES_RETIRES.png')[:,:,0]>0
rock=np.maximum.reduce([a(P/f'amp_fleurie_{n}.png')[:,:,3] for n in m['static_layers'] if any(s in n for s in ['falaises','rochers'])])>0
assert np.array_equal(rock,gray&~dead)
for t in range(2):
 info=m['tree_sources'][t];x0,y0,x1,y1=info['source_box'];b=info['trim_box'];sources=[a(REF/f'vast_steppe_layer_{k}.png')[y0:y1,x0:x1][b[1]:b[3],b[0]:b[2]] for k in [3,4]]
 sprite=a(O/f'sprites/arbre_pmd_{t:02}.png');match=np.logical_or.reduce([np.all(sprite==s,axis=2) for s in sources]);assert np.all(match[sprite[:,:,3]>0])
atlas=a(REF/'Vast_Steppe_Flower_Animations.png')
for phase,pose in enumerate([0,1,0,2]):assert np.array_equal(a(O/f'sprites/fleur_vast_phase_{phase:02}.png'),atlas[:,pose*24:(pose+1)*24])
events=m['timeline'];assert sum(e['duration_game_frames'] for e in events)==1120;assert sum(e['duration_ms'] for e in events)==18667;assert len(events)==272
for e in events:
 t=e['game_frame'];im=Image.new('RGBA',(456,408))
 for name in m['static_layers']:im.alpha_composite(Image.open(P/f'amp_fleurie_{name}.png').convert('RGBA'))
 for g in m['animation_groups']:im.alpha_composite(Image.open(P/g['files'][(t//g['native_frame_length_game_frames'])%4]).convert('RGBA'))
 assert np.array_equal(np.array(im),a(P/e['png']));assert np.all(np.array(im)[:,:,3]==255)
with zipfile.ZipFile(P/'amp_plains_fleurie.ora') as z:
 im=Image.new('RGBA',(456,408))
 for l in reversed(ET.fromstring(z.read('stack.xml')).find('stack')):im.alpha_composite(Image.open(io.BytesIO(z.read(l.get('src')))).convert('RGBA'))
 assert np.array_equal(np.array(im),a(P/'COMPOSITION.png'))
walk=a(O/'PASSAGE_CENTRAL_CONTROLE.png')[:,:,0]>0;tree=np.maximum.reduce([a(P/f'amp_fleurie_10_arbre_pmd_{k:02}.png')[:,:,3] for k in range(2)])>0;assert not np.any(walk&(tree|rock))
print('PASS: native tree RGB/coordinates, flower sequence, exact rock geometry, 272 timeline events, opaque compositions, ORA, 24px open corridor. No runtime test.')
