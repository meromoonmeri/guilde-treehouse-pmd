"""Mesures sur les fichiers réels : silhouettes, repères et gabarits de pieds."""
from pathlib import Path
from PIL import Image
from scipy.ndimage import binary_erosion, label, binary_fill_holes
import json
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'plans/guilde_4_niveaux'


def measure():
    kit=json.loads((ROOT/'kit.json').read_text());rows=[];silhouettes={}
    for room in kit['salles']:
        s=np.array(Image.open(ROOT/room['source_masque']));floor=s==1
        a=np.array(Image.open(ROOT/room['source_base']).convert('RGBA'))
        silhouettes[room['id']]=binary_fill_holes(a[:,:,3]>0)
        row={'id':room['id'],'nom':room['nom'],'dimensions':room['dimensions'],'surface_sol_px':int(floor.sum()),'acces':[]}
        cores={}
        for size in [16,24,32]:
            er=binary_erosion(floor,structure=np.ones((size,size),bool),border_value=1)
            lab,_=label(er);counts=np.bincount(lab.ravel());counts[0]=0;main=int(counts.argmax());cores[size]=(er,lab==main)
        for p in room['passages_pmd']:
            x,y=p['point_sol'];rx,ry,rw,rh=p['zone_transition']
            q={'id':p['id'],'type':p['type'],'point_sol':p['point_sol'],'rectangle_repere':p['zone_transition'],'gabarits':{}}
            for size,(er,core) in cores.items():
                ys,xs=np.where(core[ry:ry+rh,rx:rx+rw])
                alternate=None
                if len(xs):
                    xs,ys=xs+rx,ys+ry;k=np.argmin((xs-x)**2+(ys-y)**2);alternate=[int(xs[k]),int(ys[k])]
                yy,xx=np.where(core);k=np.argmin((xx-x)**2+(yy-y)**2)
                nearest=[int(xx[k]),int(yy[k])]
                q['gabarits'][str(size)]={'pied_possible':bool(er[y,x]),'relie_au_sol_principal':bool(core[y,x]),
                                         'alternative_dans_rectangle':alternate,'point_sur_sol_principal_le_plus_proche':nearest,
                                         'distance_repositionnement_px':round(float(np.hypot(xx[k]-x,yy[k]-y)),2)}
            if 'sol_bord' in p:q['largeur_visuelle_bord_px']=p['sol_bord'][1]-p['sol_bord'][0]+1
            row['acces'].append(q)
        row['effets']={}
        for mode in ['jour','nuit']:
            row['effets'][mode]={}
            for file in ['08_ombres_acces','09_eclairage_fixe']:
                b=np.array(Image.open(ROOT/'calques'/room['dossier']/mode/(file+'.png')).convert('RGBA'));alpha=b[:,:,3]
                row['effets'][mode][file]={'pixels':int((alpha>0).sum()),'alpha_moyen_non_nul':float(alpha[alpha>0].mean())}
        rows.append(row)
    pairs=[]
    for i,a in enumerate(sorted(silhouettes)):
        for b in sorted(silhouettes)[i+1:]:
            if silhouettes[a].shape!=silhouettes[b].shape:continue
            vals=[]
            for flip in [False,True]:
                other=np.fliplr(silhouettes[b]) if flip else silhouettes[b]
                vals.append(float((silhouettes[a]&other).sum()/(silhouettes[a]|other).sum()))
            pairs.append({'a':a,'b':b,'iou':max(vals),'miroir':bool(vals[1]>vals[0])})
    pairs.sort(key=lambda p:-p['iou'])
    report={'salles':rows,'proches':pairs,'hypothese':'Empreintes carrées 16/24/32 px sur les masques de sol, sans mobilier. Erosion avec border_value=1 pour les sorties du cadre. Les résultats portent sur les repères actuels, pas sur un moteur ni sur tous les trajets possibles.',
            'silhouettes':'IoU de la silhouette extérieure à taille égale, fenêtres rebouchées pour la mesure uniquement ; meilleur score normal/miroir. Les pixels des assets ne sont pas modifiés.'}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'mesures_assets.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Mesures : 12 salles, 19 repères, 3 gabarits, comparaison des silhouettes sans modifier les images.')
    return report

if __name__=='__main__':measure()
