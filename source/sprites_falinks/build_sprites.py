"""Build the Falinks #0870 form 0 sprite sheets for SpriteCollab.

Form 0 is the whole Falinks formation. SpriteCollab already has the two halves
as canonical art:

  sprite/0870/0002 = Brass    (the leader)
  sprite/0870/0003 = Trooper  (the rank and file)

Both share one identical 13-colour palette, so the formation is composed from
their canonical pixels with no recolouring, no resampling and no rotation:
per animation, per direction, per frame, the Brass is drawn at the head of the
column and Troopers are placed behind him along the marching axis, in the
formation depth order the game expects.

Nothing here is AI generated: every pixel comes from the published sheets.
"""
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CANON = Path(__file__).resolve().parent / "canonical"
BRASS = CANON / "brass"
TROOPER = CANON / "trooper"
OUT = ROOT / "sprite" / "0870"

# PMD direction order used by every sheet row.
DIRECTIONS = ["down", "down-right", "right", "up-right", "up",
              "up-left", "left", "down-left"]
# Unit vector of each direction, in sheet pixels. The formation lines up
# *behind* the Brass, so troopers are offset along the negative facing vector.
VECTORS = {
    "down": (0, 1), "down-right": (1, 1), "right": (1, 0), "up-right": (1, -1),
    "up": (0, -1), "up-left": (-1, -1), "left": (-1, 0), "down-left": (-1, 1),
}

# Three troopers trail the Brass: enough to read as a formation without
# turning the frame into an unreadable pile at dungeon zoom.
TROOPER_COUNT = 3
# Spacing between two consecutive members along the column axis.
SPACING = 7


def load_sheet(path):
    return Image.open(path).convert("RGBA")


def frames(sheet, width, height):
    """Split a sheet into a grid of frames: rows are directions."""
    cols, rows = sheet.width // width, sheet.height // height
    return [[sheet.crop((c * width, r * height, (c + 1) * width, (r + 1) * height))
             for c in range(cols)] for r in range(rows)], cols, rows


def anim_entries(path):
    root = ET.parse(path).getroot()
    entries = {}
    for anim in root.find("Anims"):
        entries[anim.findtext("Name")] = anim
    return root, entries


def compose_frame(brass, trooper, direction, size):
    """One formation frame: troopers behind, Brass in front and drawn last."""
    width, height = size
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    dx, dy = VECTORS[direction]
    # Draw from the back of the column forward so the Brass overlaps correctly.
    for rank in range(TROOPER_COUNT, 0, -1):
        offset_x = -dx * SPACING * rank
        offset_y = -dy * SPACING * rank
        layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        layer.paste(trooper, (
            (width - trooper.width) // 2 + offset_x,
            (height - trooper.height) // 2 + offset_y,
        ))
        canvas = Image.alpha_composite(canvas, layer)
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    layer.paste(brass, ((width - brass.width) // 2, (height - brass.height) // 2))
    return Image.alpha_composite(canvas, layer)


def formation_size(brass_size, trooper_size):
    """Grow the frame so the whole column fits, keeping even dimensions."""
    reach = SPACING * TROOPER_COUNT
    width = max(brass_size[0], trooper_size[0]) + 2 * reach
    height = max(brass_size[1], trooper_size[1]) + 2 * reach
    return width + width % 2, height + height % 2


def build_animation(name, brass_anim, trooper_anim):
    """Return the three composed sheets and the frame size for one animation."""
    bw = int(brass_anim.findtext("FrameWidth"))
    bh = int(brass_anim.findtext("FrameHeight"))
    tw = int(trooper_anim.findtext("FrameWidth"))
    th = int(trooper_anim.findtext("FrameHeight"))
    width, height = formation_size((bw, bh), (tw, th))

    sheets = {}
    for kind in ("Anim", "Offsets", "Shadow"):
        brass_frames, bcols, brows = frames(load_sheet(BRASS / f"{name}-{kind}.png"), bw, bh)
        troop_frames, tcols, trows = frames(load_sheet(TROOPER / f"{name}-{kind}.png"), tw, th)
        cols = max(bcols, tcols)
        rows = max(brows, trows)
        sheet = Image.new("RGBA", (cols * width, rows * height), (0, 0, 0, 0))
        for r in range(rows):
            direction = DIRECTIONS[r % len(DIRECTIONS)]
            for c in range(cols):
                brass = brass_frames[min(r, brows - 1)][min(c, bcols - 1)]
                trooper = troop_frames[min(r, trows - 1)][min(c, tcols - 1)]
                if kind == "Offsets":
                    # Offsets describe the Brass only: he is the acting body.
                    frame = Image.new("RGBA", (width, height), (0, 0, 0, 0))
                    frame.paste(brass, ((width - bw) // 2, (height - bh) // 2))
                else:
                    frame = compose_frame(brass, trooper, direction, (width, height))
                sheet.paste(frame, (c * width, r * height))
        sheets[kind] = sheet
    return sheets, width, height


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    brass_root, brass_anims = anim_entries(BRASS / "AnimData.xml")
    _, trooper_anims = anim_entries(TROOPER / "AnimData.xml")

    out_root = ET.Element("AnimData")
    ET.SubElement(out_root, "ShadowSize").text = brass_root.findtext("ShadowSize")
    out_anims = ET.SubElement(out_root, "Anims")

    for anim in brass_root.find("Anims"):
        name = anim.findtext("Name")
        node = ET.SubElement(out_anims, "Anim")
        ET.SubElement(node, "Name").text = name
        ET.SubElement(node, "Index").text = anim.findtext("Index")
        if anim.findtext("CopyOf"):
            ET.SubElement(node, "CopyOf").text = anim.findtext("CopyOf")
            continue

        sheets, width, height = build_animation(name, anim, trooper_anims[name])
        for kind, sheet in sheets.items():
            sheet.save(OUT / f"{name}-{kind}.png")

        ET.SubElement(node, "FrameWidth").text = str(width)
        ET.SubElement(node, "FrameHeight").text = str(height)
        for tag in ("RushFrame", "HitFrame", "ReturnFrame"):
            if anim.findtext(tag):
                ET.SubElement(node, tag).text = anim.findtext(tag)
        durations = ET.SubElement(node, "Durations")
        for duration in anim.find("Durations"):
            ET.SubElement(durations, "Duration").text = duration.text
        print(f"{name}: {width}x{height}")

    ET.indent(out_root, space="\t")
    ET.ElementTree(out_root).write(OUT / "AnimData.xml", encoding="utf-8",
                                   xml_declaration=True)

    (OUT / "credits.txt").write_text(
        "2023-01-04 01:46:59.676997\t<@!215638650434617345>\tCUR\tPMDCollab_1\t"
        "Brass base used for the formation\n"
        "2024-12-22 02:08:38.853154\t<@!544245909639397378>\tCUR\tCC_BY-NC_4\t"
        "Trooper base used for the formation\n"
        "2026-09-15\tArena.ai Agent for meromoonmeri\tNEW\tUnspecified\t"
        "Form 0 formation composition of the canonical Brass and Trooper sheets\n"
    )
    print("form 0 formation written to", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
