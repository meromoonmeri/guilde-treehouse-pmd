"""Compare les deux scènes du navigateur aux pixels et phases des exports."""
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
import base64
import io
import json
import numpy as np
import os
from verify_falaise import references, expected, samples

R = Path(__file__).resolve().parents[1]
C = R / '.cache/exterieurs-v4/navigateur'


def actual(page):
    data = page.locator('#map').evaluate('(c)=>c.toDataURL()').split(',')[1]
    return np.array(Image.open(io.BytesIO(base64.b64decode(data))).convert('RGBA'))


def visual_delta(a, b):
    def premultiplied(q):
        a = np.asarray(q, dtype=float).copy()
        a[:, :, :3] *= a[:, :, 3:4]/255
        return a
    return float(np.abs(premultiplied(a)-premultiplied(b)).max())


def verify():
    C.mkdir(parents=True, exist_ok=True)
    errors, requests = [], []
    launch = {'headless': True, 'args': ['--no-sandbox']}
    if os.environ.get('FALAISE_CHROMIUM'):
        launch['executable_path'] = os.environ['FALAISE_CHROMIUM']
    reports = []
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch)
        context = browser.new_context(offline=True, viewport={'width': 1280, 'height': 1000}, device_scale_factor=1)
        page = context.new_page()
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('request', lambda r: requests.append(r.url) if r.url.startswith(('http://', 'https://')) else None)
        page.goto((R / 'apercu_falaise.html').as_uri())
        page.wait_for_selector('body[data-ready=true]')
        assert page.evaluate('FALAISE.getState().running')
        start = page.evaluate('FALAISE.getState().frame')
        page.wait_for_function('(n)=>FALAISE.getState().frame!==n', arg=start, timeout=4000)
        page.evaluate('FALAISE.pause()')
        # Une reprise peut précéder un RAF déjà horodaté : jamais de frame -1,
        # qui ferait chercher une image inexistante dans les cycles exportés.
        page.evaluate('''() => {
            FALAISE.setFrame(0);document.querySelector('#animation').click();
            const raf=window.requestAnimationFrame;window.requestAnimationFrame=()=>0;
            try {tick(performance.now()-16);if(FALAISE.getState().frame<0)throw new Error('Frame négative')}
            finally {window.requestAnimationFrame=raf;FALAISE.pause()}
        }''')
        for scene in ['falaise', 'sharpedo']:
            root = R / scene
            m = json.loads((root / 'kit.json').read_text(encoding='utf-8'))
            size, count = tuple(m['dimensions']), m['animation']['frames']
            page.click(f'[data-scene="{scene}"]')
            assert page.evaluate('FALAISE.getState().scene') == scene
            assert page.locator('#map').evaluate('(c)=>[c.width,c.height]') == list(size)
            page.click('[data-sky="nuit"]')
            assert page.evaluate('FALAISE.getState().mode') == 'nuit'
            assert page.locator('[data-sky="nuit"]').get_attribute('aria-pressed') == 'true'
            page.click('[data-sky="jour"]')
            comparisons, max_delta = 0, 0
            for mode in m['ambiances']:
                page.select_option('#ambiance', mode)
                refs = references(root, m, mode)
                for frame in samples(count):
                    page.evaluate('(f)=>FALAISE.setFrame(f)', frame)
                    delta = visual_delta(actual(page), expected(refs, frame, size))
                    assert delta <= 2, (scene, mode, frame, delta)
                    max_delta = max(max_delta, delta)
                    comparisons += 1
                page.evaluate('FALAISE.setFrame(7)')
                for i in range(len(m['calques'])):
                    check = page.locator(f'input[data-layer="{i}"]')
                    if check.is_disabled():
                        assert not refs[i].array[:, :, 3].any()
                        continue
                    check.uncheck()
                    delta = visual_delta(actual(page), expected(refs, 7, size, excluded=i))
                    assert delta <= 2, (scene, mode, i, 'Calque masqué', delta)
                    max_delta = max(max_delta, delta)
                    page.locator(f'input[data-layer="{i}"]').check()
                page.click('#base')
                delta = visual_delta(actual(page), expected(refs, 7, size, base_start=m['base_start']))
                assert delta <= 2
                assert page.locator('#stage').evaluate('(e)=>getComputedStyle(e).backgroundColor') == 'rgb(255, 0, 255)'
                page.locator('input[data-layer="0"]').check()
                assert page.locator('#composite').evaluate('(e)=>e.classList.contains("on")')
                assert not page.locator('#base').evaluate('(e)=>e.classList.contains("on")')
                for selector, key in [('#png', 'composition'), ('#ase', 'aseprite'), ('#tiled', 'tiled')]:
                    f = m['fichiers'][mode]
                    assert page.locator(selector).get_attribute('href') == scene+'/'+f[key]
                    assert (root / f[key]).is_file()
                if scene == 'sharpedo':
                    assert page.locator('#tileset').is_visible()
                    assert page.locator('#tileset').get_attribute('href') == scene+'/'+m['fichiers'][mode]['tileset_bordures']['png']
                else:
                    assert page.locator('#tileset').is_hidden()
                page.evaluate('FALAISE.setFrame(0)')
                if mode in ['jour', 'nuit']:
                    page.screenshot(path=str(C / f'{scene}_{mode}.png'), full_page=True)
                print('PASS navigateur', scene, mode, flush=True)
            page.select_option('#ambiance', 'nuit')
            page.evaluate('FALAISE.setFrame(0)')
            page.click('#base')
            before = actual(page)
            page.click('#animation')
            page.wait_for_function('FALAISE.getState().frame>=3', timeout=4000)
            assert np.array_equal(actual(page), before), 'Le terrain fixe est animé'
            page.click('#animation')
            paused = page.evaluate('FALAISE.getState().frame')
            page.wait_for_timeout(550)
            assert page.evaluate('FALAISE.getState().frame') == paused
            page.click('#composite')
            page.evaluate('FALAISE.setFrame(0)')
            widths = [320, 390, 680, 950, 1280]
            for width in widths:
                page.set_viewport_size({'width': width, 'height': 844})
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), (scene, width)
                if width == 390:
                    page.screenshot(path=str(C / f'{scene}_mobile.png'), full_page=True)
            page.select_option('#zoom', '2')
            assert page.locator('#map').evaluate('(c)=>c.getBoundingClientRect().width') == size[0]*2
            page.select_option('#zoom', 'fit')
            page.check('#grid')
            page.uncheck('#grid')
            page.select_option('#speed', '2')
            assert page.evaluate('FALAISE.getState().speed') == 2
            page.select_option('#speed', '1')
            reports.append({'scene': scene, 'comparaisons': comparisons, 'erreur_max_par_canal_premultiplie': round(max_delta, 4),
                            'calques_masquables': True, 'terrain_fixe': True, 'lecture_pause': True,
                            'boutons_jour_nuit': True, 'largeurs_sans_debordement': widths})
        page.set_content('<iframe id="x" sandbox="allow-scripts" style="width:100%;height:900px"></iframe>')
        page.locator('#x').evaluate('(f,s)=>f.srcdoc=s', (R / 'apercu_falaise.html').read_text(encoding='utf-8'))
        f = page.frame_locator('#x')
        f.locator('body[data-ready=true]').wait_for()
        f.locator('[data-scene="sharpedo"]').click()
        f.locator('[data-sky="nuit"]').click()
        f.locator('input[data-layer="4"]').uncheck()
        f.locator('#reset').click()
        reduced = browser.new_context(offline=True, reduced_motion='reduce')
        page2 = reduced.new_page()
        page2.on('pageerror', lambda e: errors.append(str(e)))
        page2.goto((R / 'apercu_falaise.html').as_uri())
        page2.wait_for_selector('body[data-ready=true]')
        assert not page2.evaluate('FALAISE.getState().running')
        assert not errors, errors
        assert not requests, requests
        version = browser.version
        browser.close()
    for report in reports:
        report.update(hors_ligne=True, sandbox_allow_scripts=True, mouvement_reduit=True,
                      requetes_reseau=requests, erreurs_js=errors, chromium=version)
        (R / report['scene'] / 'controle_navigateur.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(reports, ensure_ascii=False, indent=2))
    return reports


if __name__ == '__main__':
    verify()
