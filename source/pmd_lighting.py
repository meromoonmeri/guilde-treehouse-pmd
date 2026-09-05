"""Éclairage local des accès, en pixels natifs.

Les ombres suivent les joues, les linteaux et les pieds d'échelle. Elles ne
sont plus extraites des couleurs sombres du veinage. Pas de lumière globale,
de flou photographique ni de barre traversant un passage.
"""
import numpy as np
from PIL import Image


def access_lighting(base, semantic, passages, mode="jour"):
    """Renvoie deux RGBA indépendants : contacts et reflets de seuil.

    Les dimensions et les masques sont les mêmes le jour et la nuit ; la
    lumière nocturne est moins intense. Les fenêtres ne sont jamais peintes.
    Le modelé ambiant des matériaux reste dans la base artistique approuvée.
    """
    a = np.asarray(base.convert("RGBA"))
    h, w = a.shape[:2]
    floor = semantic == 1
    architecture = np.isin(semantic, [1, 2, 5])
    shade = np.zeros((h, w), dtype=float)
    light = np.zeros((h, w), dtype=float)

    def stroke(target, points, radius, peak, allowed):
        # Distance analytique, évaluée uniquement dans la petite boîte du trait.
        # Les niveaux sont quantifiés à l'export : pas de sous-pixels floutés.
        for (x0, y0), (x1, y1) in zip(points, points[1:]):
            left = max(0, int(min(x0, x1) - radius - 1))
            top = max(0, int(min(y0, y1) - radius - 1))
            right = min(w, int(max(x0, x1) + radius + 2))
            bottom = min(h, int(max(y0, y1) + radius + 2))
            if left >= right or top >= bottom:
                continue
            yy, xx = np.mgrid[top:bottom, left:right]
            dx, dy = x1 - x0, y1 - y0
            t = np.clip(((xx - x0) * dx + (yy - y0) * dy) / max(dx * dx + dy * dy, 1), 0, 1)
            distance = np.hypot(xx - (x0 + t * dx), yy - (y0 + t * dy))
            strength = peak * np.clip(1 - distance / radius, 0, 1) ** 1.4
            strength *= allowed[top:bottom, left:right]
            target[top:bottom, left:right] = np.maximum(target[top:bottom, left:right], strength)

    for p in passages:
        typ = p["type"]
        if typ == "passage_lateral":
            top, bottom = p["sol_bord"]
            west = p["orientation"] == "O"
            root = p["racine"]
            edge = 0 if west else w - 1
            inner = root + 15 if west else root - 15
            # L'ombre longe le mur arrière, PARALLÈLEMENT à la circulation.
            stroke(shade, [(inner, top + 1), (root, top + 2), (edge, top + 2)], 7, 92, floor)
            stroke(shade, [(inner, bottom - 1), (root, bottom - 1), (edge, bottom - 1)], 4, 56, floor)
            # Petit rebond sur le sol côté éclairé ; pas de halo ni de lampe ajoutée.
            stroke(light, [(root, bottom - 5), (edge, bottom - 5)], 1.6, 64 if west else 76, floor)
            stroke(light, [(root, top - 88), (edge, top - 88)], 1.4, 64, architecture)
        elif typ == "passage_sud":
            left, right, top = p["bouche"]
            height = 28 if w > 1000 else 24
            stroke(shade, [(left + 1, top + 2), (left - 2, top + height), (left - 5, top + height + 7)], 7, 100, floor)
            stroke(shade, [(right - 1, top + 2), (right + 2, top + height), (right + 5, top + height + 7)], 6, 72, floor)
            stroke(light, [(left + 8, top + 3), (left + 5, top + height - 1)], 1.8, 72, floor)
            stroke(light, [(right - 8, top + 3), (right - 6, top + height - 2)], 1.5, 40, floor)
        elif typ == "passage_nord":
            # La profondeur du renfoncement fait partie de la retouche locale.
            # Ces traits ne renforcent que les contacts, jamais toute l'ouverture.
            stroke(shade, [(289, 143), (285, 165), (282, 181)], 4.5, 70, floor)
            stroke(shade, [(357, 143), (360, 165), (362, 181)], 4, 45, floor)
            stroke(light, [(278, 111), (280, 99), (287, 89), (305, 84), (331, 83)], 1.3, 58, architecture)
            stroke(light, [(291, 169), (288, 180)], 1.5, 38, floor)
        elif typ == "echelle":
            x, y = p["pied"]
            stroke(shade, [(x - 25, y + 2), (x, y + 4), (x + 24, y + 2)], 6, 80, floor)
            stroke(light, [(x - 27, y + 9), (x - 5, y + 11)], 1.5, 42, floor)
        elif typ == "porte_fermee":
            x, y = p["point_sol"]
            stroke(shade, [(x - 31, y - 10), (x + 32, y - 10)], 5, 68, floor)
            stroke(light, [(x - 30, y - 4), (x + 30, y - 4)], 1.2, 38, floor)

    opaque = a[:, :, 3] > 0
    result = []
    night = mode == "nuit"
    for values, color, multiplier in [
        (shade, (9, 12, 21) if night else (37, 18, 7), 1.05 if night else 1.),
        (light, (131, 144, 178) if night else (251, 204, 116), .28 if night else 1.),
    ]:
        alpha = (np.rint(values * multiplier / 4) * 4).clip(0, 116).astype("uint8")
        alpha[~opaque] = 0
        pixels = np.zeros((h, w, 4), dtype="uint8")
        pixels[:, :, :3] = color
        pixels[:, :, 3] = alpha
        pixels[alpha == 0] = 0
        result.append(Image.fromarray(pixels))
    return tuple(result)
