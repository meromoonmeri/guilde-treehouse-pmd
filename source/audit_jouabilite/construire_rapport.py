"""Rapport illustré et schéma interactif. Les dessins sont des schémas, pas des décors."""
from pathlib import Path
from html import escape
import base64
import io
import json
import math
import textwrap
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
import markdown

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'plans/guilde_4_niveaux'
PLAN=json.loads((OUT/'plan_canonique.json').read_text())
METRICS=json.loads((OUT/'mesures_assets.json').read_text())
CHECK=json.loads((OUT/'controle_plan.json').read_text())
NODES={n['id']:n for n in PLAN['zones']}


def port_xy(node,pid):
    x,y,w,h=node['schema'];p=node['ports'][pid];u,v=p['position_schema'];d=p['orientation']
    if d in ['N','S']:
        xx=x+u*w;yy=y+h/2+(-1 if d=='N' else 1)*(h/2)*math.sqrt(max(0,1-(2*u-1)**2))
    elif d in ['E','O']:
        yy=y+v*h;xx=x+w/2+(-1 if d=='O' else 1)*(w/2)*math.sqrt(max(0,1-(2*v-1)**2))
    else:xx=x+u*w;yy=y+v*h
    return xx,yy


def floor_svg(level,standalone=True):
    ns=[n for n in PLAN['zones'] if n['niveau']==level]
    svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 640" role="img" aria-label="Plan schématique '+('RDC' if level==0 else 'R+'+str(level))+'">']
    svg.append('''<style>.edge{fill:none;stroke:#7c967e;stroke-width:3}.edge.door{stroke:#aa7a35;stroke-width:4}.edge.route{stroke:#d3942e;stroke-width:6}.node ellipse.body{fill:#eff2e3;stroke:#6e896e;stroke-width:2}.node.circulation ellipse.body{fill:#fcf0d8;stroke:#b28a49;stroke-dasharray:7 5}.node.prototype ellipse.body{fill:#eeebf4;stroke:#8b7e9b;stroke-dasharray:5 4}.node.exterior ellipse.body{fill:#e4eeea;stroke:#4e786e}.node.route ellipse.body{stroke:#c38729;stroke-width:4;fill:#fff1c9}.node.selected ellipse.body{stroke:#244e38;stroke-width:5}.node{cursor:pointer}.nt{font:600 15px system-ui,sans-serif;fill:#294533;text-anchor:middle;pointer-events:none}.ni{font:11px system-ui,sans-serif;fill:#76836a;text-anchor:middle;pointer-events:none}.port{fill:#456e54;stroke:#f7f6ed;stroke-width:2}.vertical{fill:#e6dcec;stroke:#8b729c;stroke-width:1.5}.vtext{font:600 10px system-ui,sans-serif;fill:#67477d;text-anchor:middle;pointer-events:none}.edge-label{font:10px system-ui,sans-serif;fill:#936721}</style>''')
    if standalone:svg.append('<rect width="1200" height="640" fill="#f7f5eb"/>')
    normals={'N':(0,-1),'S':(0,1),'E':(1,0),'O':(-1,0)}
    for e in PLAN['liaisons']:
        a,b=NODES[e['a']['zone']],NODES[e['b']['zone']]
        if e['type']=='vertical' or a['niveau']!=level:continue
        ax,ay=port_xy(a,e['a']['port']);bx,by=port_xy(b,e['b']['port'])
        nx,ny=normals[a['ports'][e['a']['port']]['orientation']];mx,my=normals[b['ports'][e['b']['port']]['orientation']]
        distance=math.hypot(bx-ax,by-ay)
        length=min(75,max(8,distance*.35),distance*.48)
        cls='edge door' if e['type']=='porte' else 'edge'
        title=f"{e['id']} : {a['nom']} ↔ {b['nom']}"
        svg.append(f'<path class="{cls}" data-link="{e["id"]}" d="M{ax:.1f},{ay:.1f} C{ax+nx*length:.1f},{ay+ny*length:.1f} {bx+mx*length:.1f},{by+my*length:.1f} {bx:.1f},{by:.1f}"><title>{escape(title)}</title></path>')
        if e['type']=='porte':svg.append(f'<text class="edge-label" x="{(ax+bx)/2+9:.1f}" y="{(ay+by)/2:.1f}">porte du chef</text>')
    for node in ns:
        x,y,w,h=node['schema'];cx,cy=x+w/2,y+h/2
        cls='node'
        if node['type'] in ['couloir','palier']:cls+=' prototype' if node['statut_asset']=='prototype_a_adapter' else ' circulation'
        if node['type']=='exterieur':cls+=' exterior'
        svg.append(f'<g class="{cls}" data-zone="{node["id"]}" tabindex="0" role="button" aria-label="{escape(node["nom"])}"><title>{escape(node["nom"]+" — "+node["forme"].get("description",node["forme"]["famille"]))}</title>')
        svg.append(f'<ellipse class="body" cx="{cx}" cy="{cy}" rx="{w/2}" ry="{h/2}"/>')
        lines=textwrap.wrap(node['nom'],width=23 if w>200 else 15)
        start=cy-(len(lines)-1)*9
        svg.append(f'<text class="ni" x="{cx}" y="{start-23}">{node["id"]}</text>')
        for i,line in enumerate(lines):svg.append(f'<text class="nt" x="{cx}" y="{start+i*18}">{escape(line)}</text>')
        suffix='pièce existante' if node['type']=='piece' else ('prototype à adapter' if node['statut_asset']=='prototype_a_adapter' else ('carte à intégrer' if node['type']=='exterieur' else 'à générer'))
        svg.append(f'<text class="ni" x="{cx}" y="{start+len(lines)*18+4}">{suffix}</text>')
        for pid,p in node['ports'].items():
            px,py=port_xy(node,pid)
            if p['type'] in ['tremie_descendante','echelle_montante']:
                for e in PLAN['liaisons']:
                    if e['type']!='vertical':continue
                    if e['a']=={'zone':node['id'],'port':pid}:other=NODES[e['b']['zone']];break
                    if e['b']=={'zone':node['id'],'port':pid}:other=NODES[e['a']['zone']];break
                z='RDC' if other['niveau']==0 else 'R+'+str(other['niveau'])
                label_=('↓ ' if p['type']=='tremie_descendante' else '↑ ')+z
                # Les badges sont des symboles de schéma, pas une image de trémie.
                if p['type']=='tremie_descendante':px,py=cx,y+h-9
                else:py-=12
                svg.append(f'<g data-vertical="{e["id"]}"><rect class="vertical" x="{px-30}" y="{py-11}" width="60" height="22" rx="11"/><text class="vtext" x="{px}" y="{py+4}">{label_}</text></g>')
            else:svg.append(f'<circle class="port" cx="{px}" cy="{py}" r="4.5"/>')
        svg.append('</g>')
    svg.append('<text x="20" y="632" style="font:11px system-ui;fill:#7a826e">Schéma de connexions : les positions ne sont pas des coordonnées moteur. Tous les contours restent arrondis.</text></svg>')
    return ''.join(svg)


def to_data(path):
    return 'data:image/png;base64,'+base64.b64encode(Path(path).read_bytes()).decode()


def binary_png(a):
    buffer=io.BytesIO();Image.fromarray(a.astype('uint8')*255).save(buffer,format='PNG',optimize=True)
    return 'data:image/png;base64,'+base64.b64encode(buffer.getvalue()).decode()


def build():
    svgs={str(z):floor_svg(z) for z in [3,2,1,0]}
    for z,svg in svgs.items():(OUT/f'plan_R{z}.svg').write_text(svg)
    # Vue d'ensemble en quatre panneaux, indépendante de l'onglet actif de l'HTML.
    allsvg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1240 2880"><rect width="1240" height="2880" fill="#f7f5eb"/>']
    for i,z in enumerate([3,2,1,0]):
        title=('RDC' if z==0 else f'R+{z}')+' / '+next(l['usage'] for l in PLAN['niveaux'] if l['id']==z)
        allsvg.append(f'<text x="35" y="{i*720+38}" style="font:600 24px system-ui;fill:#294533">{escape(title)}</text>')
        allsvg.append(f'<g transform="translate(20,{i*720+55})">'+svgs[str(z)].replace('viewBox="0 0 1200 640"','viewBox="0 0 1200 640" width="1200" height="640"')+'</g>')
    allsvg.append('</svg>');(OUT/'plan_canonique.svg').write_text(''.join(allsvg))
    rooms={}
    for r in METRICS['salles']:
        n=NODES[r['id']];s=np.array(Image.open(ROOT/n['masque_sol']))==1;yy,xx=np.unravel_index(np.argmax(distance_transform_edt(s)),s.shape)
        rooms[r['id']]={'id':r['id'],'nom':r['nom'],'dimensions':r['dimensions'],'image':to_data(ROOT/n['image']),
                         'mask':binary_png(s),'center':[int(xx),int(yy)],'metrics':r,
                         'ports':[{'id':pid,**p} for pid,p in n['ports'].items()], 'forme':n['forme']}
    payload={'plan':PLAN,'checks':CHECK,'metrics':METRICS,'svgs':svgs,'rooms':rooms,
             'prototype':to_data(OUT/'prototype_tremie/jour.png'),
             'gallery':to_data(ROOT/'tilesheets/generes/galerie_est_ouest/apercu_jour.png')}
    article=markdown.markdown((OUT/'rapport.md').read_text(),extensions=['tables','fenced_code'])
    # Le titre de page est déjà donné par le bandeau de l'atelier.
    article=article[article.index('</h1>')+5:]
    html=r'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Guilde Treehouse — plan arrondi et audit de jouabilité</title><style>
:root{--ink:#2d4937;--muted:#6a7b67;--paper:#f7f5eb;--line:#d9dfce;--gold:#ae7b31;--alert:#8e4333;--soft:#edf0e1}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:14px/1.65 system-ui,sans-serif}a{color:#466d4d;text-underline-offset:3px}main{max-width:1400px;margin:auto;padding:30px 26px 50px}header{display:flex;gap:30px;justify-content:space-between;align-items:center}.eyebrow{color:var(--gold);letter-spacing:.16em;text-transform:uppercase;font-size:10px;font-weight:700}h1{font:500 clamp(31px,3.7vw,48px)/1.13 Georgia,serif;letter-spacing:-.025em;margin:10px 0 15px}header p{max-width:810px;color:var(--muted);margin:0}.stamp{padding:14px 20px;border:1px solid #b9c8ac;border-radius:8px;min-width:205px;font-size:12px}.stamp strong{display:block;color:#365b3c}.stamp span{color:var(--alert)}nav{display:flex;gap:20px;flex-wrap:wrap;margin:26px 0;font-size:12px}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line);border-radius:9px;overflow:hidden;margin:24px 0}.stats div{background:#fffef7;padding:16px 19px}.stats b{display:block;font-size:27px;font-weight:600}.stats span{font-size:11px;color:var(--muted)}h2{font:500 28px Georgia,serif;margin:0 0 14px}h3{font-size:15px;margin:25px 0 12px}.lead{color:var(--muted);max-width:980px;font-size:13px}.section{margin-top:38px;scroll-margin-top:20px}button,select,input{font:inherit}button,select{background:#fffef7;color:var(--ink);border:1px solid #cbd4bf;border-radius:6px;padding:8px 11px;max-width:100%;cursor:pointer}button:hover{border-color:#7e956d}button.active{background:#2d4937;color:#fbf8e9;border-color:#2d4937}button:focus-visible,select:focus-visible,a:focus-visible,canvas:focus-visible{outline:3px solid #b9944e;outline-offset:3px}.levels{display:flex;gap:7px;flex-wrap:wrap;margin:18px 0}.levels button{min-width:135px;font-size:12px}.plan-work{display:grid;grid-template-columns:minmax(0,1fr) 275px;gap:16px}.panel{background:#fffef8;border:1px solid var(--line);border-radius:9px;overflow:hidden;min-width:0}.panel-head{padding:13px 18px;border-bottom:1px solid var(--line);font-size:12px;display:flex;justify-content:space-between;gap:12px}.map svg{display:block;width:100%;height:auto}.map{background:#f7f5eb;min-height:330px}.legend{display:flex;gap:16px;flex-wrap:wrap;padding:12px 16px;border-top:1px solid var(--line);font-size:10px;color:var(--muted)}.legend i{display:inline-block;width:10px;height:10px;border:1px solid #718e6c;border-radius:50%;margin-right:5px;background:#eff2e3}.legend .missing{background:#fcf0d8;border-color:#b28a49}.legend .proto{background:#eeebf4;border-color:#8b7e9b}aside{padding:18px}aside h3{font-size:14px;margin:0 0 13px}aside p{font-size:12px;color:var(--muted);margin:10px 0}aside img{max-width:100%;height:auto;background:#17101d;border-radius:5px;image-rendering:pixelated}.tag{font-size:10px;display:inline-block;padding:3px 7px;border:1px solid #d7ddca;border-radius:4px;margin:4px 3px 4px 0;background:#eff3e5}.route-controls{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:16px 0}.route-controls label{font-size:11px;color:var(--muted)}.route-controls select{font-size:12px;min-width:160px}.itinerary{padding:13px 16px;border:1px solid #e1d3ae;border-radius:7px;background:#fff5db;font-size:12px}.itinerary b{color:#805c23}.route-line{display:flex;gap:7px;align-items:center;flex-wrap:wrap}.route-line button{padding:3px 7px;border-radius:12px;font-size:11px}.downloads{display:flex;gap:16px;flex-wrap:wrap;margin:15px 0;font-size:12px}.checks{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:18px 0}.check{background:#fffef7;border:1px solid var(--line);padding:17px;border-radius:8px}.check strong{display:block;font-size:14px;margin-bottom:7px}.check p{font-size:12px;color:var(--muted);margin:0}.check.bad{border-top:3px solid #b15f41}.check.ok{border-top:3px solid #6b9465}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:18px 0}.card{background:#fffef8;border:1px solid var(--line);border-radius:8px;padding:12px;min-width:0}.card img{width:100%;height:122px;object-fit:contain;background:#17101d;border-radius:4px;image-rendering:pixelated}.card h3{font-size:12px;margin:10px 0 4px}.card p{font-size:11px;color:var(--muted);margin:5px 0}.card span{font-size:10px;color:var(--gold)}.lab-toolbar{display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin:15px 0}.lab-toolbar label{font-size:11px}.lab-grid{display:grid;grid-template-columns:minmax(0,1fr) 275px;gap:16px}.lab-stage{padding:18px;background:#17101d;display:flex;align-items:center;min-height:380px;overflow:auto}canvas{display:block;margin:auto;image-rendering:pixelated;outline:none;flex:none}.lab-info{padding:18px}.lab-info .result{font-size:18px;font-weight:650;margin-bottom:10px}.good{color:#567a44}.bad-text{color:#a04731}.note{padding:13px 16px;background:#e9eddc;border-radius:6px;font-size:12px;margin:16px 0;color:#55694e}.tremie-grid{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr);gap:20px;align-items:center}.tremie-grid img{width:100%;background:#17101d;image-rendering:pixelated;border-radius:7px}.tremie-grid ul{font-size:13px;padding-left:19px}.report{padding:24px;background:#fffef8;border:1px solid var(--line);border-radius:8px}.report h2{font:600 21px system-ui;margin:35px 0 15px}.report h2:first-of-type{margin-top:5px}.report h3{font-size:15px}.report p,.report li{font-size:13px;max-width:1120px}.report table{border-collapse:collapse;width:100%;margin:15px 0;font-size:12px}.report td,.report th{border-bottom:1px solid var(--line);text-align:left;padding:9px 10px;vertical-align:top}.report th{background:#edf1e3}.report pre{background:#eff1e6;padding:14px;overflow:auto}.report code{font-size:11px;overflow-wrap:anywhere}footer{font-size:11px;color:var(--muted);margin-top:30px;border-top:1px solid var(--line);padding-top:16px}.print-plans{display:none}.subtle{font-size:11px;color:var(--muted)}
@media(max-width:980px){.plan-work,.lab-grid{grid-template-columns:minmax(0,1fr) 235px}.cards{grid-template-columns:repeat(3,1fr)}.stamp{display:none}}
@media(max-width:720px){main{padding:22px 12px}.plan-work,.lab-grid,.tremie-grid{grid-template-columns:minmax(0,1fr)}h1{font-size:32px}.stats{grid-template-columns:repeat(2,1fr)}.stats b{font-size:23px}.levels button{min-width:0;flex:1;padding:8px 5px}.cards{grid-template-columns:repeat(2,1fr)}.checks{grid-template-columns:1fr}.map{min-height:0;overflow:auto}.map svg{min-width:680px}.panel-head{padding:10px}.report{padding:15px}.report table{display:block;overflow-x:auto;font-size:11px}.route-controls select{min-width:0;flex:1}.lab-stage{min-height:250px;padding:10px}.card img{height:100px}nav{gap:12px}}
@media print{@page{size:A4;margin:13mm}body{background:white;font-size:11px}main{padding:0;max-width:none}header{display:block}h1{font-size:30px}.stamp,nav,.interactive,.cards,.lab-section,.downloads,.stats,.checks{display:none!important}.section{margin-top:18px}.report{border:0;padding:0}.report p,.report li{font-size:10px}.report h2{font-size:17px;break-after:avoid}.report table{font-size:9px;display:table}.report tr{break-inside:avoid}.report th,.report td{padding:6px}.tremie-grid{grid-template-columns:1fr 1fr}.tremie-grid ul{font-size:10px}.print-plans{display:block}.print-plans section{break-before:page;break-inside:avoid}.print-plans svg{width:100%;height:auto}.note{font-size:10px}.section h2{font-size:22px}a{color:inherit;text-decoration:none}footer{font-size:9px}.paper-hide{display:none}}
</style></head><body><main>
<header><div><div class="eyebrow">Guilde Treehouse / audit d’intégration · 06.09.2026</div><h1>Arrondis, mais pas identiques.</h1><p>Une guilde sur quatre niveaux, des connexions sans ambiguïté et de vraies descentes dans le plancher. On garde le bois, les courbes et la DA — on ne transforme pas les pièces en polygones.</p></div><div class="stamp"><strong>Plan vérifié</strong><span>Assets et intégration à compléter</span><br>Pas une certification moteur</div></header>
<nav><a href="#plan">Plan des étages</a><a href="#constats">Points bloquants</a><a href="#formes">Formes arrondies</a><a href="#collision">Essai de gabarit</a><a href="#tremie">Descendre par le trou</a><a href="#rapport">Audit complet</a></nav>
<div class="stats"><div><b>4</b><span>niveaux · RDC + 3</span></div><div><b>12</b><span>pièces conservées et affectées</span></div><div><b>22</b><span>liaisons réciproques vérifiées</span></div><div><b>3</b><span>trémies hautes à intégrer</span></div></div>
<section id="plan" class="section"><h2>Le plan de référence</h2><p class="lead">L’entrée historique reste au nord de l’accueil, côté terrasse. On descend ensuite vers les missions puis la vie commune. Les paliers rendent chaque changement d’étage explicite ; aucune nouvelle entrée au RDC n’est inventée.</p>
<div class="interactive"><div class="levels" aria-label="Étages"><button data-level="3">R+3 · Accueil</button><button data-level="2">R+2 · Missions</button><button data-level="1">R+1 · Vie commune</button><button data-level="0">RDC · Dortoirs</button></div>
<div class="plan-work"><div class="panel"><div class="panel-head"><strong id="level-title"></strong><span>Schéma, pas coordonnées moteur</span></div><div id="map" class="map"></div><div class="legend"><span><i></i>Pièce existante</span><span><i class="missing"></i>Circulation à générer</span><span><i class="proto"></i>Prototype à adapter</span><span>↑ ↓ Échelle / trémie jumelées</span></div></div><aside id="details" class="panel"></aside></div>
<div class="route-controls"><label for="start">Départ</label><select id="start"></select><label for="end">Arrivée</label><select id="end"></select><button id="calc">Voir le trajet</button></div><div id="route" class="itinerary"></div></div>
<div class="downloads"><a href="plan_canonique.svg">Plan complet SVG</a><a href="plan_canonique.png">Plan complet PNG</a><a href="plan_canonique.json">Référence JSON</a><a href="transitions_a_integrer.json">44 transitions à intégrer</a><a href="rapport.pdf">Audit PDF</a></div>
<div class="note">Une scène par étage est recommandée. « Trois changements de scène » ne signifie pas trois portes : les pièces et les petits couloirs d’un même étage devraient se parcourir sans chargement intermédiaire.</div></section>
<section id="constats" class="section"><h2>Ce qui manque vraiment</h2><div class="checks"><div class="check ok"><strong>Connexions : complètes dans le plan</strong><p>12 pièces, 19 accès affectés une seule fois, aucune branche orpheline, une seule porte vers le chef et trois paires verticales.</p></div><div class="check bad"><strong>Circulation : décors incomplets</strong><p>Sept zones attendent un master conforme. Deux galeries peuvent partir de la génération existante, mais leurs raccords restent à adapter.</p></div><div class="check bad"><strong>Descente et moteur : pas encore branchés</strong><p>Les trois paliers hauts et l’échelle basse P0 restent à produire/intégrer. Le prototype de trémie n’est pas une intégration au moteur.</p></div></div></section>
<section id="formes" class="section"><h2>Conserver les courbes, varier les proportions</h2><p class="lead">05/07/11 et 08/10 ont des silhouettes identiques à miroir près. Les images ci-dessous restent les assets actuels ; les descriptions donnent les directions de génération, toutes arrondies. Aucun décor en L n’a été installé.</p><div id="cards" class="cards"></div></section>
<section id="collision" class="section lab-section"><h2>Essayer un gabarit, sans prétendre avoir le jeu</h2><p class="lead">Ce carré représente uniquement les pieds du personnage sur les masques existants. Il ne simule ni les PNJ ni le mobilier. Aux sorties, les pieds peuvent dépasser le cadre, comme dans la mesure. Cliquer le décor puis utiliser les flèches ; les passages ne changent pas de scène dans ce laboratoire.</p><div class="lab-toolbar"><select id="lab-room" aria-label="Pièce à tester"></select><select id="lab-port" aria-label="Repère"></select><select id="lab-size" aria-label="Taille des pieds"><option value="16">Pieds 16 px</option><option value="24" selected>Pieds 24 px</option><option value="32">Pieds 32 px</option></select><label><input id="canonical" type="checkbox" checked>Repère recalé du plan</label><label><input id="show-mask" type="checkbox">Afficher le sol</label><button id="recenter">Recentrer</button></div><div class="lab-grid"><div class="panel lab-stage" id="lab-stage"><canvas id="lab" tabindex="0" aria-label="Gabarit de pieds sur le sol actuel"></canvas></div><div class="panel lab-info"><div id="lab-result" class="result"></div><p id="lab-caption"></p><p class="subtle">19/19 repères actuels passent en 16 px. En 24 px, trois recalages de 1 à 3 px suffisent dans leurs rectangles existants. Les 32 px révèlent de vrais cols plus étroits en 03/04.</p><p class="subtle">Le gabarit réel du personnage reste à fixer. La géométrie des futurs paliers n’est pas testée par cet outil.</p></div></div></section>
<section id="tremie" class="section"><h2>Une descente doit montrer le vide.</h2><div class="tremie-grid"><img id="tremie-image" alt="Prototype généré de trémie ovale, avec échelle descendante et intérieur sombre"><div><p class="lead">Prototype réellement généré, corrigé pour conserver une ouverture arrondie. L’intérieur n’est pas du magenta : c’est la profondeur du puits.</p><ul><li>Plancher évidé, épaisseur et parois intérieures visibles.</li><li>Barreaux sous le plancher qui disparaissent dans l’ombre.</li><li>Vide non praticable et rebord avant sur un plan séparé.</li><li>Arrivée sûre, hors déclencheur, puis réarmement après relâchement.</li></ul><p class="subtle">Trois calques, jour/nuit, grille 8 px. Prototype local contrôlé avec pieds de 16 px ; à adapter dans P3, P2 et P1.</p><div class="downloads"><a href="prototype_tremie/jour.png">PNG transparent</a><a href="prototype_tremie/jour.aseprite">Aseprite</a><a href="prototype_tremie/controle.json">Contrôle du prototype</a></div></div></div></section>
<section id="rapport" class="section"><h2>Audit complet et ordre de production</h2><div class="report">__ARTICLE__</div></section>
<div class="print-plans">__PRINT_PLANS__</div>
<footer>Plan canonique interne de notre guilde, inspiré de la lecture PMD. Les douze images de pièces et leurs sources ne sont pas repeintes par cet audit. Les ellipses, tracés et gabarits de cette page sont des schémas techniques ; les décors futurs passent par le générateur d’images.</footer>
</main><script>
const D=__DATA__,$=s=>document.querySelector(s),nodes=Object.fromEntries(D.plan.zones.map(n=>[n.id,n])),neighbors={};let level=3,selected='01',currentRoute=null;for(const n of D.plan.zones)neighbors[n.id]=[];for(const e of D.plan.liaisons){neighbors[e.a.zone].push([e.b.zone,e]);neighbors[e.b.zone].push([e.a.zone,e])}
function floorName(z){return z===0?'RDC':'R+'+z}
function setFloor(z){level=+z;$('#map').innerHTML=D.svgs[level];$('#level-title').textContent=floorName(level)+' — '+D.plan.niveaux.find(l=>l.id===level).usage;document.querySelectorAll('[data-level]').forEach(b=>b.classList.toggle('active',+b.dataset.level===level));$('#map').querySelectorAll('[data-zone]').forEach(g=>{g.onclick=()=>details(g.dataset.zone);g.onkeydown=e=>{if(e.key==='Enter')details(g.dataset.zone)}});if(nodes[selected].niveau!==level)selected=D.plan.niveaux.find(l=>l.id===level).pieces[0];details(selected)}
function details(id){selected=id;const n=nodes[id],r=D.rooms[id];let html='<h3>'+n.id+' · '+n.nom+'</h3>';if(r)html+='<img src="'+r.image+'" alt="Pièce actuelle"><p><b>Forme conservée : arrondie.</b><br>'+r.forme.description+'</p><p>'+r.forme.brief+'</p>';else if(n.statut_asset==='prototype_a_adapter')html+='<img src="'+D.gallery+'" alt="Galerie générée candidate"><p>Source générée disponible. Cet aperçu ne garantit pas encore les raccords de cette instance.</p>';else if(n.type==='palier')html+='<img src="'+D.prototype+'" alt="Type de trémie générée"><p>Type d’accès illustré, <b>pas le décor du palier</b>. Le master du palier reste à générer.</p>';else html+='<p>'+ (n.type==='exterieur'?'La destination terrasse est historique. Sa carte jouable et ses collisions ne sont pas dans ce dépôt.':'Retour courbe à générer. Sa topologie n’impose ni coin droit ni chambre polygonale.')+'</p>';html+='<div>';Object.values(n.ports).forEach(p=>html+='<span class="tag">'+p.orientation+' · '+p.type.replaceAll('_',' ')+'</span>');html+='</div><p class="subtle">'+floorName(n.niveau)+' · '+n.statut_asset.replaceAll('_',' ')+'</p>';$('#details').innerHTML=html;highlight()}
function findRoute(a,b){let q=[[a,[a],[]]],seen=new Set([a]);while(q.length){const [id,path,links]=q.shift();if(id===b)return{path,links};for(const [next,e]of neighbors[id])if(!seen.has(next)){seen.add(next);q.push([next,[...path,next],[...links,e]])}}}
function route(){currentRoute=findRoute($('#start').value,$('#end').value);const changes=currentRoute.links.filter(e=>e.type==='vertical').length,scenes=currentRoute.links.filter(e=>['vertical','exterieur'].includes(e.type)).length;$('#route').innerHTML='<b>'+changes+' changement(s) d’étage · '+scenes+' changement(s) de scène cibles</b><div class="route-line">'+currentRoute.path.map(id=>'<button data-jump="'+id+'">'+id+' · '+nodes[id].nom+'</button>').join('<span>→</span>')+'</div><span class="subtle">Budget de planification avec une scène par étage, pas un chronométrage moteur.</span>';$('#route').querySelectorAll('[data-jump]').forEach(b=>b.onclick=()=>{setFloor(nodes[b.dataset.jump].niveau);details(b.dataset.jump)});highlight()}
function highlight(){const ids=new Set(currentRoute?.path||[]),es=new Set((currentRoute?.links||[]).map(e=>e.id));$('#map').querySelectorAll('[data-zone]').forEach(g=>{g.classList.toggle('route',ids.has(g.dataset.zone));g.classList.toggle('selected',g.dataset.zone===selected)});$('#map').querySelectorAll('[data-link]').forEach(g=>g.classList.toggle('route',es.has(g.dataset.link)))}
D.plan.zones.filter(n=>n.type==='piece'||n.type==='exterieur').sort((a,b)=>a.id.localeCompare(b.id)).forEach(n=>{for(const id of ['start','end'])$('#'+id).append(new Option(n.id+' · '+n.nom,n.id))});$('#start').value='05';$('#end').value='TERRASSE';$('#calc').onclick=route;document.querySelectorAll('[data-level]').forEach(b=>b.onclick=()=>setFloor(+b.dataset.level));setFloor(3);details('01');route();
$('#cards').innerHTML=Object.values(D.rooms).map(r=>'<div class="card"><img src="'+r.image+'" alt="Salle '+r.id+' actuelle"><h3>'+r.id+' · '+r.nom+'</h3><span>'+floorName(nodes[r.id].niveau)+' · image actuelle</span><p><b>Cible arrondie :</b> '+r.forme.description+'</p></div>').join('');$('#tremie-image').src=D.prototype;
const C=$('#lab'),ctx=C.getContext('2d');let labId='03',pos=[8,265],foot=24,loaded={},labReady=false;function load(url){return new Promise((ok,no)=>{const im=new Image();im.onload=()=>ok(im);im.onerror=no;im.src=url})}
Promise.all(Object.values(D.rooms).map(async r=>{const image=await load(r.image),maskImage=await load(r.mask),temp=document.createElement('canvas');temp.width=r.dimensions[0];temp.height=r.dimensions[1];const c=temp.getContext('2d');c.drawImage(maskImage,0,0);const rgba=c.getImageData(0,0,temp.width,temp.height),mask=new Uint8Array(temp.width*temp.height);for(let i=0;i<mask.length;i++){mask[i]=rgba.data[i*4]>128?1:0;rgba.data[i*4]=112;rgba.data[i*4+1]=205;rgba.data[i*4+2]=142;rgba.data[i*4+3]=mask[i]*70}c.putImageData(rgba,0,0);loaded[r.id]={image,mask,overlay:temp}})).then(()=>{labReady=true;resetRoom();document.body.dataset.ready='true'}).catch(e=>{$('#lab-result').textContent='Erreur de chargement des images';console.error(e)});
Object.values(D.rooms).forEach(r=>$('#lab-room').append(new Option(r.id+' · '+r.nom,r.id)));$('#lab-room').value='03';function resetRoom(){if(!labReady)return;labId=$('#lab-room').value;$('#lab-port').innerHTML='';D.rooms[labId].ports.forEach((p,i)=>$('#lab-port').append(new Option(p.id,i)));resetPoint()}
function resetPoint(){if(!labReady)return;const p=D.rooms[labId].ports[+$('#lab-port').value];pos=[...($('#canonical').checked?p.repere_canonique_px:p.repere_asset_px)];drawLab()}
function canStand(x,y){const r=D.rooms[labId],[w,h]=r.dimensions,m=loaded[labId].mask,half=foot/2;if(x<0||y<0||x>=w||y>=h)return false;for(let yy=Math.floor(y-half);yy<y+half;yy++)for(let xx=Math.floor(x-half);xx<x+half;xx++){const sx=Math.max(0,Math.min(w-1,xx)),sy=Math.max(0,Math.min(h-1,yy));if(!m[sy*w+sx])return false}return true}
function drawLab(){if(!labReady)return;const r=D.rooms[labId],[w,h]=r.dimensions;foot=+$('#lab-size').value;C.width=w;C.height=h;ctx.imageSmoothingEnabled=false;ctx.drawImage(loaded[labId].image,0,0);if($('#show-mask').checked)ctx.drawImage(loaded[labId].overlay,0,0);const valid=canStand(...pos);ctx.fillStyle=valid?'rgba(89,226,159,.42)':'rgba(255,86,78,.55)';ctx.strokeStyle=valid?'#65ffb0':'#ff7668';ctx.lineWidth=1;ctx.fillRect(pos[0]-foot/2,pos[1]-foot/2,foot,foot);ctx.strokeRect(pos[0]-foot/2+.5,pos[1]-foot/2+.5,foot-1,foot-1);ctx.fillStyle='#fff';ctx.fillRect(pos[0]-1,pos[1]-1,2,2);$('#lab-result').textContent=valid?'Pieds sur le sol':'Empreinte en conflit';$('#lab-result').className='result '+(valid?'good':'bad-text');const p=r.ports[+$('#lab-port').value];$('#lab-caption').textContent=foot+' × '+foot+' px · position ('+pos.join(', ')+'). Repère d’origine : '+p.repere_asset_px.join(', ')+' ; plan : '+p.repere_canonique_px.join(', ')+'.';fitLab()}
function fitLab(){if(!labReady)return;const s=Math.min(1.35,($('#lab-stage').clientWidth-36)/C.width);C.style.width=C.width*s+'px';C.style.height=C.height*s+'px'}
$('#lab-room').onchange=resetRoom;$('#lab-port').onchange=resetPoint;$('#canonical').onchange=resetPoint;$('#lab-size').onchange=drawLab;$('#show-mask').onchange=drawLab;$('#recenter').onclick=()=>{pos=[...D.rooms[labId].center];drawLab();C.focus()};C.onkeydown=e=>{const d={ArrowUp:[0,-1],ArrowDown:[0,1],ArrowLeft:[-1,0],ArrowRight:[1,0],z:[0,-1],s:[0,1],q:[-1,0],d:[1,0]}[e.key];if(!d)return;e.preventDefault();const n=[pos[0]+d[0],pos[1]+d[1]];if(canStand(...n))pos=n;drawLab()};window.addEventListener('resize',fitLab);
</script></body></html>'''
    printplans=''.join('<section><h2>'+('RDC' if z==0 else f'R+{z}')+' — '+next(l['usage'] for l in PLAN['niveaux'] if l['id']==z)+'</h2>'+svgs[str(z)]+'</section>' for z in [3,2,1,0])
    html=html.replace('__DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':'))).replace('__ARTICLE__',article).replace('__PRINT_PLANS__',printplans)
    (OUT/'index.html').write_text(html)
    print('Rapport HTML autonome et plans SVG écrits ;',len(html.encode()),'octets.')

if __name__=='__main__':build()
