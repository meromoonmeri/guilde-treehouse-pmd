from pathlib import Path
import io,json,zipfile,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/antre_harmonie_v3';P=O/'antre';REF=Path(__file__).parent/'references';m=json.loads((O/'manifest.json').read_text())
def im(p):return Image.open(p).convert('RGBA')
def a(p):return np.array(im(p))
static={n:im(P/f'harmonie_{n}.png') for n in m['static']};rock=np.maximum.reduce([np.array(static[n])[:,:,3] for n in m['static'] if n.startswith(('02','03','04','05'))])>0;dry=np.maximum.reduce([np.array(static[n])[:,:,3] for n in m['static'] if n.startswith(('06','07','08'))])>0
for phase in range(12):
 ls=dict(static)
 for n in m['animated']:
  ls[n]=im(P/f'harmonie_{n}_{phase:02}.png');aa=np.array(ls[n]);assert ls[n].size==(480,312)
  if n!='00_eau_altere':assert not np.any(aa[:,:,3][rock|dry])
 out=Image.new('RGBA',(480,312))
 for n in m['order']:out.alpha_composite(ls[n])
 assert np.array_equal(np.array(out),a(P/f'harmonie_composition_{phase:02}.png'));assert np.all(np.array(out)[:,:,3]==255)
for n in m['animated']:
 period=3 if 'ecume' in n else 4
 for p in range(12):assert np.array_equal(a(P/f'harmonie_{n}_{p:02}.png'),a(P/f'harmonie_{n}_{p%period:02}.png'))
proof=json.loads((REF/'timing_proof.json').read_text());assert {s['FrameLength'] for s in proof}=={10};assert {len(s['Frames']) for s in proof if s['layer']==1}=={4};assert {len(s['Frames']) for s in proof if s['layer']==6}=={3}
for k in range(3):assert np.array_equal(a(O/f'sprites/pas_japonais_natif_{k}.png'),a(REF/'altere_layer_5.png')[392+24*k:416+24*k,528:560])
ref=a(R/'source/cote_v5_expeditions/audit/Halcyon__crooked_cavern_entrance_layer_0.png')[:110];colors=set(map(tuple,ref[:,:,:3].reshape(-1,3)))
for n in ['02_paroi_fond','03_bordure_gauche','04_bordure_droite','05_rebord_bas']:
 aa=np.array(static[n]);assert set(map(tuple,aa[:,:,:3][aa[:,:,3]>0])).issubset(colors)
with zipfile.ZipFile(P/'antre_harmonie.ora') as z:
 out=Image.new('RGBA',(480,312))
 for layer in reversed(ET.fromstring(z.read('stack.xml')).find('stack')):out.alpha_composite(im(io.BytesIO(z.read(layer.get('src')))))
 assert np.array_equal(np.array(out),a(P/'COMPOSITION.png'))
assert sum(m['durations_ms'])==2000
print('PASS:23aligned layers,12states, native4/3periods at10gameframes, exact native step pixels, Crooked palette membership, no water effects over rocks/platform, exact ORA. No runtime test.')
