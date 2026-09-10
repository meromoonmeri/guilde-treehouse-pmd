from __future__ import annotations

"""Met le cafe Spinda a la meme taille que le cafe de Halcyon (Palikadude).

Mesures etablies en reconstruisant reellement les assets de Halcyon
(Content/Tile/Metano_Town_Objects.tile applique sur Data/Ground/metano_town.rsground,
zone reperee par l'objet 'Cafe_Entrance' en X=1144 Y=592) :

    facade du cafe de Halcyon = 208 x 101 px   (26 x ~12.6 cellules de 8 px)

Le batiment de spindacafevFINAL.png mesure 400 x 179 px (hors tapis du bas).
Facteur applique : 208 / 400 = 0.52

Sorties :
  spinda_cafe_taille_halcyon.png   image complete remise a l'echelle
  spinda_cafe_batiment.png         batiment seul, recadre
  spinda_cafe_pmdo_grille8.png     batiment cale sur la grille 8 px de PMDO
  spinda_cafe_comparaison.png      cote a cote avec la reference Halcyon
"""

from pathlib import Path
import sys

from PIL import Image

# Taille mesuree de la facade du cafe de Halcyon.
REF_W, REF_H = 208, 101

# Taille mesuree du batiment dans l'image source, tapis exclu.
SRC_BUILDING_W = 400
# Le tapis commence a cette ligne ; au-dessus, c'est le batiment.
SRC_BUILDING_BOTTOM = 190

TILE = 8  # GraphicsManager.TEX_SIZE


def building_box(im: Image.Image, bottom: int) -> tuple[int, int, int, int]:
    """bbox du batiment seul (on ignore tout ce qui est sous `bottom`)."""
    top = im.crop((0, 0, im.width, bottom))
    box = top.getbbox()
    if box is None:
        raise SystemExit("Image vide.")
    return box


def main() -> int:
    src_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("spindacafevFINAL.png")
    out_dir = src_path.parent
    if not src_path.exists():
        print(f"Introuvable : {src_path}")
        return 1

    im = Image.open(src_path).convert("RGBA")
    bx0, by0, bx1, by1 = building_box(im, SRC_BUILDING_BOTTOM)
    bw, bh = bx1 - bx0, by1 - by0
    print(f"Source            : {im.width} x {im.height}")
    print(f"Batiment source   : {bw} x {bh}  (bbox {bx0},{by0} -> {bx1},{by1})")
    print(f"Reference Halcyon : {REF_W} x {REF_H}")

    factor = REF_W / bw
    print(f"Facteur           : {REF_W}/{bw} = {factor:.4f}")

    # L'image source est deja lissee (44 971 couleurs, alpha sur 256 niveaux) :
    # ce n'est pas du pixel-art 1:1. LANCZOS conserve donc mieux le dessin que
    # NEAREST, qui produirait des escaliers sans rien gagner en nettete.
    new_size = (round(im.width * factor), round(im.height * factor))
    full = im.resize(new_size, Image.LANCZOS)
    full.save(out_dir / "spinda_cafe_taille_halcyon.png")
    print(f"\nImage complete    : {full.width} x {full.height}"
          f"  -> spinda_cafe_taille_halcyon.png")

    # Batiment seul, recadre au pixel pres.
    nb = full.crop((round(bx0 * factor), round(by0 * factor),
                    round(bx1 * factor), round(by1 * factor)))
    nb.save(out_dir / "spinda_cafe_batiment.png")
    print(f"Batiment seul     : {nb.width} x {nb.height}"
          f"  -> spinda_cafe_batiment.png  (cible {REF_W} x ...)")

    # Version calee sur la grille 8 px, prete a decouper en .tile pour PMDO.
    gw = (nb.width + TILE - 1) // TILE * TILE
    gh = (nb.height + TILE - 1) // TILE * TILE
    grid = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    grid.paste(nb, ((gw - nb.width) // 2, gh - nb.height), nb)
    grid.save(out_dir / "spinda_cafe_pmdo_grille8.png")
    print(f"Grille PMDO 8 px  : {gw} x {gh}"
          f"  = {gw // TILE} x {gh // TILE} cellules"
          f"  -> spinda_cafe_pmdo_grille8.png")

    # Comparaison visuelle avec la reference, si elle est disponible.
    ref_path = out_dir / "cafe_halcyon_reference.png"
    if ref_path.exists():
        ref = Image.open(ref_path).convert("RGBA")
        pad = 12
        cw = nb.width + ref.width + pad * 3
        ch = max(nb.height, ref.height) + pad * 2
        cmp_im = Image.new("RGBA", (cw, ch), (40, 40, 48, 255))
        cmp_im.paste(ref, (pad, ch - pad - ref.height), ref)
        cmp_im.paste(nb, (pad * 2 + ref.width, ch - pad - nb.height), nb)
        cmp_im.save(out_dir / "spinda_cafe_comparaison.png")
        print(f"Comparaison       : Halcyon {ref.width}x{ref.height}"
              f" | Spinda {nb.width}x{nb.height}"
              f"  -> spinda_cafe_comparaison.png")

    return 0


if __name__ == "__main__":
    sys.exit(main())
