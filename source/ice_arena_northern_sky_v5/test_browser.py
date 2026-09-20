"""Real headless Chromium checks. Requires Playwright; not a PMDO GPU test.
Default uses installed Playwright Chromium. An optional local, untracked
.cache/browser/launch.json can supply an executable_path and args.
"""
from pathlib import Path
import json, sys, os, io
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[2];O=R/'renders/ice_arena_northern_sky_v5'
URL=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8768'
checks=[]
def check(name,value,detail=None):
 assert value,name
 checks.append({'check':name,'status':'PASS','detail':detail})
def pixels(raw):return np.array(Image.open(io.BytesIO(raw)).convert('RGB')).astype(int)
with sync_playwright() as p:
 cfg={};local=R/'.cache/browser/launch.json'
 if local.exists():
  cfg=json.loads(local.read_text())
  # Optional runtime libraries from the downloaded serverless Chromium package.
  if Path('/tmp/al2023/lib').exists():cfg['env']={**os.environ,'LD_LIBRARY_PATH':'/tmp/al2023/lib:/tmp','FONTCONFIG_PATH':'/tmp/fonts'}
 browser=p.chromium.launch(headless=True,**cfg);version=browser.version
 page=browser.new_page(viewport={'width':1280,'height':1200},device_scale_factor=1)
 errors=[];failed=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('response',lambda r:failed.append(r.url) if r.status>=400 and 'favicon' not in r.url else None)
 page.goto(URL,wait_until='networkidle')
 def ready():page.wait_for_function("Array.from(document.querySelectorAll('#scene img')).every(i=>i.complete&&i.naturalWidth>0)")
 ready();check('All six scene images load in actual Chromium',True)
 check('Default desktop view is native size',page.locator('#scene').bounding_box()['width']==512)
 first=pixels(page.locator('#scene').screenshot());page.wait_for_timeout(450);second=pixels(page.locator('#scene').screenshot())
 terrain=np.array(Image.open(O/'layers/NorthernSkyV5_Terrain.png').convert('RGBA'));mask=terrain[:,:,3]==255
 check('WebP aurora really animates in browser',np.any(first[:288]!=second[:288]))
 check('Opaque terrain remains stationary while sky animates',np.array_equal(first[mask],second[mask]))
 page.click('#reset');ready()
 check('Phase-zero button opens PNG inspection',page.evaluate('window.viewerV5.getState().frame===0&&!window.viewerV5.getState().animation'))
 screen=pixels(page.locator('#scene').screenshot());ref=np.array(Image.open(O/'composition.png').convert('RGB')).astype(int)
 diff=np.abs(screen-ref)
 check('Actual browser phase-zero rendering matches PNG within 2 levels',int(diff.max())<=2,{'max_RGB_error':int(diff.max()),'mean_RGB_error':float(diff.mean())})
 page.click('#previous');ready();check('Previous wraps zero to191',page.evaluate('window.viewerV5.getState().frame')==191)
 page.click('#next');ready();check('Next wraps191 tozero',page.evaluate('window.viewerV5.getState().frame')==0)
 page.locator('#phase').fill('96');page.locator('#phase').dispatch_event('input');ready()
 check('Scrub selects exact aurora and star PNGs',page.locator('#aurora').get_attribute('src').endswith('_096.png') and page.locator('#stars').get_attribute('src').endswith('_32.png'))
 check('Inspection clouds are placed at the selected time',page.locator('#clouds').evaluate("e=>getComputedStyle(e).transform")=='matrix(1, 0, 0, 1, -6, 0)')
 for layer in ['sky','stars','aurora','clouds','terrain']:
  selector=f'[data-layer="{layer}"]';page.locator(selector).uncheck();check('Layer toggle hides '+layer,page.locator('#'+layer).is_hidden());page.locator(selector).check();check('Layer toggle restores '+layer,page.locator('#'+layer).is_visible())
 page.locator('[data-layer="stars"]').uncheck();page.click('#play');ready()
 check('Animation resumes using WebP',page.locator('#aurora').get_attribute('src')=='aurora_loop.webp')
 check('Hidden layers survive mode change',page.locator('#stars').is_hidden());page.locator('[data-layer="stars"]').check()
 check('Cloud drift does not reset every6.4s',page.locator('#clouds').evaluate("e=>getComputedStyle(e).animationDuration")=='720s')
 # Seek the actual CSS animation across an aurora boundary, not an elapsed sleep.
 before=page.locator('#clouds').evaluate("e=>{e.getAnimations()[0].pause();e.getAnimations()[0].currentTime=6300;return getComputedStyle(e).transform}")
 after=page.locator('#clouds').evaluate("e=>{e.getAnimations()[0].currentTime=6600;return getComputedStyle(e).transform}")
 check('Cloud displacement continues through6.4s boundary',before=='matrix(1, 0, 0, 1, -12, 0)' and after=='matrix(1, 0, 0, 1, -13, 0)')
 page.locator('#zoom').select_option('2');check('2x zoom updates scroll surface',page.locator('#sizer').evaluate('e=>e.style.width')=='1024px' and page.locator('#sizer').evaluate('e=>e.style.height')=='1728px')
 page.locator('#zoom').select_option('fit');page.click('#reset');ready()
 page.set_viewport_size({'width':390,'height':844});page.wait_for_function("document.querySelector('#scene').getBoundingClientRect().width<=document.querySelector('.viewport').clientWidth+1")
 check('Mobile fit shows the whole scene width',page.locator('#scene').bounding_box()['width']<=page.locator('.viewport').evaluate('e=>e.clientWidth')+1)
 check('No mobile page-level horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
 page.set_viewport_size({'width':1280,'height':1200});page.wait_for_function("document.querySelector('#scene').getBoundingClientRect().width===512")
 page.screenshot(path=str(R/'.cache/browser/review_v5.png'),full_page=True)
 check('No JavaScript errors',not errors,errors);check('No failed page assets',not failed,failed)
 browser.close()
report={'count':len(checks),'checks':checks,'status':'PASS','browser':version,'renderer':'real headless Chromium (software rendering)','PMDO_GPU_tested':False}
(O/'browser_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(f'{len(checks)} actual Chromium checks PASS ({version}). No PMDO runtime test.')
