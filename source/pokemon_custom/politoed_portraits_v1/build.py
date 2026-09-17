"""Politoed: generated magenta studies -> keyed alpha -> anatomical cleanup -> canonical BG.
Preserves all four upstream portraits. New drafts are not upstream/user/runtime approvals.
"""
from pathlib import Path
import json, hashlib, shutil, base64, sys
import numpy as np
from scipy.ndimage import label
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[3]
SRC=Path(__file__).parent
NATIVE=ROOT/'source/guild_members_audit/references/0186/portrait'
OUT=ROOT/'exports/pokemon_custom/politoed_portraits_v1'
C=json.loads((ROOT/'source/pmd_character_pipeline/contract.json').read_text())
PRESERVE=['Normal','Inspired','Shouting','Surprised']
BG_COLORS=[(122,199,216),(155,209,196),(228,243,185)]


def native_subject(normal):
    a=np.array(normal.convert('RGBA'))
    candidate=np.zeros(a.shape[:2],bool)
    for color in BG_COLORS:candidate|=np.all(a[:,:,:3]==color,axis=2)
    labs,n=label(candidate)
    border=set(labs[0])|set(labs[-1])|set(labs[:,0])|set(labs[:,-1]);border.discard(0)
    bg=np.isin(labs,list(border))
    # Background enclosed by the canonical antenna curl; never erase cream iris pixels.
    bg[:8]|=candidate[:8]
    a[bg]=0
    return Image.fromarray(a)


def key_magenta(image):
    a=np.array(image.convert('RGBA'))
    r,g,b=[a[:,:,i].astype(np.int16) for i in range(3)]
    matte=(r>170)&(b>170)&(g<100)&(r>g*1.8)&(b>g*1.8)
    a[matte]=0
    a[~matte,3]=255
    return Image.fromarray(a),matte


def expression_mask():
    m=np.zeros((40,40),bool)
    m[9:20,11:21]=True
    # Small tear area immediately below the existing eye, not across the cheek/muzzle.
    m[19:22,13:20]=True
    m[18:27,5:13]=False  # canonical pink cheek disc
    return m


def build():
    for part in ['portraits_individual','extracted','editable','review']:(OUT/part).mkdir(parents=True,exist_ok=True)
    normal=Image.open(NATIVE/'Normal.png').convert('RGBA')
    subject=native_subject(normal);subject.save(SRC/'Normal_subject.png')
    fg=np.array(subject)[:,:,3]>0
    Image.fromarray(np.uint8(fg)*255).save(SRC/'subject_mask.png')
    ref=Image.new('RGBA',(40,40),(255,0,255,255));ref.alpha_composite(subject)
    ref.resize((400,400),Image.Resampling.NEAREST).save(SRC/'Normal_magenta_x10.png')
    palette=np.unique(np.array(subject)[fg,:3],axis=0).astype(np.int32)
    mask=expression_mask()&fg
    template=Image.open(ROOT/'template.png').convert('RGBA')
    report={'scope':'Politoed base slot0186 front portraits only','source_pin':'3609a86be2a4c8ad7cf255bd2255f044daafe24f','workflow':'generator on pure magenta -> chroma key to alpha -> expression-region cleanup against native Normal -> exact canonical emotion background','anatomy_policy':'Frog identity preserved. No human lips or second smile inside yellow jaw. This closed-mouth batch changes only the original eye and its immediate tear area. Existing canonically open-mouth portraits stay untouched.','generated_limit':10,'generation_blocked':['Sigh','Stunned'],'portraits':{},'template_sha256':hashlib.sha256((ROOT/'template.png').read_bytes()).hexdigest()}
    for emotion in PRESERVE:
        p=NATIVE/(emotion+'.png');dst=OUT/'portraits_individual'/p.name
        shutil.copyfile(p,dst)
        report['portraits'][emotion]={'existing_native_preserved':True,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    shutil.copyfile(NATIVE/'credits.txt',OUT/'native_credits.txt')
    new_subjects={}
    for emotion in C['portrait']['required_full']:
        if emotion in PRESERVE:continue
        raw=SRC/'generation'/f'{emotion}_magenta.png'
        if not raw.exists():continue
        keyed,matte=key_magenta(Image.open(raw))
        assert matte.mean()>.1,(emotion,'source not on magenta')
        keyed.save(OUT/'extracted'/f'{emotion}_keyed.png')
        small=np.array(keyed.resize((40,40),Image.Resampling.NEAREST))
        active=mask&(small[:,:,3]>0)
        rgb=small[:,:,:3].astype(np.int32)
        nearest=palette[np.argmin(((rgb[:,:,None,:]-palette[None,None,:,:])**2).sum(axis=3),axis=2)]
        a=np.array(subject);a[active,:3]=nearest[active]
        assert np.array_equal(a[~mask],np.array(subject)[~mask]),emotion
        assert np.array_equal(a[:,:,3],np.array(subject)[:,:,3]),emotion
        changed=int(np.any(a!=np.array(subject),axis=2).sum())
        assert changed>0,(emotion,'unchanged Normal cannot be a new expression')
        cleaned=Image.fromarray(a);cleaned.save(OUT/'editable'/f'{emotion}_subject.png')
        new_subjects[emotion]=hashlib.sha256(a.tobytes()).hexdigest()
        i=C['portrait']['emotions'].index(emotion)
        bg=template.crop((i%5*40,i//5*40,i%5*40+40,i//5*40+40))
        bg.save(OUT/'editable'/f'{emotion}_canonical_background.png')
        final=bg.copy();final.alpha_composite(cleaned)
        count=len(final.getcolors(9999));assert count<=15,(emotion,count)
        assert np.all(np.array(final)[:,:,3]==255)
        assert np.array_equal(np.array(final)[~fg],np.array(bg)[~fg])
        final.save(OUT/'portraits_individual'/f'{emotion}.png')
        report['portraits'][emotion]={'raw_generated':str(raw.relative_to(ROOT)),'magenta_pixels_removed':int(matte.sum()),'native_face_pixels_changed':changed,'outside_eye_and_tear_area_changed':0,'native_subject_alpha_preserved':True,'visible_canonical_background_pixels_exact':int((~fg).sum()),'canonical_slot':i,'colors':count,'technical_precheck':'PASS','art_approved':False}
    duplicate=[(a,b) for a in new_subjects for b in new_subjects if a<b and new_subjects[a]==new_subjects[b]]
    report['duplicate_new_subject_pairs']=duplicate
    assert not duplicate,duplicate
    report['missing_required']=[n for n in C['portrait']['required_full'] if n not in report['portraits']]
    report['runtime_PMDO']='NOT TESTED'
    sheet=Image.new('RGBA',(200,160));contact=Image.new('RGB',(640,792),(20,29,43));draw=ImageDraw.Draw(contact)
    for j,emotion in enumerate(C['portrait']['required_full']):
        p=OUT/'portraits_individual'/f'{emotion}.png';x=j%4*160;y=j//4*198
        if not p.exists():draw.text((x+5,y+6),emotion+' / MANQUANT',fill=(239,183,143));continue
        im=Image.open(p);i=C['portrait']['emotions'].index(emotion);sheet.paste(im,(i%5*40,i//5*40))
        contact.paste(im.resize((160,160),Image.Resampling.NEAREST),(x,y+25))
        draw.text((x+5,y+6),emotion+(' / natif' if emotion in PRESERVE else ''),fill='white')
    sheet.save(OUT/'portraits_partial.png');contact.save(OUT/'review/expressions_x4.png')
    for emotion in PRESERVE:
        assert hashlib.sha256((NATIVE/(emotion+'.png')).read_bytes()).hexdigest()==report['portraits'][emotion]['sha256']
        assert hashlib.sha256((OUT/'portraits_individual'/(emotion+'.png')).read_bytes()).hexdigest()==report['portraits'][emotion]['sha256']
    sys.path.insert(0,str(ROOT/'source/pmd_character_pipeline'))
    from validate import run
    report['partial_sheet_precheck']=run('portrait',OUT/'portraits_partial.png','minimum')
    report['full_sheet_precheck']=run('portrait',OUT/'portraits_partial.png','full')
    assert report['partial_sheet_precheck']['technical_precheck']=='PASS'
    (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    gallery(report)
    print('New portraits:',len(new_subjects),'preserved:',len(PRESERVE),'missing:',report['missing_required'])


def gallery(report):
    def image(path):return 'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()
    html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Tarpaud • Magenta vers fonds canoniques</title><style>body{font:16px system-ui;background:#141d2b;color:#edf4fa;max-width:1100px;margin:32px auto;padding:0 24px}p{line-height:1.6;color:#b7cbd9}img{max-width:100%;image-rendering:pixelated}.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}section{padding:18px;background:#202d40;border-radius:12px;margin:20px 0}.steps img{width:100%;background:repeating-conic-gradient(#2d394c 0% 25%,#192536 0% 50%) 0 0/16px 16px}h2{font-size:20px}.note{border-left:3px solid #e9bc7d;padding:15px}@media(max-width:700px){.steps{grid-template-columns:1fr}}</style><h1>Tarpaud : génération sur magenta,<br>puis fonds canoniques</h1><p>Le visage Normal natif est la référence. Pas de lèvres humaines, pas de deuxième sourire dans la mâchoire jaune. Les expressions fermées de ce lot utilisent l’œil ; les portraits natifs à bouche ouverte restent intacts.</p><div class="steps">'''
    for title,path in [('1 · Source générée / magenta',SRC/'generation/Happy_magenta.png'),('2 · Détourage / alpha',OUT/'extracted/Happy_keyed.png'),('3 · Nettoyage / fond canonique',OUT/'portraits_individual/Happy.png')]:
        html+='<section><h2>'+title+'</h2><img alt="'+title+'" src="'+image(path)+'"></section>'
    html+='</div><section><h2>Expressions disponibles</h2><img alt="Planche des expressions" src="'+image(OUT/'review/expressions_x4.png')+'"></section><p class="note">10 nouvelles propositions, 4 portraits natifs conservés. Sigh et Stunned restent manquants : limite de génération atteinte. Ce lot est techniquement contrôlé, pas approuvé artistiquement ni testé dans PMDO. Aucun dessin refusé n’est utilisé comme export.</p></html>'
    (ROOT/'apercu_tarpaud_portraits_v1.html').write_text(html)

if __name__=='__main__':build()
