from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
from scipy import ndimage as nd
R=Path(__file__).resolve().parents[2];O=R/'renders/siphons_ecoulement_v3';P=O/'siphons_ecoulement';OLD=R/'renders/eau_siphons_rapides_v2/eau_siphons_rapides';m=json.loads((O/'manifest.json').read_text())
def load(p):return Image.open(p).convert('RGBA')
f=np.load(O/'CHAMP_ECOULEMENT.npz');u,v,wet,sink,solid=[f[n] for n in ['u','v','wet','sink','solid']]
uf=np.zeros_like(u,dtype=bool);vf=np.zeros_like(v,dtype=bool);uf[:,1:-1]=wet[:,:-1]&wet[:,1:];uf[:,0]=wet[:,0];uf[:,-1]=wet[:,-1];vf[1:-1]=wet[:-1]&wet[1:];vf[0]=wet[0];vf[-1]=wet[-1]
assert np.all(u[~uf]==0) and np.all(v[~vf]==0)
residual=(u[:,1:]-u[:,:-1]+v[1:]-v[:-1]+sink)[wet];assert np.max(np.abs(residual))/sink.max()<1e-8
inflow=u[:,0].sum()-u[:,-1].sum()+v[0].sum()-v[-1].sum();assert np.isclose(inflow,sink.sum(),rtol=1e-8)
tr=np.load(O/'TRACEURS_CONTROLE.npz');active=tr['alpha']>0
for n in ['heads','tails']:
 pts=tr[n][active]/2;xs=np.clip(pts[:,0].astype(int),0,wet.shape[1]-1);ys=np.clip(pts[:,1].astype(int),0,wet.shape[0]-1);assert np.all(wet[ys,xs]),n
static={n:load(P/f'siphons_v3_{n}.png') for n in m['static_layers']};seen=set();interior=nd.distance_transform_edt(solid)>3
for n in ['04_rochers_arriere','05_rochers_avant','06_galet_decale','07_chaussee_surface','08_chaussee_rebords']:
 a=np.array(static[n]);b=np.array(load(OLD/f'siphons_v2_{n}.png'));assert np.array_equal(a[:,:,3],b[:,:,3]);assert np.array_equal(a[interior],b[interior])
terrain=Image.new('RGBA',tuple(m['size']))
for n,im in static.items():
 if n!='03_ombres_contact':terrain.alpha_composite(im)
for i in range(m['frames']):
 c=Image.new('RGBA',tuple(m['size']))
 for n in m['render_order']:
  im=static[n] if n in static else load(P/f'siphons_v3_{n}_{i:03}.png');c.alpha_composite(im)
  if n=='02_filets_courant':assert not np.any(np.array(im)[:,:,3][solid])
  if n=='09_reflets_rives':assert np.array(im)[:,:,3].max()<=28
 a=np.array(c);assert np.array_equal(a,np.array(load(P/f'siphons_v3_scene_{i:03}.png')));assert np.all(a[:,:,3]==255)
 assert np.array_equal(a[interior],np.array(terrain)[interior]);seen.add(hashlib.sha256(a.tobytes()).hexdigest())
assert len(seen)==m['frames']
m['tests'].update({'all_128_saved_frames_recompose':True,'128_unique_full_frames':True,'independent_mass_balance_and_zero_solid_flux_checks':True,'all_visible_tracer_endpoints_in_fluid':True,'rock_and_causeway_alpha_unchanged':True,'dry_interiors_unchanged_all_frames':True,'shore_reflection_alpha_at_most_28':True})
(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print(json.dumps(m['tests'],indent=2))
