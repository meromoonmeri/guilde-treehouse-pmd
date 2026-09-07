"""
sons.py — synthèse procédurale des effets sonores de la zone de boss.

Tout est calculé au signal, sans échantillon extérieur : sinusoïdes
inharmoniques pour le cristal, balayages de fréquence pour la montée en
puissance, bruit filtré pour la foudre. Sortie en WAV PCM 16 bits, 44,1 kHz,
stéréo, avec fondus de bouclage pour les nappes.
"""

import math
import wave
import numpy as np

SR = 44100


# --------------------------------------------------------------------------
# Briques élémentaires
# --------------------------------------------------------------------------

def t(duree):
    return np.linspace(0.0, duree, int(SR * duree), endpoint=False)


def env_ad(n, attaque, chute, courbe=2.0):
    """Enveloppe attaque / décroissance, en nombre d'échantillons."""
    a = max(1, int(n * attaque))
    e = np.empty(n)
    e[:a] = np.linspace(0.0, 1.0, a) ** 0.6
    reste = n - a
    e[a:] = np.exp(-np.linspace(0.0, courbe * 6.0, reste)) if chute else 1.0
    return e


def cristal(freq, duree, partiels=7, brillance=1.0, amp=0.25):
    """
    Timbre de cristal : partiels inharmoniques légèrement désaccordés, chacun
    avec sa propre décroissance — les aigus s'éteignent plus vite.
    """
    x = t(duree)
    n = len(x)
    s = np.zeros(n)
    for k in range(1, partiels + 1):
        ratio = k * (1.0 + 0.013 * k * k)          # inharmonicité
        f = freq * ratio
        if f > SR / 2.2:
            break
        a = amp / (k ** 1.35) * (brillance ** (k - 1))
        dec = np.exp(-np.linspace(0.0, 3.0 + 1.6 * k, n))
        vib = 1.0 + 0.0015 * np.sin(2 * np.pi * (4.0 + k) * x)
        s += a * dec * np.sin(2 * np.pi * f * x * vib)
    return s * env_ad(n, 0.004, True, 0.4)


def balayage(f0, f1, duree, amp=0.3, forme="exp", dents=0.35):
    """Balayage de fréquence, avec une pointe de dent-de-scie pour le mordant."""
    x = t(duree)
    n = len(x)
    if forme == "exp":
        f = f0 * (f1 / f0) ** (x / duree)
    else:
        f = f0 + (f1 - f0) * (x / duree)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = (1.0 - dents) * np.sin(ph) + dents * (2.0 * (ph / (2 * np.pi) % 1.0) - 1.0)
    return amp * s * env_ad(n, 0.06, False)


def bruit_filtre(duree, f_centre, q=6.0, amp=0.3):
    """Bruit blanc passé dans un résonateur à deux pôles."""
    n = int(SR * duree)
    x = np.random.default_rng(7).standard_normal(n)
    w0 = 2 * math.pi * f_centre / SR
    r = math.exp(-w0 / (2 * q))
    a1, a2 = -2 * r * math.cos(w0), r * r
    y = np.zeros(n)
    for i in range(2, n):
        y[i] = x[i] - a1 * y[i - 1] - a2 * y[i - 2]
    y /= (np.max(np.abs(y)) + 1e-9)
    return amp * y


def craquement(duree, densite=26, amp=0.5, graine=1):
    """Foudre : salves de bruit très courtes, réparties aléatoirement."""
    n = int(SR * duree)
    rng = np.random.default_rng(graine)
    s = np.zeros(n)
    for _ in range(int(densite * duree)):
        p = rng.integers(0, max(1, n - 2000))
        L = int(rng.integers(140, 1800))
        seg = rng.standard_normal(L) * np.exp(-np.linspace(0, 7, L))
        f = rng.uniform(900, 5200)
        seg *= np.sin(2 * np.pi * f * np.arange(L) / SR)
        s[p:p + L] += seg * rng.uniform(0.35, 1.0)
    s /= (np.max(np.abs(s)) + 1e-9)
    return amp * s


def grondement(duree, f=42.0, amp=0.45):
    x = t(duree)
    n = len(x)
    s = np.sin(2 * np.pi * f * x) + 0.5 * np.sin(2 * np.pi * f * 1.5 * x)
    s += 0.35 * np.random.default_rng(3).standard_normal(n) * np.exp(-np.linspace(0, 4, n))
    return amp * s * env_ad(n, 0.01, True, 0.5)


def reverb(s, duree=1.6, melange=0.32, graine=11):
    """Réverbération simple par convolution avec un bruit décroissant."""
    n = int(SR * duree)
    rng = np.random.default_rng(graine)
    ir = rng.standard_normal(n) * np.exp(-np.linspace(0, 6.5, n))
    ir[0] = 1.0
    ir /= np.max(np.abs(ir))
    hum = np.convolve(s, ir)[:len(s) + n]
    hum /= (np.max(np.abs(hum)) + 1e-9)
    out = np.zeros(len(hum))
    out[:len(s)] += (1 - melange) * s
    out += melange * hum
    return out


def poser(base, s, debut):
    """Ajoute s dans base à l'instant debut (en secondes)."""
    i = int(SR * debut)
    fin = min(len(base), i + len(s))
    if fin > i:
        base[i:fin] += s[:fin - i]
    return base


def boucler(s, fondu=0.25):
    """Rend une nappe bouclable : la queue est fondue sur le début."""
    n = int(SR * fondu)
    if n * 2 >= len(s):
        return s
    tete, queue = s[:n].copy(), s[-n:].copy()
    r = np.linspace(0.0, 1.0, n)
    s = s[:-n]
    s[:n] = tete * r + queue * (1 - r)
    return s


def ecrire(chemin, s, stereo=True, largeur=0.35, normaliser=0.89):
    s = np.asarray(s, dtype=np.float64)
    m = np.max(np.abs(s)) + 1e-9
    s = s / m * normaliser
    if stereo:
        d = int(SR * 0.011)
        g = s.copy()
        dr = np.concatenate([np.zeros(d), s[:-d]]) if d else s.copy()
        gauche = g * (1 - largeur * 0.5) + dr * (largeur * 0.5)
        droite = dr * (1 - largeur * 0.5) + g * (largeur * 0.5)
        data = np.stack([gauche, droite], axis=1)
    else:
        data = s[:, None]
    data = np.clip(data, -1.0, 1.0)
    pcm = (data * 32767).astype("<i2")
    with wave.open(chemin, "wb") as f:
        f.setnchannels(pcm.shape[1])
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(pcm.tobytes())
    return len(s) / SR


# --------------------------------------------------------------------------
# Les sons de la zone
# --------------------------------------------------------------------------

GAMME = [261.63, 311.13, 349.23, 392.00, 466.16, 523.25, 622.25, 698.46]


def ambiance_arene(duree=12.0):
    """Nappe de l'arène : bourdon grave, battement, éclats de cristal épars."""
    x = t(duree)
    n = len(x)
    s = np.zeros(n)
    for f, a in ((55.0, 0.30), (82.5, 0.16), (110.0, 0.11), (164.8, 0.05)):
        deriv = 1.0 + 0.0025 * np.sin(2 * np.pi * 0.07 * x + f)
        s += a * np.sin(2 * np.pi * f * x * deriv)
    s += 0.05 * bruit_filtre(duree, 1400.0, q=1.2, amp=1.0)
    s *= 1.0 + 0.10 * np.sin(2 * np.pi * 0.11 * x)      # respiration lente
    rng = np.random.default_rng(5)
    for _ in range(14):
        d = rng.uniform(0.4, duree - 2.0)
        f = GAMME[rng.integers(0, len(GAMME))] * rng.choice([1.0, 2.0, 4.0])
        poser(s, cristal(f, 2.0, partiels=6, amp=rng.uniform(0.05, 0.13)), d)
    return boucler(reverb(s, 2.2, 0.30), fondu=0.9)


def transformation(duree=5.2):
    """
    Transformation Terastal -> Stellaire, calée sur l'animation :
    montée, enveloppement, silence suspendu, éclatement, résonance.
    """
    n = int(SR * duree)
    s = np.zeros(n)
    # 0,0 - 1,8  la puissance monte
    poser(s, balayage(70, 420, 1.8, amp=0.22, dents=0.20), 0.0)
    for i, f in enumerate(GAMME):
        poser(s, cristal(f * 2, 1.4, partiels=6, amp=0.10), 0.15 + i * 0.16)
    # 1,8 - 2,8  la sphère se referme
    poser(s, balayage(420, 1500, 1.0, amp=0.20, dents=0.45), 1.8)
    poser(s, bruit_filtre(1.0, 2600.0, q=3.0, amp=0.12)
          * np.linspace(0.2, 1.0, int(SR * 1.0)), 1.8)
    # 2,8 - 3,1  suspension : presque rien
    poser(s, cristal(1046.5, 0.35, partiels=4, amp=0.07), 2.85)
    # 3,1  éclatement
    poser(s, grondement(1.8, 38.0, 0.55), 3.10)
    poser(s, craquement(0.9, densite=60, amp=0.42, graine=4), 3.08)
    poser(s, balayage(2600, 300, 0.7, amp=0.18, forme="lin", dents=0.5), 3.10)
    # 3,3 - 5,2  résonance arc-en-ciel, accord ouvert
    for i, f in enumerate([261.63, 392.00, 523.25, 784.00, 1046.5]):
        poser(s, cristal(f, 1.9, partiels=8, brillance=1.05,
                         amp=0.16 - 0.02 * i), 3.30 + i * 0.05)
    return reverb(s, 2.6, 0.34)


def cercle_foudre(duree=2.0):
    """Anneau de foudre : craquements bouclables sur un souffle électrique."""
    s = craquement(duree, densite=34, amp=0.42, graine=9)
    s += bruit_filtre(duree, 3200.0, q=2.2, amp=0.10)
    x = t(duree)
    s += 0.06 * np.sin(2 * np.pi * 120.0 * x) * (0.6 + 0.4 * np.sin(2 * np.pi * 6.0 * x))
    return boucler(reverb(s[:int(SR * duree)], 0.9, 0.22), fondu=0.22)


def colonne_lumiere(duree=2.2):
    """Colonne de lumière : souffle montant et carillon arc-en-ciel."""
    n = int(SR * duree)
    s = np.zeros(n)
    poser(s, balayage(180, 2400, 0.9, amp=0.16, dents=0.15), 0.0)
    souffle = bruit_filtre(duree, 1800.0, q=1.0, amp=0.16)
    souffle *= np.exp(-np.linspace(0.0, 3.2, n))
    s += souffle
    for i, f in enumerate([523.25, 659.26, 783.99, 1046.5, 1318.5]):
        poser(s, cristal(f, 1.5, partiels=7, amp=0.13 - 0.015 * i), 0.12 + i * 0.07)
    return reverb(s, 1.8, 0.30)


def pilier_resonance(duree=2.6):
    """Un pilier de cristal que l'on frappe."""
    n = int(SR * duree)
    s = np.zeros(n)
    s += cristal(196.0, duree, partiels=9, brillance=0.95, amp=0.30)[:n]
    poser(s, bruit_filtre(0.08, 3400.0, q=1.5, amp=0.22), 0.0)
    poser(s, cristal(587.33, 1.6, partiels=6, amp=0.10), 0.02)
    return reverb(s, 2.0, 0.30)


def impact_stellaire(duree=3.0):
    """Impact de l'attaque stellaire."""
    n = int(SR * duree)
    s = np.zeros(n)
    poser(s, grondement(2.2, 34.0, 0.60), 0.0)
    poser(s, craquement(0.5, densite=80, amp=0.40, graine=2), 0.0)
    poser(s, balayage(1800, 90, 0.5, amp=0.22, forme="lin", dents=0.55), 0.0)
    for i, f in enumerate([130.81, 196.0, 261.63, 392.0]):
        poser(s, cristal(f, 2.2, partiels=8, amp=0.14), 0.06 + i * 0.04)
    return reverb(s, 2.4, 0.32)


CATALOGUE = {
    "ambiance_arene": (ambiance_arene, "nappe de l'arène, bouclable"),
    "transformation": (transformation, "Terastal vers Stellaire, 5,2 s"),
    "cercle_foudre": (cercle_foudre, "anneau de foudre, bouclable"),
    "colonne_lumiere": (colonne_lumiere, "jaillissement d'une colonne"),
    "pilier_resonance": (pilier_resonance, "impact sur un pilier"),
    "impact_stellaire": (impact_stellaire, "impact de l'attaque stellaire"),
}
