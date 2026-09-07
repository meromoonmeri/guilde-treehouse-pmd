# -*- coding: utf-8 -*-
"""Définition des animations Terapagos, grammaire PMD Sprite Collab.

Chaque animation = liste de frames ; chaque frame = dict de paramètres passés
à modele.terapagos(). Les durées sont en ticks PMD (1 tick = 1/60 s), comme
dans AnimData.xml. Les noms d'animations sont ceux de SpriteCollab.
"""
import math

M = math


def _c(n, i):
    return i / max(n, 1)


def idle():
    d = []
    n = 8
    for i in range(n):
        d.append(dict(phase=_c(n, i), duree=8,
                      clign=1.0 if i == 5 else 0.0))
    return d


def marche():
    d = []
    n = 8
    for i in range(n):
        p = _c(n, i)
        d.append(dict(phase=p, pas=p, saut=0.6 * abs(M.sin(p * 2 * M.pi)),
                      duree=5))
    return d


def course():
    d = []
    n = 8
    for i in range(n):
        p = _c(n, i)
        d.append(dict(phase=p, pas=p,
                      saut=1.6 * abs(M.sin(p * 2 * M.pi)),
                      incl=1.0 * M.sin(p * 2 * M.pi),
                      ecrase=0.25 * max(0, -M.sin(p * 2 * M.pi)),
                      expr="determination", duree=3))
    return d


def attaque():
    return [
        dict(phase=0.0, ecrase=0.55, incl=-2, expr="colere", duree=4),
        dict(phase=0.1, ecrase=0.65, incl=-3, expr="colere", duree=4),
        dict(phase=0.3, ecrase=0.0, incl=3, saut=2, expr="colere", duree=2),
        dict(phase=0.5, ecrase=0.30, incl=4, saut=0, expr="colere", duree=3),
        dict(phase=0.7, ecrase=0.10, incl=2, expr="determination", duree=4),
        dict(phase=0.9, ecrase=0.0, incl=0, expr="neutre", duree=6),
    ]


def tir():
    return [
        dict(phase=0.0, ecrase=0.35, incl=-2, expr="determination", duree=5),
        dict(phase=0.2, ecrase=0.50, incl=-3, expr="colere", duree=5),
        dict(phase=0.4, ecrase=0.0, incl=2, expr="surprise", duree=3),
        dict(phase=0.6, ecrase=0.15, incl=1, expr="determination", duree=4),
        dict(phase=0.8, ecrase=0.0, incl=0, expr="neutre", duree=6),
    ]


def coup_special():
    """Rotation du dôme : anticipation longue, éclat, retour."""
    return [
        dict(phase=0.0, ecrase=0.4, retrait=0.3, expr="determination", duree=6),
        dict(phase=0.2, ecrase=0.6, retrait=0.6, expr="colere", duree=6),
        dict(phase=0.4, ecrase=0.0, saut=3, retrait=0.2, expr="colere", duree=3),
        dict(phase=0.6, ecrase=0.0, saut=4, ech=1.06, expr="colere", duree=3),
        dict(phase=0.8, ecrase=0.3, saut=0, expr="determination", duree=5),
        dict(phase=0.9, ecrase=0.0, expr="neutre", duree=6),
    ]


def degats():
    return [
        dict(phase=0.0, incl=-3, ecrase=0.3, expr="peur", duree=4),
        dict(phase=0.2, incl=-4, ecrase=0.1, expr="peur", retrait=0.4, duree=5),
        dict(phase=0.5, incl=-2, expr="triste", retrait=0.2, duree=5),
        dict(phase=0.8, incl=0, expr="neutre", duree=6),
    ]


def ko():
    return [
        dict(phase=0.0, ecrase=0.4, retrait=0.7, expr="ko", duree=6),
        dict(phase=0.3, ecrase=0.6, retrait=0.9, expr="ko", saut=-1, duree=8),
        dict(phase=0.6, ecrase=0.7, retrait=1.0, expr="ko", saut=-2, duree=60),
    ]


def dodo():
    d = []
    n = 6
    for i in range(n):
        p = _c(n, i)
        d.append(dict(phase=p, expr="dodo", retrait=0.45 + 0.15 * M.sin(p * 2 * M.pi),
                      ecrase=0.25, duree=14))
    return d


def reveil():
    return [
        dict(phase=0.0, expr="dodo", retrait=0.6, ecrase=0.3, duree=10),
        dict(phase=0.3, expr="surprise", retrait=0.2, duree=6),
        dict(phase=0.6, expr="surprise", retrait=0.0, saut=1, duree=6),
        dict(phase=0.9, expr="neutre", duree=8),
    ]


def confusion():
    d = []
    n = 6
    for i in range(n):
        p = _c(n, i)
        d.append(dict(phase=p, incl=2.2 * M.sin(p * 2 * M.pi),
                      expr="surprise", clign=0.5 * (i % 2), duree=8))
    return d


def peur():
    d = []
    n = 4
    for i in range(n):
        d.append(dict(phase=_c(n, i), incl=(1 if i % 2 else -1),
                      expr="peur", retrait=0.35, ecrase=0.2, duree=4))
    return d


def colere():
    return [
        dict(phase=0.0, expr="colere", ecrase=0.3, duree=6),
        dict(phase=0.3, expr="colere", saut=2, ech=1.04, duree=5),
        dict(phase=0.6, expr="colere", ecrase=0.35, duree=5),
        dict(phase=0.9, expr="colere", duree=8),
    ]


def joie():
    d = []
    n = 6
    for i in range(n):
        p = _c(n, i)
        d.append(dict(phase=p, saut=max(0, 3.2 * M.sin(p * 2 * M.pi)),
                      ecrase=0.35 * max(0, -M.sin(p * 2 * M.pi)),
                      expr="joie", duree=5))
    return d


def tristesse():
    d = []
    n = 4
    for i in range(n):
        p = _c(n, i)
        d.append(dict(phase=p, expr="triste", retrait=0.25,
                      ecrase=0.2 + 0.05 * M.sin(p * 2 * M.pi), duree=12))
    return d


def surprise():
    return [
        dict(phase=0.0, expr="surprise", ecrase=0.4, duree=3),
        dict(phase=0.2, expr="surprise", saut=3, ech=1.05, duree=4),
        dict(phase=0.5, expr="surprise", saut=1, duree=5),
        dict(phase=0.8, expr="surprise", duree=10),
    ]


def determination():
    d = []
    n = 4
    for i in range(n):
        p = _c(n, i)
        d.append(dict(phase=p, expr="determination",
                      ecrase=0.12 * abs(M.sin(p * 2 * M.pi)), duree=9))
    return d


def pose():
    return [dict(phase=0.0, expr="neutre", duree=1)]


def frappe_sol():
    return [
        dict(phase=0.0, saut=4, ecrase=0.0, expr="determination", duree=4),
        dict(phase=0.2, saut=6, ecrase=0.0, expr="colere", duree=3),
        dict(phase=0.4, saut=0, ecrase=0.6, expr="colere", duree=4),
        dict(phase=0.7, saut=0, ecrase=0.2, expr="neutre", duree=5),
    ]


def charge():
    d = []
    n = 6
    for i in range(n):
        p = _c(n, i)
        d.append(dict(phase=p, ecrase=0.35, retrait=0.25,
                      ech=1.0 + 0.03 * M.sin(p * 2 * M.pi),
                      expr="determination", duree=6))
    return d


def rotation():
    """Withdraw / rentre dans la carapace puis ressort."""
    return [
        dict(phase=0.0, retrait=0.2, ecrase=0.25, duree=5),
        dict(phase=0.2, retrait=0.6, ecrase=0.45, duree=5),
        dict(phase=0.4, retrait=1.0, ecrase=0.6, duree=8),
        dict(phase=0.7, retrait=0.5, ecrase=0.3, expr="surprise", duree=5),
        dict(phase=0.9, retrait=0.0, expr="neutre", duree=6),
    ]


def saut():
    return [
        dict(phase=0.0, ecrase=0.55, duree=4),
        dict(phase=0.2, saut=4, ech=1.03, expr="determination", duree=4),
        dict(phase=0.4, saut=7, expr="surprise", duree=5),
        dict(phase=0.6, saut=4, duree=4),
        dict(phase=0.8, saut=0, ecrase=0.5, duree=4),
        dict(phase=0.9, ecrase=0.0, duree=5),
    ]


# ---------------------------------------------------------------------------
# Table des animations. « dirs » indique si l'anim est rendue sur 8 directions
# (règle SpriteCollab : les anims de déplacement/combat le sont ; certaines
# émotions restent sur 8 directions aussi pour rester utilisables partout).
ANIMS = [
    ("Idle",          idle,          8, "Repos, respiration lente + clignement"),
    ("Walk",          marche,        8, "Marche, cycle 8 frames"),
    ("Run",           course,        8, "Course, cycle rapide penché"),
    ("Attack",        attaque,       8, "Attaque physique, coup de carapace"),
    ("Shoot",         tir,           8, "Attaque à distance"),
    ("Special",       coup_special,  8, "Attaque spéciale, dôme illuminé"),
    ("Strike",        frappe_sol,    8, "Impact au sol"),
    ("Charge",        charge,        8, "Concentration / charge"),
    ("Withdraw",      rotation,      8, "Rentre dans la carapace"),
    ("Jump",          saut,          8, "Saut"),
    ("Hurt",          degats,        8, "Dégâts subis"),
    ("Faint",         ko,            8, "KO"),
    ("Sleep",         dodo,          1, "Sommeil"),
    ("Wake",          reveil,        1, "Réveil"),
    ("Dizzy",         confusion,     1, "Confusion"),
    ("Fear",          peur,          1, "Peur"),
    ("Rage",          colere,        1, "Colère"),
    ("Joyous",        joie,          1, "Joie"),
    ("Sad",           tristesse,     1, "Tristesse"),
    ("Shock",         surprise,      1, "Surprise"),
    ("Pose",          pose,          1, "Pose neutre de référence"),
    ("Determination", determination, 1, "Détermination"),
]
