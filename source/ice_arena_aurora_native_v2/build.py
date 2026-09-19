"""V1 layout + recovered native aurora controls; RGB8 PMDO port, not a DS capture.
No generated imagery, warping, rescaling, scrolling, invented palette or new terrain.
Run from any directory: .venv/bin/python source/ice_arena_aurora_native_v2/build.py
"""
from pathlib import Path
import base64
import hashlib
import io
import json
import shutil
import struct
from importlib.metadata import version

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from skytemple_files.common.types.file_types import FileType
from skytemple_files.common.ppmdu_config.xml_reader import Pmd2XmlReader

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).resolve().parent
OUT = ROOT / "exports/ice_arena_aurora_native_v2"
OLD = ROOT / "exports/ice_arena_aurora_v1"
REF = SOURCE / "references/pret"
PREFIX = "IceAuroraNativeV2"
ORIGIN = (120, 0)
SIZE = (264, 216)
CANVAS = (512, 720)
TICKS = 240
PARTS = ["Sky", "Ribbons", "Stars", "Haze", "DistantIce"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def coefficients(tick):
    """Cyclic phase zero is the preceding fade-in endpoint, not a cutscene timestamp.
    HandleFades uses integer division on positive delta * remaining / duration.
    The first half targets -256; the second targets zero. Hardware coefficients
    are independently truncated from the complementary 0..128 engine values.
    """
    t = tick % TICKS
    value = -256 + 256 * (120 - t) // 120 if t <= 120 else -(256 * (240 - t) // 120)
    a128 = min(128, max(0, (value + 256) // 2))
    return value, (a128 & 0xF8) >> 3, ((128 - a128) & 0xF8) >> 3


def native_layers():
    base = REF / "files/MAP_BG"
    bma = FileType.BMA.deserialize((base / "v38p05a.bma").read_bytes())
    bpc = FileType.BPC.deserialize((base / "v38p05a.bpc").read_bytes())
    bpl = FileType.BPL.deserialize((base / "v38p05a.bpl").read_bytes())
    assert not bpl.has_palette_animation
    # SkyTemple's layer 0 = lower/BPC layer 1; layer 1 = upper/BPC layer 0.
    layers = [bma.to_pil_single_layer(bpc, bpl.palettes, [None] * 8, i) for i in (0, 1)]
    assert all(im.size == SIZE for im in layers)
    assert all(not np.any(np.asarray(im) % 16 == 0) for im in layers), "Unexpected transparent native pixel"
    return tuple(im.convert("RGBA") for im in layers)


def blend_rgb8(upper, lower, a, b):
    """Native EVA/EVB on original BPL RGB8. Deliberately NOT an RGB555/LCD emulator.
    This preserves both unblended source images exactly, including 7/15/... values.
    In-between colors result only from the recorded native blend coefficients.
    """
    rgb = (upper[:, :, :3].astype(np.uint16) * a + lower[:, :, :3].astype(np.uint16) * b) // 16
    rgba = np.empty(upper.shape, dtype=np.uint8)
    rgba[:, :, :3] = np.minimum(rgb, 255)
    rgba[:, :, 3] = 255
    return Image.fromarray(rgba)


def separation_masks(upper, lower):
    """Editorial masks, not recovered native sublayers. Recomposition is exact.
    Reuse the V1 distant-ice mask. Label small native sky components as stars;
    where the other drawing has a ribbon over a star, keep that overlap in Ribbons.
    No hidden pixels or star positions are reconstructed.
    """
    old_parts = ROOT / "exports/zones_relayout_v2/aurora"
    ice = np.asarray(Image.open(old_parts / "ZonesV2_aurora_05_ice_foreground.png").convert("RGBA"))[:, :, 3] > 0
    yy = np.indices((SIZE[1], SIZE[0]))[0]
    stars, ribbons = [], []
    for image in (upper, lower):
        different = np.any(image[:, :, :3] != image[0, 0, :3], axis=2)
        labels, _ = ndimage.label(different & ~ice & (yy < 150))
        counts = np.bincount(labels.ravel())
        star = (labels > 0) & np.isin(labels, np.flatnonzero((counts > 0) & (counts <= 16)))
        stars.append(star)
        ribbons.append(different & ~star & ~ice & (yy < 152))
    star = (stars[0] | stars[1]) & ~(ribbons[0] | ribbons[1])
    haze = ~ice & (yy >= 152)
    ribbon = ~ice & ~star & ~haze
    return [ribbon, star, haze, ice]


def split_frame(frame, masks):
    a = np.asarray(frame)
    sky = Image.new("RGBA", SIZE, tuple(a[0, 0]))
    different = np.any(a[:, :, :3] != a[0, 0, :3], axis=2)
    result = [sky]
    for mask in masks:
        part = np.zeros_like(a)
        use = different & mask
        part[use] = a[use]
        result.append(Image.fromarray(part))
    check = Image.new("RGBA", SIZE)
    for image in result:
        check.alpha_composite(image)
    assert check.tobytes() == frame.tobytes()
    return result


def save_dir(path, unique_frames, timeline):
    # 15x16 slots keeps both atlas dimensions below 4096; source pixels stay 1:1.
    atlas = Image.new("RGBA", (SIZE[0] * 15, SIZE[1] * 16))
    for t, row in enumerate(timeline):
        atlas.paste(unique_frames[row["state"]], ((t % 15) * SIZE[0], (t // 15) * SIZE[1]))
    # Alpha is binary in our separated frames, so RGB is already premultiplied.
    stream = io.BytesIO()
    atlas.save(stream, format="PNG", compress_level=9)
    raw = stream.getvalue()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(struct.pack("<q", len(raw)) + raw + struct.pack("<4i", *SIZE, 0, TICKS))


def compose(frame, static):
    image = static[0].copy()
    image.alpha_composite(frame, ORIGIN)
    # The complete native BG replaces old separate haze/ice and authored effects.
    # The five foreground/terrain layers are copied and drawn without alteration.
    for layer in static[3:]:
        image.alpha_composite(layer)
    return image


def background_recipe(name):
    return {"$type": "RogueEssence.Dungeon.MapBG, RogueEssence", "MapLoc": {"X": 120, "Y": 0},
            "BGAnim": {"AnimIndex": PREFIX + "_" + name, "FrameTime": 1, "StartFrame": 0,
                       "EndFrame": 239, "AnimDir": -1, "Alpha": 255, "AnimFlip": 0},
            "BGMovement": {"X": 0, "Y": 0}, "Parallax": "1, 1", "RepeatX": False, "RepeatY": False}


def build():
    for folder in ["static", "native_layers", "frames/BGComposite", *["frames/" + p for p in PARTS], "review"]:
        (OUT / folder).mkdir(parents=True, exist_ok=True)
    sources = json.loads((SOURCE / "references/sources.json").read_text())
    for row in sources["sources"]:
        assert sha(SOURCE / "references" / row["local"]) == row["sha256"]
    lower_im, upper_im = native_layers()
    original = Image.open(ROOT / "aurorepmdsky.png").convert("RGBA")
    assert original.tobytes() == upper_im.tobytes(), "Native upper layer must equal user reference"
    lower_im.save(OUT / "native_layers" / f"{PREFIX}_BG3_Lower.png")
    upper_im.save(OUT / "native_layers" / f"{PREFIX}_BG2_Upper.png")
    upper, lower = np.asarray(upper_im), np.asarray(lower_im)
    assert np.array_equal(upper[0, 0], lower[0, 0])
    masks = separation_masks(upper, lower)

    script = FileType.SSB.deserialize((REF / "files/language-specific/EU/SCRIPT/D52P32A/n09a1207.ssb").read_bytes(),
                                     static_data=Pmd2XmlReader.load_default())
    ops = script.get_filled_routine_ops()[2]
    script_ops = [{"offset": op.offset, "opcode": op.op_code.name, "params": [str(p) for p in op.params]} for op in ops]
    dump(OUT / "native_script_routine2.json", script_ops)
    effects = [(op.op_code.name, list(op.params)) for op in ops if op.op_code.name in ("back2_SetEffect", "Wait")]
    assert effects == [("back2_SetEffect", [5, 120]), ("Wait", [120]), ("back2_SetEffect", [3, 120]), ("Wait", [120])]

    static, preservation = [], []
    for old in sorted((OLD / "static").glob("*.png")):
        dst = OUT / "static" / old.name.replace("IceAuroraV1", PREFIX)
        shutil.copyfile(old, dst)
        static.append(Image.open(dst).convert("RGBA"))
        preservation.append({"original": str(old.relative_to(ROOT)), "copy": str(dst.relative_to(OUT)),
                             "sha256": sha(old), "identical_bytes": old.read_bytes() == dst.read_bytes()})
    assert len(static) == 8
    dump(OUT / "preserved_v1_layers.json", preservation)

    states, ids, timeline, full_frames, components = [], {}, [], [], {p: [] for p in PARTS}
    for t in range(TICKS):
        value, a, b = coefficients(t)
        pair = (a, b)
        if pair not in ids:
            index = len(states)
            ids[pair] = index
            frame = blend_rgb8(upper, lower, a, b)
            stem = f"{PREFIX}_a{a:02}_b{b:02}"
            states.append({"id": index, "eva": a, "evb": b, "file": f"frames/BGComposite/{stem}_BGComposite.png"})
            frame.save(OUT / states[-1]["file"])
            full_frames.append(frame)
            for part, image in zip(PARTS, split_frame(frame, masks)):
                image.save(OUT / "frames" / part / f"{stem}_{part}.png")
                components[part].append(image)
        timeline.append({"tick": t, "fade_value": value, "eva": a, "evb": b, "state": ids[pair],
                         "preview_ms": round((t + 1) * 1000 / 60) - round(t * 1000 / 60)})
    assert len(states) == 33
    dump(OUT / "timeline.json", {"ticks": 240, "nominal_port_fps": 60, "phase_origin": "preceding fade-in endpoint",
                                  "states": states, "samples": timeline})

    for name, images in {"BGComposite": full_frames, **components}.items():
        save_dir(OUT / "pmdo/Content/BG" / f"{PREFIX}_{name}.dir", images, timeline)
    recipes = {"schema": "placement_recipe_NOT_a_Ground_file", "target": "PMDO 0.8.12", "origin_px": ORIGIN,
               "choose_one": {"one_complete_BG": [background_recipe("BGComposite")],
                              "five_editable_components": [background_recipe(p) for p in PARTS]},
               "render_order": ["static/01_dark_sky", "chosen native BG option", "static/04 through 08"],
               "disable_old_effects": ["IceAuroraV1_Ribbons", "IceAuroraV1_Stars"],
               "old_static_02_03": "Retained as byte-identical files; replaced in rendering by native BG components, do not double-draw.",
               "collision": "NOT PROVIDED", "runtime_tested": False}
    dump(OUT / "pmdo/placement_recipe.json", recipes)

    scenes = [compose(f, static) for f in full_frames]
    durations = [row["preview_ms"] for row in timeline]
    for name, images in [("scene", scenes), ("background", full_frames)]:
        seq = [images[row["state"]] for row in timeline]
        seq[0].save(OUT / "review" / f"{name}.webp", save_all=True, append_images=seq[1:],
                    duration=durations, loop=0, lossless=True, method=6)
    scenes[timeline[0]["state"]].save(OUT / "review/scene_upper.png")
    scenes[timeline[120]["state"]].save(OUT / "review/scene_lower.png")
    board = Image.new("RGB", (528, 240), "#0e1d30")
    draw = ImageDraw.Draw(board)
    draw.text((8, 6), "BG2 / BPC0 - upper, original V1", fill="white")
    draw.text((272, 6), "BG3 / BPC1 - lower, native alternate", fill="white")
    board.paste(upper_im, (0, 24)); board.paste(lower_im, (264, 24))
    board.save(OUT / "review/native_pair.png")

    report = {"title": "V1 layout / recovered native aurora mechanism", "layout": [512, 720], "BG_size": SIZE,
              "BG_origin": ORIGIN, "grid_px": 8, "native_source": "v38p05a", "native_source_match": "RGBA exact with aurorepmdsky.png",
              "animation": "Two native BPC drawings, effect 5/3, 120 ticks each; no geometric motion or palette animation.",
              "ticks": 240, "unique_coefficient_pairs": 33, "nominal_preview_seconds": 4,
              "color_port": "Original BPL RGB8; floor((upper*EVA + lower*EVB)/16), NOT bit-exact DS RGB555/LCD rendering.",
              "coefficient_note": "EVA and EVB independently quantized by the native code: sum can be 15, not always 16. Do not normalize.",
              "layers": "Two actual native opaque BPC layers; five editorial separated components recompose every port frame exactly.",
              "stars": "Native drawings/blend replace old invented twinkle; overlapping stars/ribbons remain together in Ribbons.",
              "terrain": "Eight original static files copied byte-for-byte; five foreground terrain layers remain active and unchanged.",
              "generator_used": False, "resampling": False, "wrap": False, "native_game_capture": False,
              "PMDO_gpu_or_gameplay_validated": False, "collision_validated": False, "art_approval": "pending",
              "sources_manifest": "../../source/ice_arena_aurora_native_v2/references/sources.json",
              "dependencies": {p: version(p) for p in ["Pillow", "numpy", "scipy", "skytemple-files"]}}
    dump(OUT / "manifest.json", report)
    make_viewer(states, timeline, components, static)
    print(f"Built {len(states)} states, 240 ticks, 6 PMDO BG assets and 5 separate animated components.")


def make_viewer(states, timeline, components, static):
    def uri(image):
        b = io.BytesIO(); image.save(b, format="PNG")
        return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()
    data = {"timeline": timeline, "parts": {p: [uri(i) for i in ims] for p, ims in components.items()},
            "static": [uri(i) for i in static], "states": states}
    template = (SOURCE / "viewer.html").read_text()
    (OUT / "review/index.html").write_text(template.replace("__DATA__", json.dumps(data)))


if __name__ == "__main__":
    build()
