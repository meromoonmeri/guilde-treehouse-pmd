"""Post-traitement d'une trémie réellement générée : aucun décor peint par code."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'source'))
from rebuild_kit import ase,night,png
RAW=Path(__file__).parent/'tremie_descente_arrondie_brute.png'
OUT=ROOT/'plans/guilde_4_niveaux/prototype_tremie'


def ellipse(box,size=(256,112)):
    im=Image.new('L',size);ImageDraw.Draw(im).ellipse(box,fill=255);return np.array(im)>0


def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    raw=Image.open(RAW).convert('RGB').resize((256,112),Image.Resampling.NEAREST)
    a=np.array(raw);r,g,b=[a[:,:,i].astype(int) for i in range(3)]
    key=(r>g+45)&(b>g+35)&(b>75)
    # Palette de travail, comme les natifs du kit. Réserver le magenta.
    work=a.copy();work[key]=(151,87,36)
    q=Image.fromarray(work).quantize(colors=255,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
    ids=np.array(q);ids[key]=255
    nat=Image.fromarray(ids).convert('P');nat.putpalette(q.getpalette()[:765]+[255,0,255]);nat.save(OUT/'natif_magenta.png',optimize=True)
    a=np.array(nat.convert('RGBA'));a[key]=0;base=Image.fromarray(a)
    outer=ellipse((79,16,177,82));yy,xx=np.indices(key.shape)
    handholds=(xx>=111)&(xx<=144)&(yy>=8)&(yy<32)
    feature=(outer|handholds)&~key
    fore=feature&(yy>=68)
    inside=ellipse((87,26,170,76))
    masks=[(~feature)&(~key),feature&~fore,fore]
    names=['00_parquet_evide','01_puits_et_echelle','02_rebord_avant']
    for mode in ['jour','nuit']:
        source=base if mode=='jour' else night(base)
        data=np.array(source);layers=[]
        folder=OUT/'calques'/mode;folder.mkdir(parents=True,exist_ok=True)
        comp=Image.new('RGBA',base.size)
        for name,mask in zip(names,masks):
            cut=data.copy();cut[~mask]=0;im=Image.fromarray(cut)
            png(im,folder/(name+'.png'));comp.alpha_composite(im);layers.append((name,im))
        assert np.array_equal(np.array(comp),data)
        png(comp,OUT/(mode+'.png'));ase(OUT/(mode+'.aseprite'),layers,base.size)
    Image.fromarray(feature.astype('uint8')*255).save(OUT/'zone_non_praticable.png')
    Image.fromarray(inside.astype('uint8')*255).save(OUT/'ouverture_interieure.png')
    collision=feature|key
    def valid_point(p,half=8):
        x,y=p;return not collision[y-half:y+half,x-half:x+half].any()
    # Exemples locaux sur ce prototype ; à repositionner dans les vrais paliers.
    action=[128,92];arrival=[96,96]
    assert valid_point(action) and valid_point(arrival), 'Aire de pieds insuffisante sur le prototype'
    trigger=[112,88,32,8]
    assert not(trigger[0]<=arrival[0]<trigger[0]+trigger[2] and trigger[1]<=arrival[1]<trigger[1]+trigger[3])
    lum=.2126*a[:,:,0]+.7152*a[:,:,1]+.0722*a[:,:,2]
    ring=(~feature)&(~key)&(yy>30)&(yy<90)
    assert lum[inside].mean()<lum[ring].mean()
    report={'statut':'Prototype généré arrondi, non posé dans les trois paliers', 'source_generee':str(RAW.relative_to(ROOT)),
            'sha256_source':hashlib.sha256(RAW.read_bytes()).hexdigest(),'dimensions':[256,112],'grille_px':8,
            'traitements':['Voisin le plus proche','Palette native','Détourage','Sélections de pixels pour les trois plans'],
            'decor_dessine_par_code':False,'calques':names,'recomposition_exacte':True,'vide_non_praticable':True,
            'luminance_puits':float(lum[inside].mean()),'luminance_plancher':float(lum[ring].mean()),
            'gabarit_pieds_px':16,'point_action_px':action,'zone_action_centre_pieds_px':trigger,'arrivee_px':arrival,
            'rearmement':'Relâchement de la touche + sortie de la zone + temporisation 300 ms',
            'limite':'Les coordonnées sont locales au prototype, pas les coordonnées des futurs paliers. Le masque doit être adapté à chaque intégration.'}
    (OUT/'controle.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    bg=Image.new('RGBA',base.size,(23,16,29,255));bg.alpha_composite(base)
    bg.resize((1024,448),Image.Resampling.NEAREST).convert('RGB').save(OUT/'apercu_4x.png',optimize=True)
    print('Prototype : trémie ovale générée, 3 plans, recomposition exacte, zone de vide et deux points de pieds contrôlés.')

if __name__=='__main__':prepare()
