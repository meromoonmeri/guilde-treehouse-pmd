"""Captures GIF des vrais rendus : deux validations/retours dans le rêve et la guilde."""
from pathlib import Path
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright
import json
import os
import subprocess
import imageio_ffmpeg
from verify_falaise import references, expected

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.cache/gif-previews'
OUTPUT = ROOT / 'previews'


def export():
    CACHE.mkdir(parents=True, exist_ok=True);OUTPUT.mkdir(exist_ok=True)
    dream_frames=CACHE/'reve';dream_frames.mkdir(exist_ok=True)
    launch={'headless':True,'args':['--no-sandbox']}
    if os.environ.get('FALAISE_CHROMIUM'):launch['executable_path']=os.environ['FALAISE_CHROMIUM']
    errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(**launch)
        page=browser.new_page(viewport={'width':1280,'height':720},device_scale_factor=1)
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto((ROOT/'apercu_reve.html').as_uri()+'?seed=42')
        page.wait_for_selector('body[data-ready=true]',timeout=60000)
        page.evaluate('REVE.capture.begin(42)')
        for f in range(144):
            time=f/12
            page.evaluate('(t)=>REVE.capture.time(t)',time)
            if f in [18,48]:page.evaluate('REVE.select(0);REVE.validate()')
            if f in [78,108]:page.evaluate('REVE.back()')
            page.evaluate('(t)=>REVE.capture.time(t)',time)
            page.screenshot(path=str(dream_frames/f'{f:04d}.png'))
        assert not errors,errors
        browser.close()
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    command=[ffmpeg,'-y','-loglevel','error','-framerate','12','-i',str(dream_frames/'%04d.png'),
             '-filter_complex','fps=10,scale=640:360:flags=lanczos,split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=5',
             '-loop','0',str(OUTPUT/'reve_personnalite.gif')]
    subprocess.run(command,check=True,timeout=180)
    root=ROOT/'falaise';m=json.loads((root/'kit.json').read_text());frames=[]
    for mode in ['jour','nuit']:
        refs=references(root,m,mode)
        for i in range(16):
            image=expected(refs,i,tuple(m['dimensions'])).convert('RGB')
            board=Image.new('RGB',(480,428),(21,28,29));board.paste(image,(0,0))
            d=ImageDraw.Draw(board);d.text((10,413),'Guilde — '+('Jour' if mode=='jour' else 'Nuit')+' · reprise entière EoS',fill=(237,222,182))
            frames.append(board.quantize(colors=256,dither=Image.Dither.NONE))
    frames[0].save(OUTPUT/'falaise_guilde_eos.gif',save_all=True,append_images=frames[1:],duration=250,loop=0,optimize=False)
    for name in ['reve_personnalite.gif','falaise_guilde_eos.gif']:
        with Image.open(OUTPUT/name) as im:print(name,im.size,im.n_frames,'frames,',(OUTPUT/name).stat().st_size,'octets')


if __name__=='__main__':export()
