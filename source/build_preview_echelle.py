# -*- coding: utf-8 -*-
"""
Apercu autonome du kit reduit a l'echelle PMDO/Halcyon : les douze salles,
jour et nuit, VIDES (calques 06/07/09 transparents, aucun mobilier pose).

Incorpore en base64 :
  - salles_reduites/<dossier>_<palette>.png        (composite des calques 01..10)
  - calques_reduits/<dossier>/<palette>/00_exterieur.png (paysage des fenetres)

Sortie : apercu_echelle_pmdo.html (hors ligne, aucun dependance externe).
"""
import base64
import io
import json
import os

from PIL import Image

D = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(D)
OUT = os.path.join(REPO, 'apercu_echelle_pmdo.html')


def b64(path):
    if not os.path.exists(path):
        return None
    return base64.b64encode(open(path, 'rb').read()).decode('ascii')


def datauri(path):
    b = b64(path)
    return 'data:image/png;base64,' + b if b else None


def cases_label(cible):
    w = cible['toile_ajustee_cases'][0]
    h = cible['toile_ajustee_cases'][1]
    fw = int(w) if abs(w - round(w)) < 1e-6 else round(w, 1)
    fh = int(h) if abs(h - round(h)) < 1e-6 else round(h, 1)
    return '%s × %s cases' % (fw, fh)


def fig(salle, cible):
    W, H = cible['toile_ajustee_px']
    aw, ah = cible['toile_actuelle_px']
    imgs = {'jour': {}, 'nuit': {}}
    for pal in ('jour', 'nuit'):
        imgs[pal]['base'] = datauri(os.path.join(
            REPO, 'salles_reduites', '%s_%s.png' % (salle['dossier'], pal)))
        imgs[pal]['ext'] = datauri(os.path.join(
            REPO, 'calques_reduits', salle['dossier'], pal, '00_exterieur.png'))
        imgs[pal]['imm'] = datauri(os.path.join(
            REPO, 'calques_reduits', salle['dossier'], pal,
            '11_immersion_feuilles.png'))
    # verification de contenu : dimensions reelles des composites
    ref = Image.open(os.path.join(
        REPO, 'salles_reduites', '%s_jour.png' % salle['dossier']))
    assert (ref.width, ref.height) == (W, H), (salle['id'], ref.size, (W, H))

    couches = []
    alt_txt = {'ext': u'paysage des fenêtres', 'base': u'salle vide',
               'imm': u'cadre de feuillage'}
    for pal in ('jour', 'nuit'):
        for kind in ('ext', 'base', 'imm'):
            uri = imgs[pal][kind]
            if uri:
                couches.append(
                    u'<img class="lyr %s %s" alt="%s — %s, %s" src="%s">'
                    % (kind, pal, salle['nom'], alt_txt[kind], pal, uri))

    svg_ref = (
        '<svg viewBox="0 0 24 24" aria-hidden="true">'
        '<rect x="0.5" y="0.5" width="23" height="23" fill="none" '
        'stroke="#7fe0ff" stroke-width="1" stroke-dasharray="3 2" opacity=".9"/>'
        '<circle cx="12" cy="8.5" r="5.2" fill="rgba(127,224,255,.30)" '
        'stroke="rgba(127,224,255,.75)" stroke-width=".8"/>'
        '<ellipse cx="12" cy="16.5" rx="7.6" ry="5.6" fill="rgba(127,224,255,.30)" '
        'stroke="rgba(127,224,255,.75)" stroke-width=".8"/>'
        '</svg>')

    return u'''
<figure class="room">
  <figcaption>
    <span class="rid">%s</span>
    <span class="rnom">%s</span>
    <span class="rdims">%d × %d px <span class="avant">(&#160;avant %d × %d&#160;)</span></span>
    <span class="rcases">%s</span>
  </figcaption>
  <div class="stage" style="--w:%dpx;--h:%dpx">
    %s
    <div class="ov g24"></div>
    <div class="ov g8"></div>
    <div class="ov ref">%s</div>
  </div>
</figure>''' % (
        salle['id'], salle['nom'], W, H, aw, ah, cases_label(cible), W, H,
        '\n    '.join(couches), svg_ref)


HTML = u'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Guilde Treehouse — kit à l&#8217;échelle PMDO (salles vides)</title>
<style>
  :root { --z: 1; }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: #100e18; color: #e8e2f2;
    font: 14px/1.45 "Segoe UI", system-ui, sans-serif;
  }
  header {
    position: sticky; top: 0; z-index: 10;
    background: rgba(16, 14, 24, .94); backdrop-filter: blur(4px);
    border-bottom: 1px solid #2c2740; padding: 10px 16px;
    display: flex; flex-wrap: wrap; gap: 10px 18px; align-items: center;
  }
  header h1 { font-size: 15px; margin: 0; font-weight: 600; }
  header h1 small { color: #9d93b8; font-weight: 400; }
  .controles { display: flex; flex-wrap: wrap; gap: 8px 14px; align-items: center; }
  .seg { display: inline-flex; border: 1px solid #3a3355; border-radius: 6px; overflow: hidden; }
  .seg button {
    background: #1b1728; color: #cfc6e4; border: 0; padding: 5px 12px;
    cursor: pointer; font: inherit;
  }
  .seg button.on { background: #4c3f78; color: #fff; }
  label.chk { display: inline-flex; gap: 6px; align-items: center; cursor: pointer; color: #cfc6e4; }
  main { padding: 18px 16px 40px; display: grid; gap: 26px; }
  .room { margin: 0; max-width: 100%; overflow-x: auto; }
  figcaption {
    display: flex; flex-wrap: wrap; gap: 4px 10px; align-items: baseline;
    margin: 0 0 6px;
  }
  .rid {
    background: #4c3f78; color: #fff; border-radius: 4px; padding: 1px 7px;
    font-weight: 600; font-size: 12px;
  }
  .rnom { font-weight: 600; }
  .rdims { color: #b7aed1; font-size: 12.5px; }
  .rdims .avant { color: #7d7399; }
  .rcases { color: #7fe0ff; font-size: 12.5px; }
  .stage {
    position: relative; width: calc(var(--w) * var(--z)); height: calc(var(--h) * var(--z));
    background: #000;
    border: 1px solid #2c2740; border-radius: 4px;
  }
  body.damier .stage {
    background:
      repeating-conic-gradient(#171420 0% 25%, #1c1928 0% 50%) 0 0 / 16px 16px;
  }
  .lyr { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
  .ov { position: absolute; inset: 0; pointer-events: none; }
  .g24, .g8 { opacity: 0; }
  .g24 {
    background-image:
      linear-gradient(to right, rgba(127, 224, 255, .22) 1px, transparent 1px),
      linear-gradient(to bottom, rgba(127, 224, 255, .22) 1px, transparent 1px);
    background-size: calc(24px * var(--z)) calc(24px * var(--z));
  }
  .g8 {
    background-image:
      linear-gradient(to right, rgba(255, 255, 255, .07) 1px, transparent 1px),
      linear-gradient(to bottom, rgba(255, 255, 255, .07) 1px, transparent 1px);
    background-size: calc(8px * var(--z)) calc(8px * var(--z));
  }
  .ref { display: none; align-items: center; justify-content: center; }
  .ref svg { width: calc(24px * var(--z)); height: calc(24px * var(--z)); }
  body.g24 .g24 { opacity: 1; }
  body.g8 .g8 { opacity: 1; }
  body:not(.paysage) .ext { visibility: hidden; }
  body:not(.imm) .imm { display: none; }
  body:not(.nuit) .nuit { display: none; }
  body.nuit .jour { display: none; }
  body.ref .ref { display: flex; }
  body.zoom { --z: 2; }
  body.zoom .lyr { image-rendering: pixelated; }
  footer {
    border-top: 1px solid #2c2740; color: #8f86ab; padding: 14px 16px 30px;
    font-size: 12.5px; max-width: 900px;
  }
  footer p { margin: 4px 0; }
</style>
</head>
<body>
<header>
  <h1>Guilde Treehouse <small>— kit à l&#8217;échelle PMDO / Halcyon, salles vides</small></h1>
  <div class="controles">
    <span class="seg" id="seg-palette">
      <button data-pal="jour" class="on">Jour</button><button data-pal="nuit">Nuit</button>
    </span>
    <label class="chk"><input type="checkbox" id="chk-paysage"> Paysage des fenêtres</label>
    <label class="chk"><input type="checkbox" id="chk-imm" checked> Immersion feuilles</label>
    <label class="chk"><input type="checkbox" id="chk-damier"> Damier (transparence)</label>
    <label class="chk"><input type="checkbox" id="chk-g24" checked> Grille 24 px</label>
    <label class="chk"><input type="checkbox" id="chk-g8"> Grille 8 px</label>
    <label class="chk"><input type="checkbox" id="chk-ref"> Repère sprite</label>
    <label class="chk"><input type="checkbox" id="chk-zoom"> Zoom ×2</label>
  </div>
</header>
<main>
%%SALLES%%
</main>
<footer>
  <p><strong>Salles vides.</strong> Aucun mobilier, tapis, plante, bannière ou lampe n&#8217;est
  posé : les calques <em>décorations</em>, <em>objets</em> et <em>éclairage</em> restent
  transparents. Le banc de props à l&#8217;échelle PMD est fourni séparément dans
  <code>sprites_reduits/</code>.</p>
  <p><strong>Cadre d&#8217;immersion.</strong> Le calque <code>11_immersion_feuilles</code>
  entoure l&#8217;extrémité des bordures de bois d&#8217;un feuillage olive (palette du kit)
  fondu dans une bande noire au ras du canvas : posé sur un fond noir, la pièce semble
  flotter dans le noir, sans couture. Les passages et les fenêtres restent totalement
  dégagés. Le fond de cet aperçu est noir pour montrer ce fondu ; activez le damier
  pour contrôler la transparence.</p>
  <p>Chaque image est le composite des calques 01 à 10 à l&#8217;échelle cible
  (le paysage des fenêtres, calque 00, est indépendant). Références PMDO/Halcyon :
  case de 24 px, sprite de starter ≈ 20 × 22 px, viewport 320 × 240 px.
  Rééchantillonnage ×0,65 depuis le kit plein format — les contours restent à
  reprendre à la main si besoin.</p>
  <p>Fichiers : <code>salles_reduites/</code> (composites), <code>calques_reduits/</code>
  (11 calques par salle et par palette), <code>analyse_echelle/cibles.json</code>
  (dimensions cibles). Régénération : <code>python3 analyse_echelle/reduire.py</code>.</p>
</footer>
<script>
(function () {
  var body = document.body;
  function seg(id, cls) {
    var box = document.getElementById(id);
    box.addEventListener('click', function (e) {
      var b = e.target.closest('button');
      if (!b) return;
      box.querySelectorAll('button').forEach(function (x) { x.classList.remove('on'); });
      b.classList.add('on');
      body.classList.toggle(cls, b.dataset.pal === 'nuit');
    });
  }
  function chk(id, cls) {
    var c = document.getElementById(id);
    body.classList.toggle(cls, c.checked);
    c.addEventListener('change', function () { body.classList.toggle(cls, c.checked); });
  }
  seg('seg-palette', 'nuit');
  chk('chk-paysage', 'paysage');
  chk('chk-imm', 'imm');
  chk('chk-damier', 'damier');
  chk('chk-g24', 'g24');
  chk('chk-g8', 'g8');
  chk('chk-ref', 'ref');
  chk('chk-zoom', 'zoom');
})();
</script>
</body>
</html>
'''


def main():
    kit = json.load(io.open(os.path.join(REPO, 'kit.json'), encoding='utf-8'))
    cibles = {c['id']: c for c in json.load(io.open(
        os.path.join(REPO, 'analyse_echelle', 'cibles.json'),
        encoding='utf-8'))['salles']}
    figs = [fig(s, cibles[s['id']]) for s in kit['salles']]
    html = HTML.replace('%%SALLES%%', '\n'.join(figs))
    with io.open(OUT, 'w', encoding='utf-8') as f:
        f.write(html)
    print('OK ->', os.path.relpath(OUT, REPO),
          '(%.1f Mo, %d salles)' % (os.path.getsize(OUT) / 1e6, len(figs)))


if __name__ == '__main__':
    main()
