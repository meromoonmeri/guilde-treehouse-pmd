"""Build the complete Politoed multi-sheet sprite pack.

The 0-12 dungeon animations are kept from the current SpriteCollab source.
Starter animations 13-34 are authored from those canonical Politoed frames:
integer-pixel transforms only, with explicit offsets and PMD shadow layers.
No resampled or foreign Pokemon artwork is shipped as a final frame.
"""
from __future__ import annotations

import shutil
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "source" / "sprites_politoed" / "canonical"
OUT = ROOT / "sprite" / "0186"
ZIP_OUT = ROOT / "sprite-0186.zip"

# The starter contract from the PMD Sprite guide.  An animation with rows=8
# has one row for each PMD direction; rows=1 is a deliberate one-direction
# starter animation, as used by the official SpriteCollab files.
SPECS = [
    ("EventSleep", 13, 40, 40, (30, 35), 8),
    ("Wake", 14, 40, 64, (8, 6, 14, 4, 10), 8),
    ("Eat", 15, 40, 56, (6, 8, 6, 8), 1),
    ("Tumble", 16, 48, 48, (3, 3, 3, 3, 3, 3, 3, 3), 1),
    ("Pose", 17, 40, 64, (12, 2, 8), 8),
    ("Pull", 18, 48, 64, (10, 12, 10, 12, 10, 12, 10), 1),
    ("Pain", 19, 48, 64, (4, 1, 1, 1, 2, 1, 4, 2, 2, 2, 2, 2), 8),
    ("Float", 20, 40, 64, (9, 18, 9, 14), 8),
    ("DeepBreath", 21, 40, 64, (12, 6, 6, 6, 6, 6, 6, 10, 4), 1),
    ("Nod", 22, 40, 64, (6, 8, 6), 8),
    ("Sit", 23, 40, 48, (8, 8, 8), 1),
    ("LookUp", 24, 40, 64, (6, 6), 1),
    ("Sink", 25, 40, 64, (6,) * 12, 1),
    ("Trip", 26, 48, 64, (4, 6, 4, 4, 4), 8),
    ("Laying", 27, 48, 40, (12,), 8),
    ("LeapForth", 28, 40, 80, (6, 1, 1, 2, 2, 2), 1),
    ("Head", 29, 40, 64, (4,), 8),
    ("Cringe", 30, 40, 64, (2, 8), 1),
    ("LostBalance", 31, 48, 64, (8, 8), 1),
    ("TumbleBack", 32, 48, 64, (3,) * 10, 1),
    ("Faint", 33, 48, 48, (8, 12, 4, 10), 8),
    ("HitGround", 34, 48, 48, (4, 4, 4, 4, 4, 6, 4, 4), 1),
]


def source_xml() -> ET.ElementTree:
    return ET.parse(CANONICAL / "AnimData.xml")


SOURCE_META: dict[str, tuple[int, int, int]] = {}
for _anim in source_xml().getroot().find("Anims") or []:
    if _anim.find("CopyOf") is not None:
        continue
    SOURCE_META[_anim.findtext("Name", "")] = (
        int(_anim.findtext("FrameWidth", "0")),
        int(_anim.findtext("FrameHeight", "0")),
        len(_anim.findall("./Durations/Duration")),
    )


def source_frame(name: str, direction: int, index: int) -> Image.Image:
    """Return one canonical opaque/transparent Politoed art frame."""
    fw, fh, count = SOURCE_META[name]
    direction = direction if name != "Sleep" else 0
    direction = min(direction, 7)
    if index >= count:
        index = count - 1
    image = Image.open(CANONICAL / f"{name}-Anim.png").convert("RGBA")
    return image.crop((index * fw, direction * fh, (index + 1) * fw, (direction + 1) * fh))


def _bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    return image.getchannel("A").getbbox()


def _largest_component_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    """Find the main connected sprite and ignore optional detached effects."""
    alpha = image.getchannel("A")
    w, h = image.size
    mask = alpha.load()
    seen: set[tuple[int, int]] = set()
    best: list[tuple[int, int]] = []
    for y in range(h):
        for x in range(w):
            if not mask[x, y] or (x, y) in seen:
                continue
            stack = [(x, y)]
            seen.add((x, y))
            component: list[tuple[int, int]] = []
            while stack:
                xx, yy = stack.pop()
                component.append((xx, yy))
                for nx, ny in ((xx - 1, yy), (xx + 1, yy), (xx, yy - 1), (xx, yy + 1)):
                    if 0 <= nx < w and 0 <= ny < h and mask[nx, ny] and (nx, ny) not in seen:
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            if len(component) > len(best):
                best = component
    if not best:
        return None
    return (
        min(x for x, _ in best),
        min(y for _, y in best),
        max(x for x, _ in best) + 1,
        max(y for _, y in best) + 1,
    )


def _transform(image: Image.Image, scale_x: int = 100, scale_y: int = 100, angle: int = 0) -> Image.Image:
    w, h = image.size
    if scale_x != 100 or scale_y != 100:
        image = image.resize(
            (max(1, round(w * scale_x / 100)), max(1, round(h * scale_y / 100))),
            Image.Resampling.NEAREST,
        )
    if angle:
        image = image.rotate(angle, resample=Image.Resampling.NEAREST, expand=True)
    return image


def render(
    image: Image.Image,
    frame_width: int,
    frame_height: int,
    *,
    dx: int = 0,
    dy: int = 0,
    scale_x: int = 100,
    scale_y: int = 100,
    angle: int = 0,
    flip: bool = False,
) -> Image.Image:
    """Place an existing pixel-art pose on a centered PMD frame.

    PMD sprites use the standard shadow center at frame_height / 2 + 4.  The
    main component is baseline-aligned to that point, so starter animations
    remain compatible with the official Politoed dungeon animations.
    """
    image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if flip else image
    image = _transform(image, scale_x, scale_y, angle)
    box = _largest_component_bbox(image) or _bbox(image)
    frame = Image.new("RGBA", (frame_width, frame_height), (0, 0, 0, 0))
    if box is None:
        return frame
    left, top, right, bottom = box
    visual_center = (left + right - 1) / 2
    target_center = (frame_width - 1) / 2 + dx
    shadow_y = frame_height // 2 + 4 + dy
    x = round(target_center - visual_center)
    y = shadow_y - bottom
    frame.alpha_composite(image, (x, y))
    return frame


def _dir_image(name: str, direction: int, index: int) -> Image.Image:
    return source_frame(name, direction, index)


def _directional(name: str, direction: int, index: int) -> Image.Image:
    return _dir_image(name, direction, index)


def _frame(name: str, direction: int, index: int, fw: int, fh: int, **kwargs: int | bool) -> Image.Image:
    return render(_directional(name, direction, index), fw, fh, **kwargs)


def _sleep_frame(index: int, flip: bool = False) -> Image.Image:
    image = source_frame("Sleep", 0, index)
    return image.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if flip else image


def make_starter_frame(name: str, direction: int, index: int, fw: int, fh: int) -> Image.Image:
    """Author one frame of one starter animation from canonical Politoed art."""
    # The four side/diagonal rows retain Politoed's curled asymmetry by using
    # their real direction instead of mirroring a front-facing source.
    if name == "EventSleep":
        return render(_sleep_frame(index, direction in (2, 3)), fw, fh)

    if name == "Wake":
        source = _sleep_frame(index, direction in (2, 3)) if index < 2 else _dir_image("Idle", direction, min(index - 2, 4))
        return render(source, fw, fh, dy=(-2 if index == 1 else 0))

    if name == "Eat":
        attack_frames = (0, 2, 5, 11)
        return _frame("Attack", 0, attack_frames[index], fw, fh, dx=(-1, -2, -1, 0)[index])

    if name == "Tumble":
        angles = (0, 45, 90, 135, 180, 225, 270, 315)
        return _frame("Walk", 0, 0, fw, fh, angle=angles[index])

    if name == "Pose":
        if index == 0:
            return _frame("Idle", direction, 0, fw, fh)
        if index == 1:
            return _frame("Attack", direction, 2, fw, fh, dy=-1)
        return _frame("Attack", direction, 5, fw, fh)

    if name == "Pull":
        attack_frames = (0, 1, 2, 3, 4, 5, 6)
        shifts = (-2, -1, 0, 1, 2, 1, 0)
        return _frame("Attack", 0, attack_frames[index], fw, fh, dx=shifts[index])

    if name == "Pain":
        hurt_frame = (0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1)[index]
        shifts = (0, -1, 1, -1, 1, 0, 0, -1, 1, -1, 1, 0)
        return _frame("Hurt", direction, hurt_frame, fw, fh, dx=shifts[index])

    if name == "Float":
        offsets = (0, -3, -5, -2)
        return _frame("Idle", direction, (0, 1, 2, 1)[index], fw, fh, dy=offsets[index])

    if name == "DeepBreath":
        idle_frames = (0, 1, 2, 3, 4, 3, 2, 1, 0)
        scales = (100, 101, 103, 105, 103, 101, 100, 100, 100)
        return _frame("Idle", 0, idle_frames[index], fw, fh, scale_x=scales[index], scale_y=scales[index])

    if name == "Nod":
        return _frame("Idle", direction, (0, 1, 0)[index], fw, fh, dy=(0, 2, 0)[index])

    if name == "Sit":
        return _frame("Walk", 0, (0, 6, 6)[index], fw, fh, scale_y=(100, 92, 88)[index])

    if name == "LookUp":
        return _frame("Walk", 4, index, fw, fh)

    if name == "Sink":
        scales = (100, 96, 88, 80, 72, 64, 56, 48, 40, 32, 24, 16)
        return _frame("Walk", 0, 0, fw, fh, scale_y=scales[index])

    if name == "Trip":
        angles = (0, -8, -25, -50, -75)
        return _frame("Walk", direction, (0, 1, 2, 5, 6)[index], fw, fh, angle=angles[index], dx=(0, 1, 2, 2, 1)[index])

    if name == "Laying":
        return render(_sleep_frame(0, direction in (2, 3)), fw, fh)

    if name == "LeapForth":
        sources = (source_frame("Walk", 0, 6), source_frame("Attack", 0, 1), source_frame("Attack", 0, 4), source_frame("Attack", 0, 5), source_frame("Walk", 0, 1), source_frame("Walk", 0, 0))
        jumps = (0, -5, -12, -15, -8, 0)
        return render(sources[index], fw, fh, dy=jumps[index])

    if name == "Head":
        return _frame("Idle", direction, 0, fw, fh)

    if name == "Cringe":
        return _frame("Hurt", 0, index, fw, fh, dy=(0, 3)[index], scale_y=(100, 90)[index])

    if name == "LostBalance":
        return _frame("Walk", 0, 0, fw, fh, angle=(-18, 18)[index])

    if name == "TumbleBack":
        angles = (0, 40, 80, 120, 160, 200, 240, 280, 320, 360)
        return _frame("Walk", 0, 0, fw, fh, angle=angles[index])

    if name == "Faint":
        angles = (0, 12, 38, 72)
        scales = (100, 98, 94, 88)
        return _frame("Walk", direction, 0, fw, fh, angle=angles[index], scale_y=scales[index])

    if name == "HitGround":
        sources = (source_frame("Walk", 0, 0), source_frame("Walk", 0, 6), source_frame("Walk", 0, 6), source_frame("Sleep", 0, 0), source_frame("Sleep", 0, 1), source_frame("Sleep", 0, 0), source_frame("Walk", 0, 6), source_frame("Walk", 0, 0))
        angles = (0, -12, -28, -55, -70, -70, -25, 0)
        scales = (100, 98, 94, 90, 88, 88, 94, 100)
        return render(sources[index], fw, fh, angle=angles[index], scale_y=scales[index])

    raise ValueError(f"unhandled starter animation {name}")


# Use the exact PMD shadow palette and silhouette from the canonical source.
SHADOW_TEMPLATE = Image.open(CANONICAL / "Walk-Shadow.png").convert("RGBA").crop((9, 36, 31, 45))


def make_shadow(frame_width: int, frame_height: int) -> Image.Image:
    out = Image.new("RGBA", (frame_width, frame_height), (0, 0, 0, 0))
    center_x = frame_width // 2
    center_y = frame_height // 2 + 4
    out.alpha_composite(SHADOW_TEMPLATE, (center_x - 11, center_y - 4))
    return out


def make_offsets(art: Image.Image) -> Image.Image:
    """Mark head, center, right hand and left hand in PMD's offset colors."""
    out = Image.new("RGBA", art.size, (0, 0, 0, 0))
    box = _largest_component_bbox(art) or _bbox(art)
    if box is None:
        return out
    left, top, right, bottom = box
    width = max(1, right - left)
    height = max(1, bottom - top)
    # The marker convention is black=head, green=body, red=right hand,
    # blue=left hand. Keep them on separate pixels even on narrow side views.
    points = [
        ((round(left + width * 0.50), round(top + height * 0.20)), (0, 0, 0, 255)),
        ((round(left + width * 0.50), round(top + height * 0.62)), (0, 255, 0, 255)),
        ((round(left + width * 0.20), round(top + height * 0.56)), (255, 0, 0, 255)),
        ((round(left + width * 0.80), round(top + height * 0.56)), (0, 0, 255, 255)),
    ]
    used: set[tuple[int, int]] = set()
    for (x, y), color in points:
        x = min(art.width - 1, max(0, x))
        y = min(art.height - 1, max(0, y))
        # Move a colliding marker by one pixel without leaving the main body.
        candidates = [(x, y), (x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
        for candidate in candidates:
            if candidate not in used and 0 <= candidate[0] < art.width and 0 <= candidate[1] < art.height:
                x, y = candidate
                used.add(candidate)
                out.putpixel((x, y), color)
                break
    return out


def _append_xml(tree: ET.ElementTree) -> None:
    root = tree.getroot()
    anims = root.find("Anims")
    if anims is None:
        raise ValueError("canonical AnimData.xml has no Anims element")
    for name, index, fw, fh, durations, rows in SPECS:
        anim = ET.SubElement(anims, "Anim")
        ET.SubElement(anim, "Name").text = name
        ET.SubElement(anim, "Index").text = str(index)
        ET.SubElement(anim, "FrameWidth").text = str(fw)
        ET.SubElement(anim, "FrameHeight").text = str(fh)
        if name in {"LeapForth"}:
            # The launch is the first airborne frame for a leap.
            ET.SubElement(anim, "RushFrame").text = "1"
        durations_node = ET.SubElement(anim, "Durations")
        for duration in durations:
            ET.SubElement(durations_node, "Duration").text = str(duration)


def _write_animation(name: str, fw: int, fh: int, durations: tuple[int, ...], rows: int) -> None:
    frames: list[Image.Image] = []
    offsets: list[Image.Image] = []
    shadows: list[Image.Image] = []
    for direction in range(rows):
        for index in range(len(durations)):
            art = make_starter_frame(name, direction, index, fw, fh)
            frames.append(art)
            offsets.append(make_offsets(art))
            shadows.append(make_shadow(fw, fh))
    sheet_size = (fw * len(durations), fh * rows)
    for suffix, collection in (("Anim", frames), ("Offsets", offsets), ("Shadow", shadows)):
        sheet = Image.new("RGBA", sheet_size, (0, 0, 0, 0))
        for n, frame in enumerate(collection):
            x = (n % len(durations)) * fw
            y = (n // len(durations)) * fh
            sheet.alpha_composite(frame, (x, y))
        sheet.save(OUT / f"{name}-{suffix}.png", optimize=True)


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # Copy every official file first. This preserves all Chunsoft/CUR pixels,
    # existing dungeon timing, optional attack variants, and original credits.
    for path in CANONICAL.iterdir():
        if path.is_file() and path.name not in {"AnimData.xml", "credits.txt"}:
            shutil.copyfile(path, OUT / path.name)
    tree = source_xml()
    _append_xml(tree)
    ET.indent(tree, space="\t")
    tree.write(OUT / "AnimData.xml", encoding="utf-8", xml_declaration=True)
    credits = (CANONICAL / "credits.txt").read_text(encoding="utf-8").rstrip() + "\n"
    credits += "2026-09-15\tmeromoonmeri / Arena.ai Agent\tNEW\tEventSleep, Wake, Eat, Tumble, Pose, Pull, Pain, Float, DeepBreath, Nod, Sit, LookUp, Sink, Trip, Laying, LeapForth, Head, Cringe, LostBalance, TumbleBack, Faint, HitGround\n"
    (OUT / "credits.txt").write_text(credits, encoding="utf-8")
    for name, _index, fw, fh, durations, rows in SPECS:
        _write_animation(name, fw, fh, durations, rows)
    # Fixed timestamps keep the submitted archive reproducible across builds.
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(OUT.iterdir()):
            if not path.is_file():
                continue
            info = zipfile.ZipInfo(path.name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())


if __name__ == "__main__":
    build()
