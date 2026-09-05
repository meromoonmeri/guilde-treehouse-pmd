from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
import json,io,base64,os,numpy as np
R=Path(__file__).resolve().parents[1];C=Path('/home/user/.cache/pmd_browser');C.mkdir(parents=True,exist_ok=True)
M=json.loads((R/'kit.json').read_text());errors=[];maximum=0;checks=0
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage'],**({'executable_path':os.environ['PMD_CHROMIUM']} if os.environ.get('PMD_CHROMIUM') else {}));ctx=b.new_context(offline=True,viewport={'width':1280,'height':1000},device_scale_factor=1);page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto((R/'apercu_pmd.html').as_uri());page.wait_for_selector('body[data-ready=true]')
 for room in M['salles']:
  page.select_option('#room',room['id']);page.click('#reset')
  for mode in ['jour','nuit']:
   page.click(f'[data-mode={mode}]')
   base=Image.open(R/room['fichiers'][mode]['base']).convert('RGBA')
   for weather in M['ambiances']:
    page.select_option('#weather',weather);raw=page.locator('#map').evaluate('(c)=>c.toDataURL()').split(',')[1]
    actual=np.array(Image.open(io.BytesIO(base64.b64decode(raw))).convert('RGBA'));expected=Image.open(R/'fenetres_exterieur'/room['id']/(weather+'.png')).convert('RGBA');expected.alpha_composite(base)
    delta=int(np.abs(actual.astype(int)-np.array(expected).astype(int)).max());assert delta<=2,(room['id'],mode,weather,delta);maximum=max(maximum,delta);checks+=1
  page.click('#base');raw=page.locator('#map').evaluate('(c)=>c.toDataURL()').split(',')[1];a=np.array(Image.open(io.BytesIO(base64.b64decode(raw))).convert('RGBA'));mask=np.array(Image.open(R/'fenetres_exterieur'/room['id']/'masque.png'))>0;assert not a[:,:,3][mask].any()
  assert page.locator('#stage').evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(255, 0, 255)';page.click('#composite')
  for k in [6,7]:assert page.locator(f'input[data-layer="{k}"]').is_disabled()
  baseline=page.locator('#map').evaluate('(c)=>c.toDataURL()')
  for k in [8,9]:
   cb=page.locator(f'input[data-layer="{k}"]');assert cb.is_enabled();cb.uncheck()
   assert page.locator('#map').evaluate('(c)=>c.toDataURL()')!=baseline,(room['id'],k,'effet invisible')
   cb.check();assert page.locator('#map').evaluate('(c)=>c.toDataURL()')==baseline
 page.select_option('#room','02');page.click('[data-mode=jour]');page.select_option('#weather','jour');page.click('#reset')
 page.screenshot(path=C/'desktop.png',full_page=True);page.click('#base');page.screenshot(path=C/'base_magenta.png',full_page=True);page.click('#composite')
 static=page.evaluate('''async()=>{let c=document.querySelector('#map'),a=c.toDataURL();await new Promise(r=>setTimeout(r,800));return c.toDataURL()===a}''');assert static
 page.set_viewport_size({'width':390,'height':844});page.screenshot(path=C/'mobile.png',full_page=True);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.click('#tabland');page.select_option('#weather','orageux');page.click('#tabrooms')
 html=(R/'apercu_pmd.html').read_text();page.set_content('<iframe id="x" sandbox="allow-scripts" style="width:100%;height:850px"></iframe>');page.locator('#x').evaluate('(f,s)=>f.srcdoc=s',html);f=page.frame_locator('#x');f.locator('body[data-ready=true]').wait_for();f.locator('#room').select_option('05');f.locator('#weather').select_option('aube');f.locator('#base').click();f.locator('#grid').check()
 assert not errors,errors;b.close()
report={'comparaisons':checks,'erreur_max_par_canal':maximum,'bases_fenetres_transparentes':True,'magenta_verifie':True,'fixe_dans_le_temps':static,'mobile_390px':'sans débordement','hors_ligne':True,'sandbox_allow_scripts':True,'erreurs_js':errors,'calques_contacts_lumiere_activables':True}
(R/'controle_navigateur.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
