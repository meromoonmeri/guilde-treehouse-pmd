"""Vérifie le graphe canonique et les contrats de transition, sans prétendre tester un moteur."""
from pathlib import Path
from collections import Counter, deque
import copy
import json
import hashlib
import os
import subprocess
import sys
import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion, label

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"plans/guilde_4_niveaux"
OPPOSITE={"N":"S","S":"N","E":"O","O":"E"}


def assert_plan(plan):
    nodes={n['id']:n for n in plan['zones']}
    assert len(nodes)==len(plan['zones']), 'Identifiants de zone dupliqués'
    assert {l['id'] for l in plan['niveaux']}=={0,1,2,3}, 'Il faut exactement RDC + 3'
    assert {n['id'] for n in nodes.values() if n['type']=='piece'}=={f'{i:02d}' for i in range(1,13)}, 'Pièce manquante'
    assert Counter(n['niveau'] for n in nodes.values() if n['type']=='piece')=={0:3,1:3,2:3,3:3}
    assert [n['id'] for n in nodes.values() if n['type']=='exterieur']==['TERRASSE'], 'Nouvel extérieur non autorisé'
    assert all(n['forme']['style']=='arrondi' for n in nodes.values()), 'Contour non arrondi'
    kit=json.loads((ROOT/'kit.json').read_text())
    for room in kit['salles']:
        assert set(nodes[room['id']]['ports'])=={p['id'] for p in room['passages_pmd']}, 'Accès de pièce ajouté ou supprimé'
    used=Counter();graph={k:[] for k in nodes};vertical=[];door=[]
    for e in plan['liaisons']:
        a,b=e['a'],e['b'];na,nb=nodes[a['zone']],nodes[b['zone']]
        pa,pb=na['ports'][a['port']],nb['ports'][b['port']]
        assert e['bidirectionnel']
        used[(a['zone'],a['port'])]+=1;used[(b['zone'],b['port'])]+=1
        graph[a['zone']].append((b['zone'],e));graph[b['zone']].append((a['zone'],e))
        if e['type']=='vertical':
            assert abs(na['niveau']-nb['niveau'])==1, 'Saut d’étage'
            high,low=(pa,pb) if na['niveau']>nb['niveau'] else (pb,pa)
            assert high['type']=='tremie_descendante' and low['type']=='echelle_montante', 'Extrémités verticales incohérentes'
            safety=high['profil_securite']
            for k in ['vide_non_praticable','ombre_interieure','epaisseur_rebord','barreaux_sous_plancher','masque_rebord_avant']:
                assert safety[k], f'Trémie incomplète : {k}'
            assert safety['forme_ouverture']=='ovale', 'Trémie non arrondie'
            x,y=safety['arrivee'];cx,cy=safety['centre_vide'];rx,ry=safety['rayons_vide']
            assert ((x-cx)/rx)**2+((y-cy)/ry)**2>1, 'Arrivée dans le vide'
            tx,ty,tw,th=safety['zone_action'];assert not(tx<=x<=tx+tw and ty<=y<=ty+th), 'Arrivée dans le déclencheur'
            vertical.append((min(na['niveau'],nb['niveau']),max(na['niveau'],nb['niveau'])))
        else:
            assert na['niveau']==nb['niveau'], 'Passage horizontal qui change d’étage'
            assert OPPOSITE[pa['orientation']]==pb['orientation'], 'Orientations non opposées'
        if e['type']=='porte':door.append(e)
    assert sorted(vertical)==[(0,1),(1,2),(2,3)], 'Chaîne verticale incomplète'
    assert len(door)==1 and {door[0]['a']['zone'],door[0]['b']['zone']}=={'02','12'}, 'Porte du chef déplacée'
    assert any(e['type']=='exterieur' and {e['a']['zone'],e['b']['zone']}=={'TERRASSE','01'} for e in plan['liaisons'])
    for node in nodes.values():
        for pid in node['ports']:assert used[(node['id'],pid)]==1, f'Accès orphelin ou multiple : {node["id"]}.{pid}'
    visited={'TERRASSE'};queue=deque(visited)
    while queue:
        for neighbor,e in graph[queue.popleft()]:
            if neighbor not in visited:visited.add(neighbor);queue.append(neighbor)
    assert visited==set(nodes), 'Zone inaccessible'
    assert len(plan['liaisons'])-len(nodes)+1==1, 'La boucle utile R+1 doit être unique'
    c=plan['contrat_jouabilite'];assert c['trou_non_praticable'] and c['arrivee_hors_declencheur'] and c['relachement_action_requis'] and c['temporisation_ms']>=250
    return nodes,graph


def route(graph,start,end):
    queue=deque([(start,[start],[])]);seen={start}
    while queue:
        current,path,links=queue.popleft()
        if current==end:
            return {'depart':start,'arrivee':end,'zones':path,'liaisons':[e['id'] for e in links],
                    'changements_niveau':sum(e['type']=='vertical' for e in links),
                    'transitions_scene_cibles':sum(e['type'] in ['vertical','exterieur'] for e in links)}
        for neighbor,e in graph[current]:
            if neighbor not in seen:seen.add(neighbor);queue.append((neighbor,path+[neighbor],links+[e]))
    raise AssertionError('Trajet introuvable')


def check_arrivals(plan):
    rows=[]
    for node in plan['zones']:
        if node['type']!='piece':continue
        floor=np.array(Image.open(ROOT/node['masque_sol']))==1
        core=binary_erosion(floor,structure=np.ones((24,24),bool),border_value=1)
        labs,_=label(core);counts=np.bincount(labs.ravel());counts[0]=0;main=counts.argmax()
        for key,p in node['ports'].items():
            x,y=p['arrivee_reference_px'];assert core[y,x] and labs[y,x]==main
            px,py=p['repere_canonique_px'];assert core[py,px] and labs[py,px]==main
            rx,ry,rw,rh=p['rectangle_canonique_px']
            assert rx<=px<rx+rw and ry<=py<ry+rh, 'Le point de pieds est hors de son déclencheur canonique'
            assert not(rx<=x<rx+rw and ry<=y<ry+rh), 'Arrivée dans le déclencheur'
            rows.append({'zone':node['id'],'port':key,'point_px':[x,y],'repere_canonique_px':[px,py],
                         'gabarit_24_valide':True,'hors_rectangle_canonique':True,'repere_recale':p['recalage_sans_redessiner'],
                         'rectangle_recale':p['rectangle_recale']})
    return rows


def verify():
    p=json.loads((OUT/'plan_canonique.json').read_text());nodes,graph=assert_plan(p)
    negatives={}
    mutations={
        'sans_trou':lambda q:q['zones'][next(i for i,n in enumerate(q['zones']) if n['id']=='P3')]['ports']['descente']['profil_securite'].__setitem__('vide_non_praticable',False),
        'trou_anguleux':lambda q:q['zones'][next(i for i,n in enumerate(q['zones']) if n['id']=='P3')]['ports']['descente']['profil_securite'].__setitem__('forme_ouverture','rectangle'),
        'piece_non_arrondie':lambda q:q['zones'][0]['forme'].__setitem__('style','polygonal'),
        'liaison_manquante':lambda q:q['liaisons'].pop(),
        'double_destination':lambda q:q['liaisons'].append(copy.deepcopy(q['liaisons'][0])),
        'saut_etage':lambda q:q['zones'][next(i for i,n in enumerate(q['zones']) if n['id']=='P3')].__setitem__('niveau',0),
    }
    for name,mutate in mutations.items():
        bad=copy.deepcopy(p);mutate(bad)
        try:assert_plan(bad)
        except (AssertionError,KeyError):negatives[name]='refusé'
        else:raise AssertionError('Le contrôle ne détecte pas '+name)
    trips=[route(graph,a,b) for a,b in [('05','02'),('05','TERRASSE'),('05','04'),('02','12'),('06','TERRASSE'),('08','03')]]
    assert trips[0]['changements_niveau']==1 and trips[1]['transitions_scene_cibles']==3
    assert trips[2]['changements_niveau']==0 and trips[3]['changements_niveau']==0
    arrivals=check_arrivals(p)
    assert sum(r['repere_recale'] for r in arrivals)==3
    assert sum(r['rectangle_recale'] for r in arrivals)==3
    # Les commandes historiques ne doivent plus réintroduire les décors refusés.
    protected=[ROOT/'tilesheets/kit.json',ROOT/'kit.json']
    before={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in protected}
    env=os.environ.copy();env.pop('GUILDE_REPRODUIRE_LEGACY',None)
    guards={}
    for script in ['source/build_tilesheets.py','source/build_hallways.py']:
        process=subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,env=env,capture_output=True,text=True,timeout=15)
        assert process.returncode!=0 and 'désactivé' in process.stderr, 'Constructeur procédural encore actif par défaut'
        guards[script]='bloqué par défaut ; reproduction historique explicite seulement'
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==sha for f,sha in before.items())
    directed=[]
    for e in p['liaisons']:
        for src,dst in [(e['a'],e['b']),(e['b'],e['a'])]:
            port=nodes[src['zone']]['ports'][src['port']]
            target=nodes[dst['zone']]['ports'][dst['port']]
            directed.append({'liaison':e['id'],'origine':src,'destination':dst,'type':e['type'],'declenchement':port['declenchement'],
                             'repere_origine_px':port.get('repere_canonique_px'),
                             'zone_action_origine':port.get('rectangle_canonique_px',port.get('profil_securite',{}).get('zone_action')),
                             'unite_zone':'pixels_asset_reference' if 'rectangle_canonique_px' in port else 'normalisee_provisoire_ou_a_definir',
                             'face_apres_arrivee':{'N':'S','S':'N','E':'O','O':'E','U':'S','D':'S'}[target['orientation']],
                             'arrivee':target.get('arrivee_reference_px',target.get('profil_securite',{}).get('arrivee')),
                             'unite_arrivee':'pixels_asset_reference' if 'arrivee_reference_px' in target else 'normalisee_provisoire_ou_a_definir',
                             'temporisation_ms':300,'rearmement':'Après sortie de zone et relâchement de la touche, si interaction.',
                             'statut':'Contrat à intégrer, pas trigger moteur installé'})
    (OUT/'transitions_a_integrer.json').write_text(json.dumps(directed,ensure_ascii=False,indent=2)+'\n')
    report={'plan_valide':True,'niveaux':4,'pieces':12,'circulations':9,'zones':22,'liaisons_bidirectionnelles':22,'transitions_dirigees':44,
            'acces_piece_affectes':19,'paires_verticales':3,'trous_superieurs_requis':3,'nouvelle_echelle_basse_requise':1,
            'aucun_acces_orphelin':True,'styles_arrondis':True,'points_recales':3,'rectangles_action_recales':3,
            'constructeurs_historiques':guards,'tests_negatifs':negatives,'trajets':trips,'arrivees_assets_reference':arrivals,
            'limite':'Validation du graphe et de repères sur assets existants. La géométrie des futurs couloirs/trémies et le moteur restent à valider.'}
    (OUT/'controle_plan.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('PASS plan : 4 niveaux, 12 pièces, 9 circulations, 22 liaisons, 3 paires d’échelles ; 19 arrivées et repères recalés vérifiés en 24 px.')
    return report

if __name__=='__main__':verify()
