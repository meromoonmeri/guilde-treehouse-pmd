"""Build a complete Falinks (#0870) PMD / SpriteCollab pack.

The existing Falinks dungeon sheets are the immutable base.  Missing starter
animations are authored frame by frame from those exact Falinks poses, with
nearest-neighbour integer transforms and a few hand-drawn pixels in the
canonical palette.  No other Pokemon artwork is used and no AI image is
inserted directly into a final sheet.
"""
from __future__ import annotations

import shutil
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "source" / "sprites_falinks" / "canonical"
OUT = ROOT / "sprite" / "0870" / "0002"
ZIP_OUT = ROOT / "sprite-0870-0002.zip"
ZIP_ALIAS = ROOT / "sprite-0870.zip"

# Falinks already has the official dungeon animations 0-3 and 5-12.  The
# generator supplies missing RearUp (4) and Starter IDs 13-34.  Sizes stay
# even and close to the native Falinks art, as required by the PMD guide.
SPECS = [
    ("RearUp", 4, 24, 40, (6, 6, 6, 6, 6, 6), 8),
    ("EventSleep", 13, 24, 24, (30, 35), 8),
    ("Wake", 14, 24, 32, (8, 6, 14, 4, 10), 8),
    ("Eat", 15, 32, 32, (6, 8, 6, 8), 1),
    ("Tumble", 16, 32, 32, (3, 3, 3, 3, 3, 3, 3, 3), 1),
    ("Pose", 17, 24, 40, (8, 6, 6, 6, 8), 8),
    ("Pull", 18, 32, 32, (10, 12, 10, 12, 10, 12, 10), 1),
    ("Pain", 19, 40, 48, (4, 1, 1, 1, 2, 1, 4, 2, 2, 2, 2, 2), 8),
    ("Float", 20, 24, 32, (9, 18, 9, 14), 8),
    ("DeepBreath", 21, 24, 32, (12, 6, 6, 6, 6, 6, 6, 10, 4), 1),
    ("Nod", 22, 24, 32, (6, 8, 6), 8),
    ("Sit", 23, 24, 32, (8, 8, 8), 1),
    ("LookUp", 24, 24, 32, (6, 8, 6), 1),
    ("Sink", 25, 24, 32, (6,) * 12, 1),
    ("Trip", 26, 32, 40, (4, 6, 4, 4, 4), 8),
    ("Laying", 27, 32, 24, (12,), 8),
    ("LeapForth", 28, 24, 48, (6, 1, 1, 2, 2, 2), 1),
    ("Head", 29, 24, 32, (4,), 8),
    ("Cringe", 30, 24, 32, (2, 8), 1),
    ("LostBalance", 31, 32, 40, (8, 8), 1),
    ("TumbleBack", 32, 32, 40, (3,) * 10, 1),
    ("Faint", 33, 32, 32, (8, 12, 4, 10), 8),
    ("HitGround", 34, 32, 32, (4, 4, 4, 4, 4, 6, 4, 4), 1),
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
    fw, fh, count = SOURCE_META[name]
    direction = 0 if name == "Sleep" else min(direction, 7)
    index = min(index, count - 1)
    image = Image.open(CANONICAL / f"{name}-Anim.png").convert("RGBA")
    return image.crop((index * fw, direction * fh, (index + 1) * fw, (direction + 1) * fh))


def _bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    return image.getchannel("A").getbbox()


def _largest_component_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    alpha = image.getchannel("A")
    w, h = image.size
    mask = alpha.load()
    seen: set[tuple[int, int]] = set()
    best: list[tuple[int, int]] = []
    for y in range(h):
        for x in range(w):
            if not mask[x, y] or (x, y) in seen:
                continue
            queue = [(x, y)]
            seen.add((x, y))
            component: list[tuple[int, int]] = []
            while queue:
                xx, yy = queue.pop()
                component.append((xx, yy))
                for nx, ny in ((xx - 1, yy), (xx + 1, yy), (xx, yy - 1), (xx, yy + 1)):
                    if 0 <= nx < w and 0 <= ny < h and mask[nx, ny] and (nx, ny) not in seen:
                        seen.add((nx, ny))
                        queue.append((nx, ny))
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


def _transform(image: Image.Image, angle: int = 0) -> Image.Image:
    if angle:
        return image.rotate(angle, resample=Image.Resampling.NEAREST, expand=True)
    return image


def render(
    image: Image.Image,
    frame_width: int,
    frame_height: int,
    *,
    dx: int = 0,
    dy: int = 0,
    angle: int = 0,
    flip: bool = False,
) -> Image.Image:
    """Center and baseline-align one native Falinks pixel-art pose."""
    if flip:
        image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    image = _transform(image, angle)
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


def _frame(name: str, direction: int, index: int, fw: int, fh: int, **kwargs: int | bool) -> Image.Image:
    return render(source_frame(name, direction, index), fw, fh, **kwargs)


def _sleep_frame(index: int, flip: bool = False) -> Image.Image:
    image = source_frame("Sleep", 0, index)
    return image.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if flip else image


# Exact colors from the canonical Falinks SpriteCollab sheets.
BLACK = (0, 0, 0, 255)
DARK = (33, 41, 41, 255)
BLUE = (49, 189, 247, 255)
DARK_BLUE = (74, 82, 82, 255)
BROWN = (115, 57, 0, 255)
CYAN = (115, 255, 255, 255)
DARK_RED = (156, 0, 0, 255)
BROWN_GOLD = (165, 107, 0, 255)
RED = (214, 57, 0, 255)
CREAM = (214, 222, 222, 255)
GOLD = (222, 181, 0, 255)
YELLOW = (255, 247, 0, 255)
WHITE = (255, 255, 255, 255)


def _paint(frame: Image.Image, points: list[tuple[int, int]], color: tuple[int, int, int, int]) -> None:
    for x, y in points:
        if 0 <= x < frame.width and 0 <= y < frame.height:
            frame.putpixel((x, y), color)


def _main_box(frame: Image.Image) -> tuple[int, int, int, int] | None:
    return _largest_component_bbox(frame) or _bbox(frame)


def _open_face(frame: Image.Image, index: int) -> Image.Image:
    """Manual Falinks visor/mouth pixels for Eat and DeepBreath."""
    if index not in (1, 3, 4, 5):
        return frame
    frame = frame.copy()
    box = _main_box(frame)
    if box is None:
        return frame
    left, top, right, bottom = box
    center = round((left + right - 1) / 2)
    y = top + max(2, round((bottom - top) * 0.62))
    _paint(frame, [(center - 2, y), (center - 1, y), (center, y), (center + 1, y), (center + 2, y)], DARK_RED)
    _paint(frame, [(center - 1, y + 1), (center, y + 1), (center + 1, y + 1)], GOLD)
    return frame


def _effort_marks(frame: Image.Image, index: int) -> Image.Image:
    if index not in (1, 3, 5):
        return frame
    frame = frame.copy()
    box = _main_box(frame)
    if box is None:
        return frame
    left, top, right, bottom = box
    y = top + round((bottom - top) * 0.35)
    _paint(frame, [(left - 3, y), (left - 2, y - 2), (right + 2, y), (right + 1, y - 2)], WHITE)
    return frame


def _impact_marks(frame: Image.Image, index: int) -> Image.Image:
    if index not in (3, 4, 5):
        return frame
    frame = frame.copy()
    box = _main_box(frame)
    if box is None:
        return frame
    left, _top, right, bottom = box
    center = round((left + right - 1) / 2)
    _paint(frame, [(left - 2, bottom), (right + 1, bottom)], WHITE)
    _paint(frame, [(center - 3, bottom + 1), (center + 3, bottom + 1)], BLUE)
    return frame


def _clip_below(frame: Image.Image, y_limit: int) -> Image.Image:
    frame = frame.copy()
    for y in range(max(0, y_limit), frame.height):
        for x in range(frame.width):
            if frame.getpixel((x, y))[3]:
                frame.putpixel((x, y), (0, 0, 0, 0))
    return frame


def _head_only(direction: int, fw: int, fh: int) -> Image.Image:
    source = source_frame("Idle", direction, 0)
    box = _main_box(source)
    if box is None:
        return Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
    _left, top, _right, bottom = box
    head = source.crop((0, top, source.width, min(bottom, top + 10)))
    return render(head, fw, fh, dy=-5)


def make_starter_frame(name: str, direction: int, index: int, fw: int, fh: int) -> Image.Image:
    """Make exactly one starter frame from canonical Falinks source pixels."""
    if name == "RearUp":
        # Hop is the official Falinks movement reference: rise, hold, settle.
        hop_frames = (0, 1, 2, 3, 4, 5)
        hop_dy = (0, -1, -2, -2, -1, 0)
        return _frame("Hop", direction, hop_frames[index], fw, fh, dy=hop_dy[index])

    if name == "EventSleep":
        return render(_sleep_frame(index, direction in (2, 3)), fw, fh)

    if name == "Wake":
        source = _sleep_frame(index, direction in (2, 3)) if index < 2 else source_frame("Idle", direction, min(index - 2, 5))
        return render(source, fw, fh, dy=-1 if index == 1 else 0)

    if name == "Eat":
        source_frames = (0, 1, 2, 1)
        return _open_face(_frame("Idle", 0, source_frames[index], fw, fh, dy=(0, 1, 1, 0)[index]), index)

    if name == "Tumble":
        return _frame("Walk", 0, 0, fw, fh, angle=(0, 45, 90, 135, 180, 225, 270, 315)[index])

    if name == "Pose":
        # Reuse the generated RearUp choreography with a held crest-first pose.
        hop_frames = (1, 2, 3, 4, 3)
        return _frame("Hop", direction, hop_frames[index], fw, fh, dy=(-1, -2, -3, -2, -1)[index])

    if name == "Pull":
        walk_frames = (1, 0, 1, 0, 1, 0, 0)
        return _effort_marks(_frame("Walk", 4, walk_frames[index], fw, fh, dy=(0, 1, 0, 1, 0, 1, 0)[index]), index)

    if name == "Pain":
        hurt_frames = (0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1)
        return _frame("Hurt", direction, hurt_frames[index], fw, fh, dx=(0, -1, 1, -1, 1, 0, 0, -1, 1, -1, 1, 0)[index])

    if name == "Float":
        return _frame("Idle", direction, (0, 1, 2, 1)[index], fw, fh, dy=(0, -2, -4, -1)[index])

    if name == "DeepBreath":
        idle_frames = (0, 1, 2, 3, 2, 3, 2, 1, 0)
        return _open_face(_frame("Idle", 0, idle_frames[index], fw, fh), index)

    if name == "Nod":
        if index == 1:
            return _frame("Idle", (direction + 4) % 8, 0, fw, fh, dy=1)
        return _frame("Idle", direction, 0, fw, fh)

    if name == "Sit":
        return _frame("Walk", 0, (1, 2, 0)[index], fw, fh, dy=(0, 1, 0)[index])

    if name == "LookUp":
        return _frame("Walk", 0, (0, 1, 2)[index], fw, fh, dy=(0, -1, -2)[index])

    if name == "Sink":
        offsets = (0, 1, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20)
        return _clip_below(_frame("Walk", 0, 0, fw, fh, dy=offsets[index]), fh // 2 + 4)

    if name == "Trip":
        angles = (0, -10, -25, -45, -65)
        return _frame("Walk", direction, (0, 1, 2, 0, 1)[index], fw, fh, angle=angles[index], dx=(0, 1, 2, 2, 1)[index])

    if name == "Laying":
        return render(_sleep_frame(0, direction in (2, 3)), fw, fh)

    if name == "LeapForth":
        hop_frames = (0, 1, 2, 3, 4, 5)
        return render(source_frame("Hop", 0, hop_frames[index]), fw, fh, dy=(0, -3, -7, -8, -4, 0)[index])

    if name == "Head":
        return _head_only(direction, fw, fh)

    if name == "Cringe":
        return _frame("Hurt", 0, index, fw, fh, dy=(0, 2)[index])

    if name == "LostBalance":
        return _frame("Walk", 0, 0, fw, fh, angle=(-16, 16)[index])

    if name == "TumbleBack":
        return _frame("Walk", 0, 0, fw, fh, angle=(0, 40, 80, 120, 160, 200, 240, 280, 320, 360)[index])

    if name == "Faint":
        if index < 2:
            return _frame("Walk", direction, (1, 0)[index], fw, fh, angle=(0, -18)[index])
        return render(_sleep_frame(index - 2, direction in (2, 3)), fw, fh)

    if name == "HitGround":
        sources = (
            source_frame("Walk", 0, 1), source_frame("Walk", 0, 2),
            source_frame("Walk", 0, 0), source_frame("Sleep", 0, 0),
            source_frame("Sleep", 0, 1), source_frame("Sleep", 0, 0),
            source_frame("Walk", 0, 0), source_frame("Walk", 0, 1),
        )
        frame = render(sources[index], fw, fh, angle=(0, -12, -28, -55, -70, -70, -25, 0)[index])
        return _impact_marks(frame, index)

    raise ValueError(f"unhandled starter animation: {name}")


# The canonical Falinks shadow has a 22x8 visible marker around the center of
# its 24x24 Walk frame.  Reuse those exact PMD shadow colors at every size.
_shadow_source = Image.open(CANONICAL / "Walk-Shadow.png").convert("RGBA").crop((0, 0, 24, 24))
_shadow_box = _shadow_source.getchannel("A").getbbox()
SHADOW_TEMPLATE = _shadow_source.crop(_shadow_box) if _shadow_box else _shadow_source


def make_shadow(frame_width: int, frame_height: int) -> Image.Image:
    out = Image.new("RGBA", (frame_width, frame_height), (0, 0, 0, 0))
    cx = frame_width // 2
    cy = frame_height // 2 + 4
    out.alpha_composite(SHADOW_TEMPLATE, (cx - SHADOW_TEMPLATE.width // 2, cy - SHADOW_TEMPLATE.height // 2))
    return out


def make_offsets(art: Image.Image) -> Image.Image:
    out = Image.new("RGBA", art.size, (0, 0, 0, 0))
    box = _main_box(art)
    if box is None:
        # A fully sunk frame has no visible art, but PMD still expects the
        # four marker colors in its companion offset cell.
        center_x = art.width // 2
        center_y = art.height // 2
        box = (center_x - 1, center_y - 1, center_x + 2, center_y + 2)
    left, top, right, bottom = box
    width = max(1, right - left)
    height = max(1, bottom - top)
    points = [
        ((round(left + width * 0.50), round(top + height * 0.18)), (0, 0, 0, 255)),
        ((round(left + width * 0.50), round(top + height * 0.58)), (0, 255, 0, 255)),
        ((round(left + width * 0.22), round(top + height * 0.56)), (255, 0, 0, 255)),
        ((round(left + width * 0.78), round(top + height * 0.56)), (0, 0, 255, 255)),
    ]
    used: set[tuple[int, int]] = set()
    for (x, y), color in points:
        for candidate in ((x, y), (x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if candidate not in used and 0 <= candidate[0] < art.width and 0 <= candidate[1] < art.height:
                used.add(candidate)
                out.putpixel(candidate, color)
                break
    return out


def _append_xml(tree: ET.ElementTree) -> None:
    root = tree.getroot()
    anims = root.find("Anims")
    if anims is None:
        raise ValueError("canonical AnimData.xml has no Anims")
    for name, index, fw, fh, durations, _rows in SPECS:
        if any(a.findtext("Name") == name for a in anims):
            continue
        anim = ET.SubElement(anims, "Anim")
        ET.SubElement(anim, "Name").text = name
        ET.SubElement(anim, "Index").text = str(index)
        ET.SubElement(anim, "FrameWidth").text = str(fw)
        ET.SubElement(anim, "FrameHeight").text = str(fh)
        if name == "LeapForth":
            ET.SubElement(anim, "RushFrame").text = "1"
        durations_node = ET.SubElement(anim, "Durations")
        for duration in durations:
            ET.SubElement(durations_node, "Duration").text = str(duration)
    ordered = sorted(list(anims), key=lambda item: int(item.findtext("Index", "999")))
    anims.clear()
    anims.extend(ordered)


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
    for path in CANONICAL.iterdir():
        if path.is_file() and path.name not in {"AnimData.xml", "credits.txt"}:
            shutil.copyfile(path, OUT / path.name)
    tree = source_xml()
    _append_xml(tree)
    ET.indent(tree, space="\t")
    tree.write(OUT / "AnimData.xml", encoding="utf-8", xml_declaration=True)
    credits = (CANONICAL / "credits.txt").read_text(encoding="utf-8").rstrip() + "\n"
    credits += (
        "2026-09-17\tmeromoonmeri / Arena.ai Agent\tNEW\t"
        "RearUp, EventSleep, Wake, Eat, Tumble, Pose, Pull, Pain, Float, "
        "DeepBreath, Nod, Sit, LookUp, Sink, Trip, Laying, LeapForth, Head, "
        "Cringe, LostBalance, TumbleBack, Faint, HitGround\n"
    )
    (OUT / "credits.txt").write_text(credits, encoding="utf-8")
    for name, _index, fw, fh, durations, rows in SPECS:
        _write_animation(name, fw, fh, durations, rows)
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(OUT.iterdir()):
            if not path.is_file():
                continue
            info = zipfile.ZipInfo(path.name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    shutil.copyfile(ZIP_OUT, ZIP_ALIAS)


if __name__ == "__main__":
    build()
