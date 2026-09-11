"""Contrôle des nouveaux paysages : sources, calques, exports et aperçu hors ligne."""
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
import json
import numpy as np
import os
from prepare_paysages_nouveaux import CONFIG
from verify_falaise import references, expected, verify_ase, verify_tiled, image
from verify_falaise_browser import actual, visual_delta

R=Path(__file__).resolve().parents[1]
C=R/'.cache/paysages-tests'


def verify():
    C.mkdir(parents=True,exist_ok=True)
    reports=[]
    for name,cfg in CONFIG.items():
        root=R/'paysages'/name;m=json.loads((root/'kit.json').read_text());size=tuple(m['dimensions'])
        assert size==tuple(cfg['size']) and m['regles']['structures'] is False
        assert m['animation']['frames']==24 and m['animation']['duree_image_ms']==250
        report={'id':name,'dimensions':list(size),'calques':6,'structures_retirees_controle_visuel':True,'recomposition_exacte':True,'ambiances':[]}
        for mode in ['jour','nuit']:
            refs=references(root,m,mode);f=m['fichiers'][mode]
            equal=np.array_equal
            composed=expected(refs,0,size)
            assert equal(np.array(composed),np.array(image(root/f['composition'])))
            assert equal(np.array(expected(refs,0,size,base_start=4)),np.array(image(root/f['base'])))
            assert not refs[5].array[:,:,3].any()
            if mode=='jour':
                original=Image.open(R/'source/paysages_nouveaux'/name/'generation_jour.png').convert('RGB')
                assert equal(np.array(composed)[:,:,:3],np.array(original)),name
            for ref in refs:
                assert equal(np.array(ref.at(0)),np.array(ref.at(24)))
                if ref.spec and ref.spec['kind']=='stars':
                    moon=(ref.groups==0)&(ref.array[:,:,3]>0)
                    assert equal(np.array(ref.at(7))[moon],ref.array[moon])
            verify_ase(root/f['aseprite'],refs,size,24,250)
            verify_tiled(root/f['tiled'],refs,size,24,250)
            report['ambiances'].append({'id':mode,'PNG_Aseprite_Tiled':'identiques','frames_verifiees':24})
        reports.append(report)
        print('PASS fichiers',name,flush=True)
    errors=[];network=[];launch={'headless':True,'args':['--no-sandbox']}
    if os.environ.get('FALAISE_CHROMIUM'):launch['executable_path']=os.environ['FALAISE_CHROMIUM']
    with sync_playwright() as p:
        browser=p.chromium.launch(**launch)
        context=browser.new_context(offline=True,viewport={'width':1280,'height':1000},device_scale_factor=1)
        page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('request',lambda q:network.append(q.url) if q.url.startswith(('http://','https://')) else None)
        page.goto((R/'apercu_falaise.html').as_uri());page.wait_for_selector('body[data-ready=true]',timeout=60000)
        page.evaluate('FALAISE.pause()')
        for report in reports:
            name=report['id'];root=R/'paysages'/name;m=json.loads((root/'kit.json').read_text());size=tuple(m['dimensions']);maximum=0
            page.click(f'[data-scene="{name}"]')
            assert page.evaluate('FALAISE.getState().scene')==name
            for mode in ['jour','nuit']:
                page.click(f'[data-sky="{mode}"]');refs=references(root,m,mode)
                for frame in [0,1,2,6,12,23]:
                    page.evaluate('(n)=>FALAISE.setFrame(n)',frame)
                    delta=visual_delta(actual(page),expected(refs,frame,size));maximum=max(maximum,delta)
                    assert delta<=2,(name,mode,frame,delta)
                page.evaluate('FALAISE.setFrame(0)');page.screenshot(path=str(C/f'{name}_{mode}.png'),full_page=True)
                for i in range(6):
                    check=page.locator(f'input[data-layer="{i}"]')
                    if check.is_disabled():continue
                    check.uncheck();delta=visual_delta(actual(page),expected(refs,0,size,excluded=i));maximum=max(maximum,delta)
                    assert delta<=2,(name,mode,i,delta)
                    page.locator(f'input[data-layer="{i}"]').check()
                for selector,key in [('#png','composition'),('#ase','aseprite'),('#tiled','tiled')]:
                    assert page.locator(selector).get_attribute('href')=='paysages/'+name+'/'+m['fichiers'][mode][key]
                page.click('#base');assert visual_delta(actual(page),expected(refs,0,size,base_start=4))<=2;page.click('#composite')
            for width in [320,390,768,1280]:
                page.set_viewport_size({'width':width,'height':844})
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(name,width)
            report['comparaisons_navigateur']=12;report['erreur_max_premultiplie']=round(maximum,4)
            report['mobile_sans_debordement']=True;report['hors_ligne']=True
            print('PASS navigateur',name,maximum,flush=True)
        assert not errors,errors;assert not network,network;browser.close()
    for report in reports:
        report['erreurs_js']=errors;report['requêtes_réseau']=network
        (R/'paysages'/report['id']/'controle_qualite.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return reports


if __name__=='__main__':verify()
