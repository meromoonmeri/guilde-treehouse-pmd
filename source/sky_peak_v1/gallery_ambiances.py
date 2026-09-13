from pathlib import Path
import json,re,base64
R=Path(__file__).resolve().parents[2];O=R/'renders/sky_peak_ambiances_v2';m=json.loads((O/'manifest.json').read_text())
def uri(p):return 'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()
data={'modes':{s['id']:{n:uri(O/s['id']/(n+'.png')) for n in s['layers'] if n!='07_fleurs'} for s in m['modes']},'flowers':{s['id']:[uri(O/s['id']/'fleurs'/f'{f:02}.png') for f in range(32)] for s in m['modes']},'reference':uri(R/'source/sky_peak_v1/gif_0.png')}
h=(R/'apercu_sky_peak_canonique_v1.html').read_text()
h=re.sub(r'const D=.*?;function im',lambda _: 'const D='+json.dumps(data)+';function im',h,count=1,flags=re.S)
options=''.join('<option value="'+s['id']+'"'+(' selected' if s['id']=='crepuscule' else '')+'>'+s['title']+'</option>' for s in m['modes'])
h=re.sub(r'<select id="mode">.*?</select>','<select id="mode">'+options+'</select>',h,count=1)
h=h.replace("mode='jour'","mode='crepuscule'").replace('03_lune_halo','03_astre_halo').replace("'Lune et halo'","'Soleil / lune et halo'")
h=h.replace('Sky Peak · layout de référence','Sky Peak · prairie élargie et cinq ambiances').replace('Sky Peak — la falaise de la référence','Sky Peak — légère variation de la référence')
h=h.replace('La géométrie de la falaise vient directement du GIF : aucune nouvelle disposition de plateau. Fleurs assorties sur un calque animé, panorama montagneux et deux couches de nuages indépendantes.','La référence reste la base. Les bordures sont écartées de 12 pixels au maximum pour élargir doucement la prairie centrale, sans nouvelle terrasse ni relief ajouté. Aube, jour, crépuscule, heure bleue et nuit gardent leurs calques séparés.')
h=h.replace('Terrain 504×504 sans redimensionnement.','Toile 504×504, faible redistribution horizontale nearest des pixels source ; aucune modification verticale.')
h=h.replace('Leur emplacement n’est pas redistribué.','Leur placement suit le léger élargissement du terrain.')
(R/'apercu_sky_peak_ambiances_v2.html').write_text(h,encoding='utf8')
