"""Vérifie le rêve plein écran, la caméra 3D, le multiframe et le vrai parcours du quiz."""
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
import base64
import hashlib
import io
import json
import numpy as np
import os

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.cache/reve-tests'


def pixels(page):
    value = page.locator('#world canvas').evaluate('(c)=>c.toDataURL()').split(',')[1]
    return np.array(Image.open(io.BytesIO(base64.b64decode(value))).convert('RGB'))


def verify():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT / 'reve/kit.json').read_text())
    cfg = manifest['atlas'];atlas = Image.open(ROOT / 'reve' / cfg['file']).convert('RGBA')
    n, gap = cfg['frame_size'][0], cfg['gutter'];tile=n+gap*2
    hashes=[]
    for i in range(cfg['frames']):
        x,y=(i%cfg['columns'])*tile+gap,(i//cfg['columns'])*tile+gap
        frame=np.array(atlas.crop((x,y,x+n,y+n)))
        assert not frame[122:134,122:134,3].any(), 'Centre de l’anneau opaque'
        assert not frame[[0,-1],:,3].any() and not frame[:,[0,-1],3].any(), 'Bords d’atlas non transparents'
        hashes.append(hashlib.sha256(frame.tobytes()).hexdigest())
    assert len(set(hashes))==36
    questions=json.loads((ROOT/'source/reve/questions.json').read_text());by_id={q['id']:q for q in questions['questions']}
    natures=json.loads((ROOT/'source/reve/natures.json').read_text())['natures']
    errors,network=[],[]
    launch={'headless':True,'args':['--no-sandbox']}
    if os.environ.get('FALAISE_CHROMIUM'):launch['executable_path']=os.environ['FALAISE_CHROMIUM']
    with sync_playwright() as p:
        browser=p.chromium.launch(**launch)
        context=browser.new_context(offline=True,viewport={'width':1280,'height':720},device_scale_factor=1)
        page=context.new_page()
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
        page.on('request',lambda r:network.append(r.url) if r.url.startswith(('http://','https://')) else None)
        page.goto((ROOT/'apercu_reve.html').as_uri()+'?seed=42')
        page.wait_for_selector('body[data-ready=true]',timeout=60000)
        assert page.evaluate('REVE.getState().render3d'), 'Rendu 3D indisponible'
        page.evaluate('REVE.capture.begin(42);REVE.capture.time(0)')
        initial=page.evaluate('REVE.getState()');a=pixels(page)
        assert initial['logicalReference']==[320,240] and initial['question']==0
        assert initial['result'] is None and not page.locator('#validate').is_enabled()
        assert not any(k in initial for k in ['weights','poids','scores'])
        page.evaluate('REVE.capture.time(2)');b=pixels(page)
        assert page.evaluate('REVE.getState().question')==0, 'Le temps a répondu à la place du joueur'
        assert np.abs(a.astype(int)-b.astype(int)).mean()>1, 'Parallaxe/multiframe immobile'
        assert (b.mean(2)<5).mean()<.02, 'Fond noir fixe'
        page.locator('[data-answer="0"]').click();page.click('#validate')
        assert page.evaluate('REVE.getState().question')==1
        assert not page.evaluate('REVE.validate()'), 'Double validation pendant le mouvement'
        page.evaluate('REVE.capture.time(4)');second=page.evaluate('REVE.getState()')
        assert initial['camera'][0]<0<second['camera'][0]
        assert second['sphere'][2]<initial['sphere'][2]-10 and second['travel']==14
        assert not second['travelling']
        page.click('#previous');page.evaluate('REVE.capture.time(6)')
        assert page.evaluate('REVE.getState().question')==0
        assert page.evaluate('REVE.getState().camera[0]')<0
        page.screenshot(path=str(OUT/'bureau.png'))
        # Huit réponses, résultat et départage identiques aux données du projet de référence.
        page.evaluate('REVE.capture.begin(42)')
        scores={n['id']:0 for n in natures};seen=[]
        for i in range(8):
            state=page.evaluate('REVE.getState()');qid=state['questionId'];seen.append(qid)
            choice=i%len(by_id[qid]['reponses'])
            for key,value in by_id[qid]['reponses'][choice]['poids'].items():scores[key]+=value
            page.evaluate('(i)=>{REVE.select(i);REVE.validate()}',choice)
            page.evaluate('(t)=>REVE.capture.time(t)',(i+1)*2)
        assert len(set(seen))==8
        result=page.evaluate('REVE.getState().result')
        expected=max(natures,key=lambda n:scores[n['id']])
        assert result['id']==expected['id'] and set(result)=={'id','fr','rgb','accent'}
        assert page.locator('#result').is_visible() and page.locator('#dialogue').is_hidden()
        assert 'points' not in page.locator('body').inner_text().lower()
        # Annuler la dernière réponse doit supprimer son poids.
        page.evaluate('REVE.back();REVE.capture.time(18)')
        last=by_id[seen[-1]];old=7%len(last['reponses'])
        for key,value in last['reponses'][old]['poids'].items():scores[key]-=value
        new=(old+1)%len(last['reponses'])
        for key,value in last['reponses'][new]['poids'].items():scores[key]+=value
        page.evaluate('(i)=>{REVE.select(i);REVE.validate()}',new);page.evaluate('REVE.capture.time(20)')
        assert page.evaluate('REVE.getState().result.id')==max(natures,key=lambda n:scores[n['id']])['id']
        page.evaluate('REVE.capture.begin(42);REVE.capture.time(1)')
        sizes=[(320,568),(390,844),(768,1024),(1280,720),(1920,1080),(844,390)]
        for w,h in sizes:
            page.set_viewport_size({'width':w,'height':h})
            page.wait_for_function('([w,h])=>REVE.getState().viewport[0]===w&&REVE.getState().viewport[1]===h',arg=[w,h])
            page.evaluate('REVE.capture.time(1)')
            assert page.locator('#world canvas').evaluate('(c)=>{const b=c.getBoundingClientRect();return[b.width,b.height]}')==[w,h]
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth&&document.documentElement.scrollHeight<=innerHeight')
            for selector in ['#question','#choices','#validate']:
                rect=page.locator(selector).bounding_box();assert rect and rect['x']>=0 and rect['x']+rect['width']<=w+1
            if w in [390,844]:page.screenshot(path=str(OUT/f'viewport_{w}x{h}.png'))
        page.set_viewport_size({'width':1280,'height':720})
        page.click('#fullscreen')
        page.wait_for_function('document.fullscreenElement!==null||document.querySelector("#notice").textContent.length>0')
        fullscreen=page.evaluate('document.fullscreenElement!==null')
        if fullscreen:page.evaluate('document.exitFullscreen()')
        # Rendu dans une iframe opaque, comme les viewers de fichiers.
        page.set_content('<iframe id="x" sandbox="allow-scripts" style="width:100%;height:700px;border:0"></iframe>')
        page.locator('#x').evaluate('(f,s)=>f.srcdoc=s',(ROOT/'apercu_reve.html').read_text())
        frame=page.frame_locator('#x');frame.locator('body[data-ready=true]').wait_for(timeout=60000)
        frame.locator('[data-answer="0"]').click();frame.locator('#validate').click()
        frame.locator('#chapter').filter(has_text='QUESTION 2').wait_for()
        reduced=browser.new_context(offline=True,reduced_motion='reduce')
        reduced_page=reduced.new_page();reduced_page.goto((ROOT/'apercu_reve.html').as_uri())
        reduced_page.wait_for_selector('body[data-ready=true]',timeout=60000)
        assert reduced_page.evaluate('REVE.getState().paused')
        t=reduced_page.evaluate('REVE.getState().clock');reduced_page.wait_for_timeout(400)
        assert reduced_page.evaluate('REVE.getState().clock')==t
        assert not errors,errors
        assert not network,network
        version=browser.version;browser.close()
    report={'webgl_3d':True,'sphere_voyage':True,'pov_gauche_droite_par_question':True,'fond_multicolore_non_noir':True,
            'phases_circulaires_distinctes':36,'question_uniquement_sur_validation':True,'retour_annule_la_reponse':True,
            'resultat_conforme_aux_donnees':True,'poids_non_affiches':True,'plein_viewport':sizes,'fullscreen_api':fullscreen,
            'iframe_sandbox':True,'hors_ligne':True,'mouvement_reduit':True,'erreurs_js':errors,'requetes_reseau':network,'chromium':version}
    (ROOT/'reve/controle_qualite.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return report


if __name__=='__main__':verify()
