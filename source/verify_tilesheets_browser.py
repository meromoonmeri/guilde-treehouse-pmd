"""Contrôle de l'atelier de tilesheets, hors ligne, sans serveur requis."""
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


def check():
    manifest = json.loads((KIT / "kit.json").read_text())
    errors, comparisons = [], 0
    launch = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage"]}
    if os.environ.get("PMD_CHROMIUM"):
        launch["executable_path"] = os.environ["PMD_CHROMIUM"]
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch)
        context = browser.new_context(offline=True, viewport={"width": 1440, "height": 1120}, device_scale_factor=1)
        page = context.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto((KIT / "apercu.html").as_uri())
        page.wait_for_selector('body[data-ready="true"]')
        assert np.array_equal(canvas(page), np.array(Image.open(KIT / "objets/objets_jour.png").convert("RGBA")))
        page.screenshot(path=CACHE / "objets.png", full_page=True)
        for i, obj in enumerate(manifest["objets"]):
            page.select_option("#object", str(i))
            for mode in ["jour", "nuit"]:
                page.click(f'[data-mode="{mode}"]')
                assert page.locator("#title").text_content() == obj["nom"]
                assert canvas(page).shape[:2] == tuple(reversed(obj["taille"]))
        page.click('[data-tab="modules"]')
        for i, module in enumerate(manifest["modules"]):
            page.select_option("#module", str(i))
            assert page.locator("#exits span").count() == len(module["acces"])
            for mode in ["jour", "nuit"]:
                page.click(f'[data-mode="{mode}"]')
                expected = np.array(Image.open(KIT / module["fichiers"][mode]["png"]).convert("RGBA"))
                assert np.array_equal(canvas(page), expected), (module["id"], mode)
                comparisons += 1
        # Les objets/spirales des paliers sont réellement retirables.
        page.select_option("#module", "6")
        page.click('[data-mode="jour"]')
        full = canvas(page)
        for index in [2, 3, 5]:
            box = page.locator(f'input[data-layer="{index}"]')
            box.uncheck()
            assert not np.array_equal(canvas(page), full), ("calque inactif", index)
            box.check()
            assert np.array_equal(canvas(page), full)
        page.screenshot(path=CACHE / "palier.png", full_page=True)
        page.click('[data-tab="structure"]')
        for sheet in ["structure", "contacts"]:
            page.select_option("#architecture", sheet)
            assert page.locator("#view").evaluate("c=>c.width") in [128, 256]
        page.click('[data-tab="parquet"]')
        page.uncheck("#spiral-visible")
        floor = canvas(page)
        assert (floor[:, :, 3] == 255).all()
        page.check("#spiral-visible")
        with_spiral = canvas(page)
        assert not np.array_equal(floor, with_spiral)
        page.uncheck("#floor-visible")
        ghost = canvas(page)
        assert 0 < ghost[:, :, 3].max() < 255
        assert np.count_nonzero(ghost[:, :, 3]) < ghost.shape[0] * ghost.shape[1] * .08
        page.locator("#view").click(position={"x": 15, "y": 15})
        assert not np.array_equal(ghost, canvas(page)), "Le motif ne se déplace pas"
        page.check("#floor-visible")
        page.click("#reset-spiral")
        page.locator("#opacity").evaluate("e=>{e.value='30';e.dispatchEvent(new Event('input',{bubbles:true}))}")
        assert page.locator("#opacity-value").text_content() == "30 %"
        page.select_option("#grain", "v")
        page.screenshot(path=CACHE / "spirales.png", full_page=True)
        # La grille est un guide d'affichage, elle n'entre pas dans le PNG téléchargé.
        clean = page.locator("#download").get_attribute("href")
        page.check("#grid")
        assert page.locator("#download").get_attribute("href") == clean
        assert "data:image/png;base64," in clean
        page.uncheck("#grid")
        for width in [390, 768]:
            page.set_viewport_size({"width": width, "height": 844})
            for tab in ["objets", "parquet", "structure", "modules"]:
                page.click(f'[data-tab="{tab}"]')
                assert page.evaluate("document.documentElement.scrollWidth<=innerWidth"), (width, tab)
        page.set_viewport_size({"width": 390, "height": 844})
        page.screenshot(path=CACHE / "mobile.png", full_page=True)
        # Même contexte d'isolation que l'afficheur de fichiers Arena.
        html = (KIT / "apercu.html").read_text()
        page.set_content('<iframe id="embed" sandbox="allow-scripts" style="width:100%;height:900px"></iframe>')
        page.locator("#embed").evaluate("(f,s)=>f.srcdoc=s", html)
        frame = page.frame_locator("#embed")
        frame.locator('body[data-ready="true"]').wait_for()
        frame.locator('[data-tab="parquet"]').click()
        frame.locator("#spiral").select_option("12")
        frame.locator("#floor-visible").uncheck()
        assert not errors, errors
        browser.close()
    report = {"comparaisons_modules": comparisons, "rendu_modules_identique_aux_PNG": True,
              "objets_selectionnables": 20, "spirales_independantes_et_deplacables": True,
              "calques_modules_activables": True, "PNG_sans_grille": True, "hors_ligne": True,
              "mobile_390px_768px": "sans débordement", "iframe_allow_scripts": True, "erreurs_js": errors}
    (KIT / "controle_navigateur.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    check()
