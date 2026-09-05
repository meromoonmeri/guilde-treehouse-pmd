"""Contrôle du premier module généré traité selon le flux d'origine (grille 8 px)."""
from pathlib import Path
import base64
import hashlib
import io
import json
import os
import struct
import zlib
import numpy as np
from PIL import Image
from scipy.ndimage import label

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "tilesheets/generes/galerie_est_ouest"


def im(path):
    return Image.open(path).convert("RGBA")


def equal(a, b, what):
    assert a.size == b.size and np.array_equal(np.array(a), np.array(b)), what


def check_files():
    m = json.loads((OUT / "kit.json").read_text())
    w, h = m["dimensions"]
    assert (w, h) == (648, 432) and m["grille"] == 8
    assert hashlib.sha256((ROOT / m["source_brute"]).read_bytes()).hexdigest() == m["sha256_source"]
    native = Image.open(ROOT / m["natif"])
    assert native.mode == "P" and len(np.unique(np.array(native))) == 256
    source = np.array(native.convert("RGBA"))
    key = (source[:, :, :3] == [255, 0, 255]).all(axis=2)
    source[key] = 0
    masks = np.array(Image.open(ROOT / "source/hallways/generations/masques/galerie_est_ouest.png"))
    assert np.array_equal(masks > 0, ~key)
    floor_labels, count = label(masks == 1)
    assert count == 1 and floor_labels[275, 8] == floor_labels[275, 639] != 0
    report = {"methode": "génération puis post-traitement", "grille": 8, "natif_indexe": True,
              "calques": 11, "calques_non_vides": 5, "modes": {}, "source_generee_intacte": True}
    silhouettes = []
    for mode, files in m["fichiers"].items():
        target = im(OUT / files["base"])
        layers = [im(OUT / file) for file in files["calques"]]
        assert len(layers) == 11 and sum(bool(q.getbbox()) for q in layers) == 5
        combined = Image.new("RGBA", (w, h))
        for q in layers:
            assert q.size == (w, h)
            combined.alpha_composite(q)
        equal(combined, target, "Recomposition PNG")
        alpha = np.array(target)[:, :, 3] > 0
        silhouettes.append(alpha)
        assert np.array_equal(alpha, ~key)
        chroma = np.array(im(OUT / files["magenta"]))
        assert (chroma[key, :3] == [255, 0, 255]).all()
        if mode == "jour":
            assert np.array_equal(source, np.array(target)), "L'export ne doit pas modifier le rendu du natif"
        raw = (OUT / files["aseprite"]).read_bytes()
        size, magic, frames, ww, hh, depth = struct.unpack_from("<IHHHHH", raw)
        assert (size, magic, frames, ww, hh, depth) == (len(raw), 0xA5E0, 1, w, h, 32)
        assert struct.unpack_from("<hhHH", raw, 36) == (0, 0, 8, 8)
        fs, fm, chunks = struct.unpack_from("<IHH", raw, 128)
        assert fm == 0xF1FA and fs + 128 == len(raw)
        pos, n_layers, cels = 144, 0, {}
        for _ in range(chunks):
            size, kind = struct.unpack_from("<IH", raw, pos)
            p = raw[pos + 6:pos + size]
            if kind == 0x2004:
                n_layers += 1
            if kind == 0x2005:
                idx, x, y, opacity, typ = struct.unpack_from("<HhhBH", p)
                assert typ == 2 and opacity == 255
                cw, ch = struct.unpack_from("<HH", p, 16)
                cels[idx] = (x, y, Image.frombytes("RGBA", (cw, ch), zlib.decompress(p[20:])))
            pos += size
        assert pos == len(raw) and n_layers == len(cels) == 11
        combined = Image.new("RGBA", (w, h))
        for _, (x, y, cel) in sorted(cels.items()):
            combined.alpha_composite(cel, (x, y))
        equal(combined, target, "Recomposition Aseprite")
        tm = json.loads((OUT / files["tiled"]).read_text())
        assert tm["tilewidth"] == tm["tileheight"] == 8 and len(tm["layers"]) == 11
        combined = Image.new("RGBA", (w, h))
        cols, rows = w // 8, h // 8
        for layer, tileset in zip(tm["layers"], tm["tilesets"]):
            a = np.array(im((OUT / tileset["image"]).resolve()))
            cells = a.reshape(rows, 8, cols, 8, 4).transpose(0, 2, 1, 3, 4).reshape(-1, 8, 8, 4)
            ids = np.array(layer["data"])
            restored = np.zeros_like(cells)
            use = ids > 0
            restored[use] = cells[ids[use] - tileset["firstgid"]]
            a = restored.reshape(rows, cols, 8, 8, 4).transpose(0, 2, 1, 3, 4).reshape(h, w, 4)
            combined.alpha_composite(Image.fromarray(a))
        equal(combined, target, "Recomposition Tiled")
        report["modes"][mode] = {"PNG_Aseprite_Tiled": "identiques", "frames": 1, "magenta_exact": True}
    assert np.array_equal(*silhouettes)
    report["limite"] = "Formats relus par code, pas dans l'interface Aseprite/Tiled. Un seul des neuf modules a été traité."
    (OUT / "controle_qualite.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("PASS : natif généré et composition identiques ; 11 calques / 5 utiles ; PNG, Aseprite et Tiled 8 px cohérents en jour/nuit.")


def check_browser():
    from playwright.sync_api import sync_playwright
    errors, comparisons = [], 0
    options = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage"]}
    if os.environ.get("PMD_CHROMIUM"):
        options["executable_path"] = os.environ["PMD_CHROMIUM"]
    m = json.loads((OUT / "kit.json").read_text())
    with sync_playwright() as p:
        browser = p.chromium.launch(**options)
        context = browser.new_context(offline=True, viewport={"width": 1360, "height": 1000})
        page = context.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto((OUT / "apercu.html").as_uri())
        page.wait_for_selector('body[data-ready="true"]')
        for mode in ["jour", "nuit"]:
            page.click(f'[data-mode="{mode}"]')
            for preset in ["all", "1", "2", "6", "10"]:
                page.click(f'[data-preset="{preset}"]')
                url = page.locator("#canvas").evaluate("c=>c.toDataURL()")
                actual = Image.open(io.BytesIO(base64.b64decode(url.split(",")[1]))).convert("RGBA")
                path = m["fichiers"][mode]["base"] if preset == "all" else m["fichiers"][mode]["calques"][int(preset)]
                equal(actual, im(OUT / path), "Aperçu navigateur")
                comparisons += 1
        page.click('[data-mode="jour"]')
        page.click('[data-preset="all"]')
        screenshot = ROOT / ".cache/methode_origine/apercu_pilote.png"
        screenshot.parent.mkdir(exist_ok=True, parents=True)
        page.screenshot(path=screenshot, full_page=True)
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        html = (OUT / "apercu.html").read_text()
        page.set_content('<iframe id="f" sandbox="allow-scripts"></iframe>')
        page.locator("#f").evaluate("(f,html)=>f.srcdoc=html", html)
        frame = page.frame_locator("#f")
        frame.locator('body[data-ready="true"]').wait_for()
        frame.locator('[data-preset="2"]').click()
        assert not errors
        browser.close()
    report = {"comparaisons_pixel_exactes": comparisons, "hors_ligne": True, "mobile_390px": True,
              "iframe_allow_scripts": True, "erreurs_js": errors}
    (OUT / "controle_navigateur.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("PASS navigateur :", report)


if __name__ == "__main__":
    import sys
    check_files()
    if "--navigateur" in sys.argv:
        check_browser()
