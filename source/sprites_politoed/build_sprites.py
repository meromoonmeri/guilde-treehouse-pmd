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
    ("Pose", 17, 40, 64, (8, 6, 6, 6, 8), 8),
    ("Pull", 18, 48, 64, (10, 12, 10, 12, 10, 12, 10), 1),
    ("Pain", 19, 48, 64, (4, 1, 1, 1, 2, 1, 4, 2, 2, 2, 2, 2), 8),
    ("Float", 20, 40, 64, (9, 18, 9, 14), 8),
    ("DeepBreath", 21, 40, 64, (12, 6, 6, 6, 6, 6, 6, 10, 4), 1),
    ("Nod", 22, 40, 64, (6, 8, 6), 8),
    ("Sit", 23, 40, 48, (8, 8, 8), 1),
    ("LookUp", 24, 40, 64, (6, 8, 6), 1),
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


# Exact colours already present in the canonical Politoed sprite.  These are
# used for the few semantic details that cannot be obtained by reusing a
# dungeon frame (notably the hand-to-mouth motion in Eat).
BLACK = (0, 0, 0, 255)
DARK_GREEN = (39, 135, 0, 255)
ORANGE = (223, 183, 0, 255)
YELLOW = (255, 247, 0, 255)
RED = (159, 0, 0, 255)
WHITE = (255, 255, 255, 255)
BLUE = (135, 159, 255, 255)


def _paint(frame: Image.Image, points: list[tuple[int, int]], color: tuple[int, int, int, int]) -> None:
    for x, y in points:
        if 0 <= x < frame.width and 0 <= y < frame.height:
            frame.putpixel((x, y), color)


def _draw_open_mouth(frame: Image.Image, *, y_bias: int = 0) -> Image.Image:
    """Add a small PMD-style open mouth to the current front pose."""
    frame = frame.copy()
    box = _largest_component_bbox(frame) or _bbox(frame)
    if box is None:
        return frame
    left, top, right, bottom = box
    center = round((left + right - 1) / 2)
    y = top + round((bottom - top) * 0.60) + y_bias
    _paint(frame, [(center - 3, y), (center - 2, y), (center - 1, y), (center, y),
                   (center + 1, y), (center + 2, y), (center + 3, y),
                   (center - 3, y + 1), (center + 3, y + 1)], BLACK)
    _paint(frame, [(center - 2, y + 1), (center - 1, y + 1), (center, y + 1),
                   (center + 1, y + 1), (center + 2, y + 1)], RED)
    _paint(frame, [(center - 1, y + 2), (center, y + 2), (center + 1, y + 2)], YELLOW)
    return frame


def _effort_marks(frame: Image.Image, index: int) -> Image.Image:
    """Add the small canonical white exertion marks used by PMD Pull."""
    if index not in (1, 3, 5):
        return frame
    frame = frame.copy()
    box = _largest_component_bbox(frame) or _bbox(frame)
    if box is None:
        return frame
    left, top, right, bottom = box
    y = top + round((bottom - top) * 0.42)
    marks = [
        (left - 4, y), (left - 3, y - 2), (left - 2, y - 3),
        (right + 3, y), (right + 2, y - 2), (right + 1, y - 3),
    ]
    _paint(frame, marks, WHITE)
    return frame


def _ground_impact(frame: Image.Image, index: int) -> Image.Image:
    """Draw restrained PMD impact pixels when the body meets the floor."""
    if index not in (3, 4, 5):
        return frame
    frame = frame.copy()
    box = _largest_component_bbox(frame) or _bbox(frame)
    if box is None:
        return frame
    left, _top, right, bottom = box
    center = round((left + right - 1) / 2)
    marks = [
        (left - 3, bottom), (left - 2, bottom + 1),
        (right + 2, bottom), (right + 1, bottom + 1),
        (center - 5, bottom + 2), (center + 5, bottom + 2),
    ]
    _paint(frame, marks[:4], WHITE)
    _paint(frame, marks[4:], BLUE)
    return frame


def _head_only(direction: int, fw: int, fh: int) -> Image.Image:
    """Use only Politoed's head for the official PMD Head expression."""
    source = _dir_image("Idle", direction, 0)
    box = _largest_component_bbox(source) or _bbox(source)
    if box is None:
        return Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
    _left, top, _right, bottom = box
    # The canonical Politoed pose is 24 pixels tall.  The upper fifteen
    # pixels contain crest, eyes and mouth; the lower pixels are the body and
    # feet that must not appear in Head.
    head_bottom = min(bottom, top + 15)
    head = source.crop((0, top, source.width, head_bottom))
    return render(head, fw, fh, dy=-10)


def _eat_details(frame: Image.Image, index: int) -> Image.Image:
    """Make the four Eat frames read as feed, open, chew, and reset."""
    frame = frame.copy()
    # Frame 1: both hands are raised toward the mouth while it opens.
    # Frame 2: hands stay near the cheeks and the mouth closes to chew.
    # Frame 3: the mouth opens once more, then the loop returns to frame 0.
    if index in (1, 3):
        _paint(frame, [(17, 23), (18, 23), (19, 23), (20, 23), (21, 23), (22, 23),
                       (16, 24), (23, 24), (16, 25), (23, 25),
                       (17, 26), (18, 26), (19, 26), (20, 26), (21, 26), (22, 26)], BLACK)
        _paint(frame, [(18, 24), (19, 24), (20, 24), (21, 24),
                       (18, 25), (19, 25), (20, 25), (21, 25)], RED)
        _paint(frame, [(19, 26), (20, 26)], YELLOW)
        if index == 1:
            # The hands visibly travel inward instead of staying in the attack
            # pose: the yellow tips nearly touch the mouth at x=16 and x=23.
            left = [(11, 24), (12, 23), (13, 22), (14, 22), (15, 22), (16, 23)]
            right = [(28, 24), (27, 23), (26, 22), (25, 22), (24, 22), (23, 23)]
        else:
            # Release the hands after the chew while keeping the mouth open for
            # the last beat of the loop.
            left = [(10, 25), (11, 24), (12, 23), (13, 23), (14, 24)]
            right = [(29, 25), (28, 24), (27, 23), (26, 23), (25, 24)]
        _paint(frame, left + right, YELLOW)
    elif index == 2:
        _paint(frame, [(17, 24), (18, 24), (19, 24), (20, 24), (21, 24), (22, 24)], DARK_GREEN)
        _paint(frame, [(19, 25), (20, 25)], ORANGE)
        _paint(frame, [(12, 22), (13, 22), (14, 23), (25, 23), (26, 22), (27, 22)], YELLOW)
    return frame


def make_starter_frame(name: str, direction: int, index: int, fw: int, fh: int) -> Image.Image:
    """Author one frame of one starter animation from canonical Politoed art."""
    # The four side/diagonal rows retain Politoed's curled asymmetry by using
    # their real direction instead of mirroring a front-facing source.
    if name == "EventSleep":
        return render(_sleep_frame(index, direction in (2, 3)), fw, fh)

    if name == "Wake":
        # Wake ends in a front/side idle pose, never in Idle's rear-facing
        # transition frame.
        source = _sleep_frame(index, direction in (2, 3)) if index < 2 else _dir_image("Idle", direction, min(index - 2, 3))
        return render(source, fw, fh, dy=(-2 if index == 1 else 0))

    if name == "Eat":
        # Match the proven PMD starter choreography: neutral, reach to mouth,
        # chew, release. Eat is a grounded action; it must not become a hop.
        attack_frames = (0, 2, 5, 11)
        dips = (0, 1, 1, 0)
        base = _frame("Attack", 0, attack_frames[index], fw, fh, dy=dips[index])
        return _eat_details(base, index)

    if name == "Tumble":
        angles = (0, 45, 90, 135, 180, 225, 270, 315)
        return _frame("Walk", 0, 0, fw, fh, angle=angles[index])

    if name == "Pose":
        # Use the existing Politoed RearUp hand-wave as the actual drawing
        # reference.  This gives Pose raised, readable arms instead of an
        # Attack frame with a few detached yellow pixels.
        if index == 0:
            return _frame("Idle", direction, 0, fw, fh)
        return _frame("RearUp", direction, index - 1, fw, fh, dy=-1 if index >= 2 else 0)

    if name == "Pull":
        # Official PMD Pull poses show the character from behind while it
        # leans against a heavy object.  Alternate canonical rear Walk poses
        # and add the same small white effort marks used by SpriteCollab.
        walk_frames = (1, 0, 1, 0, 1, 0, 0)
        frame = _frame("Walk", 4, walk_frames[index], fw, fh, dy=(0, 1, 0, 1, 0, 1, 0)[index])
        return _effort_marks(frame, index)

    if name == "Pain":
        hurt_frame = (0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1)[index]
        shifts = (0, -1, 1, -1, 1, 0, 0, -1, 1, -1, 1, 0)
        return _frame("Hurt", direction, hurt_frame, fw, fh, dx=shifts[index])

    if name == "Float":
        offsets = (0, -3, -5, -2)
        return _frame("Idle", direction, (0, 1, 2, 1)[index], fw, fh, dy=offsets[index])

    if name == "DeepBreath":
        # Idle frame 4 is a rear-facing transition, so it must not appear in
        # a yawn/breath cycle. Keep the face toward the camera throughout.
        idle_frames = (0, 1, 2, 3, 2, 3, 2, 1, 0)
        scales = (100, 101, 103, 105, 103, 101, 100, 100, 100)
        frame = _frame("Idle", 0, idle_frames[index], fw, fh, scale_x=scales[index], scale_y=scales[index])
        return _draw_open_mouth(frame, y_bias=(1 if index in (2, 3, 4, 5) else 0)) if index in (2, 3, 4, 5) else frame

    if name == "Nod":
        # A nod is a front pose, a lowered/hidden head, then the same front
        # pose again.  Turning the middle frame away mirrors the official PMD
        # starter timing without inventing a new silhouette.
        if index == 1:
            return _frame("Idle", (direction + 4) % 8, 0, fw, fh, dy=1)
        return _frame("Idle", direction, 0, fw, fh)

    if name == "Sit":
        # Stand, lower the body, then settle into Politoed's compact crouch.
        sources = (1, 2, 5)
        scales = (100, 96, 88)
        return _frame("Walk", 0, sources[index], fw, fh, scale_y=scales[index], dy=(0, 1, 0)[index])

    if name == "LookUp":
        # Rise through the existing front Walk poses instead of showing an
        # unrelated rear-facing direction.  The increasing vertical lift
        # makes the head look upward while preserving Politoed's anatomy.
        sources = (0, 1, 2)
        return _frame("Walk", 0, sources[index], fw, fh, dy=(0, -1, -2)[index])

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
        return _head_only(direction, fw, fh)

    if name == "Cringe":
        return _frame("Hurt", 0, index, fw, fh, dy=(0, 3)[index], scale_y=(100, 90)[index])

    if name == "LostBalance":
        return _frame("Walk", 0, 0, fw, fh, angle=(-18, 18)[index])

    if name == "TumbleBack":
        angles = (0, 40, 80, 120, 160, 200, 240, 280, 320, 360)
        return _frame("Walk", 0, 0, fw, fh, angle=angles[index])

    if name == "Faint":
        # Faint ends in the canonical curled Sleep pose, as in the official
        # starter animations, rather than stopping half-way through a spin.
        if index < 2:
            return _frame("Walk", direction, (1, 5)[index], fw, fh,
                          angle=(0, -18)[index], scale_y=(100, 96)[index])
        sleeping = _sleep_frame(index - 2, direction in (2, 3))
        return render(sleeping, fw, fh, dy=1 if index == 2 else 0)

    if name == "HitGround":
        # Forward fall: upright, pitch forward, make contact, lie still, then
        # begin the recovery.  The impact marks are deliberately detached
        # from the body so PMD offsets continue to describe the sprite itself.
        sources = (
            source_frame("Walk", 0, 1), source_frame("Walk", 0, 2),
            source_frame("Walk", 0, 5), source_frame("Sleep", 0, 0),
            source_frame("Sleep", 0, 1), source_frame("Sleep", 0, 0),
            source_frame("Walk", 0, 5), source_frame("Walk", 0, 0),
        )
        angles = (0, -12, -30, -58, -72, -72, -28, 0)
        scales = (100, 98, 94, 90, 88, 88, 94, 100)
        frame = render(sources[index], fw, fh, angle=angles[index], scale_y=scales[index])
        return _ground_impact(frame, index)

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
