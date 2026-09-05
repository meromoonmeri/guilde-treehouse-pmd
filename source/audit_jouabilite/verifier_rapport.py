"""Vérifie l'atelier d'audit hors ligne et rend le plan PNG / le PDF."""
from pathlib import Path
import json,os
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'plans/guilde_4_niveaux'
CACHE=ROOT/'.cache/audit_jouabilite'
CACHE.mkdir(exist_ok=True,parents=True)


def verify():
    errors=[];launch={'headless':True,'args':['--no-sandbox','--disable-dev-shm-usage']}
    if os.environ.get('PMD_CHROMIUM'):launch['executable_path']=os.environ['PMD_CHROMIUM']
    with sync_playwright() as p:
        browser=p.chromium.launch(**launch)
        context=browser.new_context(offline=True,viewport={'width':1440,'height':1100})
        page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto((OUT/'index.html').as_uri());page.wait_for_selector('body[data-ready="true"]')
        assert page.locator('#route').inner_text().startswith('2 changement(s) d’étage · 3 changement(s) de scène cibles')
        levels={3:7,2:5,1:6,0:4}
        # Chaque zone n'est dessinée que sur son propre étage.
        for z,count in levels.items():
            page.click(f'[data-level="{z}"]')
            assert page.locator('#map [data-zone]').count()==count,(z,count)
        page.select_option('#start','05');page.select_option('#end','04');page.click('#calc')
        assert '0 changement(s) d’étage' in page.locator('#route').inner_text()
        page.locator('#route [data-jump="04"]').click()
        assert page.locator('#level-title').inner_text().startswith('R+1')
        assert '04' in page.locator('#details h3').inner_text()
        page.select_option('#end','12');page.click('#calc')
        assert '02' in page.locator('#route').inner_text() and '12' in page.locator('#route').inner_text()
        # Les trois recalages sont effectivement visibles dans le laboratoire.
        for room,port in [('03','ouest'),('03','echelle_nord'),('04','est')]:
            page.select_option('#lab-room',room)
            value=page.locator('#lab-port option').evaluate_all('(els,p)=>els.find(e=>e.textContent===p).value',port)
            page.select_option('#lab-port',value);page.select_option('#lab-size','24')
            page.uncheck('#canonical')
            assert page.locator('#lab-result').inner_text()=='Empreinte en conflit',(room,port,'ancien')
            page.check('#canonical')
            assert page.locator('#lab-result').inner_text()=='Pieds sur le sol',(room,port,'plan')
        page.select_option('#lab-room','03');page.select_option('#lab-port','0');page.select_option('#lab-size','32')
        assert page.locator('#lab-result').inner_text()=='Empreinte en conflit'
        page.click('#recenter');assert page.locator('#lab-result').inner_text()=='Pieds sur le sol'
        text=page.locator('#lab-caption').inner_text();page.locator('#lab').press('ArrowRight')
        assert page.locator('#lab-caption').inner_text()!=text,'Déplacement du gabarit inactif'
        page.click('[data-level="3"]');page.select_option('#end','TERRASSE');page.click('#calc')
        page.evaluate('window.scrollTo(0,0)');page.screenshot(path=CACHE/'rapport_desktop.png',full_page=False)
        page.locator('#collision').screenshot(path=CACHE/'laboratoire.png')
        page.set_viewport_size({'width':390,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),'Débordement mobile'
        page.evaluate('window.scrollTo(0,0)');page.screenshot(path=CACHE/'rapport_mobile.png',full_page=False)
        page.set_viewport_size({'width':1440,'height':1100})
        # PDF : toutes les pages de plans sont rendues, pas uniquement l'onglet sélectionné.
        page.pdf(path=str(OUT/'rapport.pdf'),format='A4',print_background=True,prefer_css_page_size=True)
        # Isoler le document SVG pour une planche PNG lisible.
        svg=(OUT/'plan_canonique.svg').read_text()
        page.set_content('<style>html,body{margin:0;background:#f7f5eb}svg{display:block}body>svg{width:1240px;height:2880px}</style>'+svg)
        page.set_viewport_size({'width':1240,'height':900})
        page.screenshot(path=OUT/'plan_canonique.png',full_page=True)
        # Même isolation que l'afficheur Arena.
        page.set_content('<iframe id="f" sandbox="allow-scripts" style="width:1200px;height:900px"></iframe>')
        page.locator('#f').evaluate('(f,html)=>f.srcdoc=html',(OUT/'index.html').read_text())
        frame=page.frame_locator('#f');frame.locator('body[data-ready="true"]').wait_for()
        frame.locator('[data-level="0"]').click();assert frame.locator('#level-title').inner_text().startswith('RDC')
        assert not errors,errors
        browser.close()
    result={'hors_ligne':True,'niveaux_affiches':4,'routes_interactives':True,'trois_recalages_verifies_visuellement':True,
            'gabarit_deplacable':True,'mobile_390px_sans_debordement':True,'iframe_allow_scripts':True,'erreurs_js':errors,
            'pdf':'rapport.pdf','plan_png':'plan_canonique.png','limite':'Tests de l’outil d’audit, pas d’un moteur de jeu.'}
    (OUT/'controle_navigateur.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('PASS rapport : 4 niveaux, trajets, recalages, gabarit, mobile, hors ligne et iframe ; PDF et PNG rendus.')

if __name__=='__main__':verify()
