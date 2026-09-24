"""Galerie autonome V4 : calques activables, jour/nuit, trajet indicatif."""
from pathlib import Path
import base64
import json

R = Path(__file__).resolve().parents[2]
OUT = R / 'exports/zones_south_north_v4'


def uri(p):
    return 'data:image/png;base64,' + base64.b64encode(p.read_bytes()).decode()


def main():
    man = json.loads((OUT / 'manifest.json').read_text())
    data = []
    for info in man['maps']:
        d = OUT / info['id']
        data.append(dict(id=info['id'], title=info['title'], size=info['size'],
                         entrances=info['entrances'], notes=info['notes'],
                         route=uri(d / 'access_review_NOT_RUNTIME.png'),
                         layers=[dict(id=l['id'], jour=uri(d / l['file_jour']),
                                       nuit=uri(d / l['file_nuit']))
                                 for l in info['layers']]))
    html = """<!doctype html><html lang="fr"><meta charset="utf-8">""" \
        """<title>Sud-Nord V4 · entree aride + couloir violet</title><style>""" \
        """body{background:#1c1a20;color:#e6e2d8;font:16px system-ui;max-width:1250px;""" \
        """margin:32px auto;padding:20px}p{line-height:1.6;color:#c9c4b4}""" \
        """.maps{display:flex;flex-wrap:wrap;gap:24px}article{background:#2a2733;""" \
        """border:1px solid #5a5470;border-radius:12px;padding:18px;width:560px;""" \
        """box-sizing:border-box}canvas{max-width:100%;image-rendering:pixelated;""" \
        """background:#454047}label{display:inline-block;margin:8px;font-size:13px}""" \
        """h2{font-size:23px}small{color:#edcf83}details{margin:18px 0}""" \
        """button{margin:8px;padding:6px 14px;border-radius:8px;border:1px solid #5a5470;""" \
        """background:#3a3648;color:#e6e2d8;cursor:pointer}</style>""" \
        """<h1>Sud → nord V4 · deux nouvelles entrees</h1>""" \
        """<p>Entree aride 408×560 (sable, paroi ocre, bouche au nord, arbres morts) et """ \
        """couloir violet 504×488 (parois violettes, deux bouches, eboulis). Pixels natifs """ \
        """des references PMD Sky (translation seule), sols quiltes sans fondu, nuit Abyss """ \
        """exacte. Paquet natif .rsground + .tile verifie pixel-identique aux composites.</p>""" \
        """<div class="maps" id="maps"></div><script>const data=""" + \
        json.dumps(data, ensure_ascii=False) + """;for(const s of data){""" \
        """const a=document.createElement('article');a.innerHTML='<h2>'+s.title+'</h2><small>NORD · """ \
        """GROTTE ↑<br>'+s.size.join(' × ')+' px · SUD : arrivee au bas</small>';""" \
        """const c=document.createElement('canvas');c.width=s.size[0];c.height=s.size[1];a.append(c);""" \
        """const controls=document.createElement('div');a.append(controls);""" \
        """const btn=document.createElement('button');btn.textContent='Passer en nuit';""" \
        """let mode='jour';a.append(btn);""" \
        """const ctx=c.getContext('2d'),imgs={},checks=[];""" \
        """function draw(){ctx.clearRect(0,0,c.width,c.height);s.layers.forEach((l,i)=>{""" \
        """const im=imgs[mode+i];if(checks[i].checked&&im.complete)ctx.drawImage(im,0,0)})}""" \
        """btn.onclick=()=>{mode=mode==='jour'?'nuit':'jour';""" \
        """btn.textContent=mode==='jour'?'Passer en nuit':'Passer en jour';draw()};""" \
        """s.layers.forEach((l,i)=>{const label=document.createElement('label'),""" \
        """ch=document.createElement('input');ch.type='checkbox';ch.checked=true;""" \
        """ch.onchange=draw;checks.push(ch);label.append(ch,document.createTextNode(l.id));""" \
        """controls.append(label);for(const m of['jour','nuit']){const im=new Image();""" \
        """imgs[m+i]=im;im.onload=draw;im.src=l[m]}});""" \
        """const d=document.createElement('details');""" \
        """d.innerHTML='<summary>Vérifier le trajet — pas une collision moteur</summary>"""+\
        """<img src="'+s.route+'">';a.append(d);const p=document.createElement('p');""" \
        """p.textContent=s.notes;a.append(p);document.getElementById('maps').append(a)}""" \
        """</script></html>"""
    (R / 'apercu_entrees_sud_nord_v4.html').write_text(html)
    print('galerie écrite', len(html) // 1024, 'Ko')


if __name__ == '__main__':
    main()
