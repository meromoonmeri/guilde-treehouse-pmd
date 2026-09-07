"""Les 9 lignées de starters gen 1-3 et l'attribution des palettes."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline as P, foulard as F

LIGNEES = [
    {"cle": "bulbizarre", "type": "Plante",
     "membres": [("0001","Bulbasaur","Bulbizarre"),("0002","Ivysaur","Herbizarre"),("0003","Venusaur","Florizarre")]},
    {"cle": "salameche", "type": "Feu",
     "membres": [("0004","Charmander","Salamèche"),("0005","Charmeleon","Reptincel"),("0006","Charizard","Dracaufeu")]},
    {"cle": "carapuce", "type": "Eau",
     "membres": [("0007","Squirtle","Carapuce"),("0008","Wartortle","Carabaffe"),("0009","Blastoise","Tortank")]},
    {"cle": "germignon", "type": "Plante",
     "membres": [("0152","Chikorita","Germignon"),("0153","Bayleef","Macronium"),("0154","Meganium","Méganium")]},
    {"cle": "hericendre", "type": "Feu",
     "membres": [("0155","Cyndaquil","Héricendre"),("0156","Quilava","Feurisson"),("0157","Typhlosion","Typhlosion")]},
    {"cle": "kaiminus", "type": "Eau",
     "membres": [("0158","Totodile","Kaiminus"),("0159","Croconaw","Crocrodil"),("0160","Feraligatr","Aligatueur")]},
    {"cle": "arcko", "type": "Plante",
     "membres": [("0252","Treecko","Arcko"),("0253","Grovyle","Massko"),("0254","Sceptile","Jungko")]},
    {"cle": "poussifeu", "type": "Feu",
     "membres": [("0255","Torchic","Poussifeu"),("0256","Combusken","Galifeu"),("0257","Blaziken","Braségali")]},
    {"cle": "gobou", "type": "Eau",
     "membres": [("0258","Mudkip","Gobou"),("0259","Marshtomp","Flobio"),("0260","Swampert","Laggron")]},
    # Terapagos (gen 9). Deux formes présentes dans SpriteCollab : Normale et
    # Terastal. La forme Stellaire n'y a pas encore de sprites.
    {"cle": "terapagos", "type": "Normal",
     "membres": [("1024","Terapagos","Terapagos"),
                 ("1024/0001","Terapagos Terastal Form","Terapagos_Terastal")]},
]

# Choix retenu : une couleur par lignée (le foulard est l'identité du membre
# d'équipe, il ne change pas en évoluant), toutes distinctes, chacune validée
# en contraste sur les trois stades. Mettre FORCE à None pour laisser le
# scoring automatique décider.
FORCE = {
    "terapagos":  "grenat_ancien",
    "bulbizarre": "rouge_explorateur",
    "salameche":  "azur_ciel",
    "carapuce":   "or_guilde",
    "germignon":  "violet_crepuscule",
    "hericendre": "turquoise_lagon",
    "kaiminus":   "orange_braise",
    "arcko":      "rose_aurore",
    "poussifeu":  "indigo_nuit",
    "gobou":      "prune_profonde",
}


def attribuer_palettes():
    if FORCE:
        return dict(FORCE)
    return attribuer_palettes_auto()


def attribuer_palettes_auto():
    """
    Une couleur par lignée (le foulard est l'identité du membre d'équipe :
    il ne change pas en évoluant), toutes distinctes entre lignées.
    Assignation gloutonne sur le meilleur écart teinte/luminance.
    """
    notes = {}
    for lg in LIGNEES:
        cc = []
        for pid, _, _ in lg["membres"]:
            cc += P.couleurs_corps(f"{P.DOS_SPRITE}/{pid}")
        lg["_cc"] = cc
        for nom in F.PALETTES:
            notes[(lg["cle"], nom)] = _note(cc, nom)
    libres = set(F.PALETTES)
    res = {}
    for _ in range(len(LIGNEES)):
        best = max(((lg, n) for lg in LIGNEES if lg["cle"] not in res for n in libres),
                   key=lambda t: notes[(t[0]["cle"], t[1])])
        res[best[0]["cle"]] = best[1]
        libres.discard(best[1])
    return res

def _note(cc, nom):
    import colorsys
    total = sum(p for _, p in cc) or 1.0
    teintes, lum = [], 0.0
    for rgb, p in cc:
        h, s, v = F._rgb_hsv(*rgb)
        lum += F._luminance(rgb) * p / total
        if s > 0.15 and v > 0.12:
            teintes.append((h, s * (p / total)))
    h, s, v = F._rgb_hsv(*F.PALETTES[nom])
    if teintes:
        d = min(min(abs(h-hc), 1-abs(h-hc)) for hc, _ in teintes)
        w = sum(x for _, x in teintes) or 1.0
        dp = sum(min(abs(h-hc), 1-abs(h-hc))*x for hc, x in teintes)/w
    else:
        d = dp = 0.5
    contraste = abs(F._luminance(F.PALETTES[nom]) - lum)
    n = 2.4*min(d,0.28) + 1.5*dp + 1.9*min(contraste,0.45) + F.BONUS_FRANCHISE.get(nom,0.0)
    if d < 0.075: n -= 1.4
    if contraste < 0.10: n -= 0.9
    return n
