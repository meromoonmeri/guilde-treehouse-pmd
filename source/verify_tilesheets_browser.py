"""Atelier hors ligne : 13 plans, presets d'isolation et banques inchangées."""
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
import base64
import io
import json
import os
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "tilesheets"
CACHE = ROOT / ".cache/tilesheets_browser"
CACHE.mkdir(parents=True, exist_ok=True)


def canvas(page):
    data = page.locator("#view").evaluate("c=>c.toDataURL()").split(",")[1]
    return np.array(Image.open(io.BytesIO(base64.b64decode(data))).convert("RGBA"))


def composite(files, indices):
    layers = [Image.open(KIT / p).convert("RGBA") for p in files]
    out = Image.new("RGBA", layers[0].size)
    for i in indices:
        out.alpha_composite(layers[i])
    return np.array(out)


def check():
    manifest = json.loads((KIT / "kit.json").read_text())
    errors, comparisons, isolates = [], 0, 0
    launch = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage"]}
    if os.environ.get("PMD_CHROMIUM"):
        launch["executable_path"] = os.environ["PMD_CHROMIUM"]
    presets = {"floor": [3], "walls": [4, 5], "immersion": [0, 1, 2, 11, 12], "transparent": list(range(1, 13))}
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch)
        context = browser.new_context(offline=True, viewport={"width": 1440, "height": 1120}, device_scale_factor=1)
        page = context.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto((KIT / "apercu.html").as_uri())
        page.wait_for_selector('body[data-ready="true"]')
        assert page.locator('#layers input[type="checkbox"]').count() == 13
        assert page.locator("#title").text_content() == manifest["modules"][0]["nom"]
        page.screenshot(path=CACHE / "couloir_v2.png", full_page=True)
        for i, module in enumerate(manifest["modules"]):
            page.select_option("#module", str(i))
            assert page.locator("#exits span").count() == len(module["acces"])
            for mode in ["jour", "nuit"]:
                page.click(f'[data-mode="{mode}"]')
                page.click('[data-preset="all"]')
                expected = np.array(Image.open(KIT / module["fichiers"][mode]["png"]).convert("RGBA"))
                assert np.array_equal(canvas(page), expected), (module["id"], mode)
                comparisons += 1
                for name, indices in presets.items():
                    page.click(f'[data-preset="{name}"]')
                    expected = composite(module["fichiers"][mode]["calques"], indices)
                    assert np.array_equal(canvas(page), expected), (module["id"], mode, name)
                    isolates += 1
        page.select_option("#module", "0")
        page.click('[data-mode="jour"]')
        page.click('[data-preset="all"]')
        full = canvas(page)
        for i in [0, 3, 4, 5, 6, 7, 11, 12]:
            box = page.locator(f'input[data-layer="{i}"]')
            box.uncheck()
            assert not np.array_equal(canvas(page), full), ("calque sans effet visible", i)
            box.check()
            assert np.array_equal(canvas(page), full)
        page.click('[data-preset="walls"]')
        page.screenshot(path=CACHE / "murs_seuls.png", full_page=True)
        page.click('[data-preset="immersion"]')
        page.screenshot(path=CACHE / "immersion_seule.png", full_page=True)
        page.select_option("#module", "6")
        page.click('[data-preset="all"]')
        page.screenshot(path=CACHE / "palier_v2.png", full_page=True)
        page.click('[data-tab="structure"]')
        for c in manifest["architecture"]["catalogues"]:
            page.select_option("#architecture", c["id"])
            actual = page.locator("#view").evaluate("c=>[c.width,c.height]")
            assert actual == c["dimensions_atlas"]
        # Les autres planches ne sont ni supprimées ni remplacées par l'architecture.
        page.click('[data-tab="objets"]')
        assert np.array_equal(canvas(page), np.array(Image.open(KIT / "objets/objets_jour.png").convert("RGBA")))
        for i, obj in enumerate(manifest["objets"]):
            page.select_option("#object", str(i))
            assert page.locator("#title").text_content() == obj["nom"]
            assert canvas(page).shape[:2] == tuple(reversed(obj["taille"]))
        page.click('[data-tab="parquet"]')
        page.uncheck("#spiral-visible")
        floor = canvas(page)
        assert (floor[:, :, 3] == 255).all()
        page.check("#spiral-visible")
        assert not np.array_equal(floor, canvas(page))
        page.uncheck("#floor-visible")
        ghost = canvas(page)
        assert 0 < ghost[:, :, 3].max() < 255
        assert np.count_nonzero(ghost[:, :, 3]) < ghost.shape[0] * ghost.shape[1] * .08
        page.locator("#view").click(position={"x": 15, "y": 15})
        assert not np.array_equal(ghost, canvas(page))
        page.check("#floor-visible")
        page.click("#reset-spiral")
        page.locator("#opacity").evaluate("e=>{e.value='30';e.dispatchEvent(new Event('input',{bubbles:true}))}")
        assert page.locator("#opacity-value").text_content() == "30 %"
        clean = page.locator("#download").get_attribute("href")
        page.check("#grid")
        assert page.locator("#download").get_attribute("href") == clean
        page.uncheck("#grid")
        for width in [390, 768]:
            page.set_viewport_size({"width": width, "height": 844})
            for tab in ["objets", "parquet", "structure", "modules"]:
                page.click(f'[data-tab="{tab}"]')
                assert page.evaluate("document.documentElement.scrollWidth<=innerWidth"), (width, tab)
        page.set_viewport_size({"width": 390, "height": 844})
        page.screenshot(path=CACHE / "mobile_v2.png", full_page=True)
        html = (KIT / "apercu.html").read_text()
        page.set_content('<iframe id="embed" sandbox="allow-scripts" style="width:100%;height:900px"></iframe>')
        page.locator("#embed").evaluate("(f,s)=>f.srcdoc=s", html)
        frame = page.frame_locator("#embed")
        frame.locator('body[data-ready="true"]').wait_for()
        frame.locator('[data-preset="walls"]').click()
        assert frame.locator('#layers input:checked').count() == 2
        assert not errors, errors
        browser.close()
    report = {"architecture_version": 2, "calques_par_module": 13, "comparaisons_modules": comparisons,
              "comparaisons_plans_isoles": isolates, "renders_controles_pixel_exacts": comparisons + isolates,
              "murs_sol_immersion_independants": True, "objets_selectionnables": 20,
              "spirales_independantes_et_deplacables": True, "PNG_sans_grille": True, "hors_ligne": True,
              "mobile_390px_768px": "sans débordement", "iframe_allow_scripts": True, "erreurs_js": errors}
    (KIT / "controle_navigateur.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    check()
