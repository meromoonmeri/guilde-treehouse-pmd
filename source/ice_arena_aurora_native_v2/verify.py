"""File/math audits only. Does not launch PMDO, execute ARM or emulate a DS GPU."""
from pathlib import Path
import bisect
import hashlib
import io
import json
import struct

import numpy as np
from PIL import Image
from skytemple_files.common.types.file_types import FileType

from build import ROOT, SOURCE, OUT, OLD, REF, PREFIX, SIZE, PARTS, coefficients, compose, native_layers


def main():
    results = []
    def check(name, condition, detail=""):
        assert condition, name
        results.append({"check": name, "status": "PASS", "detail": detail})

    sources = json.loads((SOURCE / "references/sources.json").read_text())
    for row in sources["sources"] + sources["pmdo_sources"]:
        raw = (SOURCE / "references" / row["local"]).read_bytes()
        git_blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        check("Pinned source: " + row["path"], hashlib.sha256(raw).hexdigest() == row["sha256"] and git_blob == row["git_blob"])
    lower_im, upper_im = native_layers()
    check("Native BPC0 equals user reference, every RGBA pixel", upper_im.tobytes() == Image.open(ROOT / "aurorepmdsky.png").convert("RGBA").tobytes())
    bpc = FileType.BPC.deserialize((REF / "files/MAP_BG/v38p05a.bpc").read_bytes())
    check("Exactly two layers, no BPA tile animation", bpc.number_of_layers == 2 and all(not any(layer.bpas) for layer in bpc.layers))
    bpl = FileType.BPL.deserialize((REF / "files/MAP_BG/v38p05a.bpl").read_bytes())
    check("No native palette animation", not bpl.has_palette_animation)

    timeline = json.loads((OUT / "timeline.json").read_text())
    samples, states = timeline["samples"], timeline["states"]
    check("240 samples and 33 coefficient pairs", len(samples) == 240 and len(states) == 33)
    # Independent stateful transcription of the two HandleFades branches.
    updates = []
    for target in (-256, 0):
        remaining = 120
        while remaining:
            remaining -= 1
            value = target + (256 * remaining // 120) if target < 0 else -(256 * remaining // 120)
            engine = max(0, min(128, (value + 256) // 2))
            updates.append((value, engine // 8, (128 - engine) // 8))
    cyclic = updates[-1:] + updates[:-1]
    actual = [(r["fade_value"], r["eva"], r["evb"]) for r in samples]
    check("All ticks match independent decrementing fade-state model", actual == cyclic)
    check("Period and seam are cyclic, with no repeated endpoint added", all(coefficients(t) == coefficients(t + 240) for t in range(-240, 480)))
    check("Native independent coefficient quantization retained", {r["eva"] + r["evb"] for r in samples} == {15, 16})
    check("4,000 ms WebP timing, nominal 60 ticks/s", sum(r["preview_ms"] for r in samples) == 4000)

    preserved = json.loads((OUT / "preserved_v1_layers.json").read_text())
    static = []
    for row in preserved:
        source, copied = ROOT / row["original"], OUT / row["copy"]
        check("V1 byte preservation: " + source.name, source.read_bytes() == copied.read_bytes() and hashlib.sha256(copied.read_bytes()).hexdigest() == row["sha256"])
        static.append(Image.open(copied).convert("RGBA"))
    check("All eight V1 static layers retained", len(static) == 8)

    upper = np.asarray(upper_im).astype(np.uint16)
    lower = np.asarray(lower_im).astype(np.uint16)
    full, parts = [], {p: [] for p in PARTS}
    foreground = Image.new("RGBA", (512, 720))
    for image in static[3:]:
        foreground.alpha_composite(image)
    fg = np.asarray(foreground)
    mask = fg[:, :, 3] == 255
    outside = np.ones((720, 512), dtype=bool)
    outside[:216, 120:384] = False
    old_scene = np.asarray(Image.open(OLD / "review/scene_00.png").convert("RGBA"))
    for state in states:
        image = Image.open(OUT / state["file"]).convert("RGBA")
        full.append(image)
        expected = ((upper[:, :, :3] * state["eva"] + lower[:, :, :3] * state["evb"]) // 16).astype(np.uint8)
        assert np.array_equal(np.asarray(image)[:, :, :3], expected)
        reconstructed = Image.new("RGBA", SIZE)
        for part in PARTS:
            filename = Path(state["file"]).name.replace("_BGComposite.png", "_" + part + ".png")
            component = Image.open(OUT / "frames" / part / filename).convert("RGBA")
            parts[part].append(component)
            reconstructed.alpha_composite(component)
            a = np.asarray(component)
            assert set(np.unique(a[:, :, 3])).issubset({0, 255})
            assert not np.any(a[a[:, :, 3] == 0, :3])
            if part != "Sky":
                # Flat sky is never baked into the non-sky component PNGs.
                visible = a[:, :, 3] > 0
                assert not np.any(np.all(a[:, :, :3][visible] == np.asarray(image)[0, 0, :3], axis=1))
        assert reconstructed.tobytes() == image.tobytes()
        scene = np.asarray(compose(image, static))
        assert np.array_equal(scene[mask], fg[mask])
        assert np.array_equal(scene[outside], old_scene[outside])
    check("Every exported state uses only same-XY native RGB8 weighted by EVA/EVB", True, "No displacement, recolor curve, scale, rotation, wrap or invented frame.")
    check("All 165 separated component PNGs recompose the 33 complete BG states exactly", True)
    check("Non-sky components contain no opaque flat-sky matte", True)
    check("All components are binary-alpha and correctly premultiplied for .dir", True)
    check("Every opaque terrain pixel is unchanged at every state", True)
    check("All pixels outside native BG rectangle equal V1 at every state", True)
    check("Both animation endpoints preserve original BPL RGB8 exactly", full[samples[0]["state"]].tobytes() == upper_im.tobytes() and full[samples[120]["state"]].tobytes() == lower_im.tobytes())

    recipes = json.loads((OUT / "pmdo/placement_recipe.json").read_text())
    bgroot = OUT / "pmdo/Content/BG"
    for name, images in {"BGComposite": full, **parts}.items():
        path = bgroot / (PREFIX + "_" + name + ".dir")
        raw = path.read_bytes(); length, = struct.unpack_from("<q", raw)
        header = struct.unpack_from("<4i", raw, 8 + length)
        assert header == (264, 216, 0, 240)
        assert len(raw) == 8 + length + 16
        atlas = Image.open(io.BytesIO(raw[8:8 + length])).convert("RGBA")
        assert atlas.size == (3960, 3456)
        for t, row in enumerate(samples):
            x, y = (t % 15) * 264, (t // 15) * 216
            assert atlas.crop((x, y, x + 264, y + 216)).tobytes() == images[row["state"]].tobytes()
        check("PMDO .dir header and all 240 frame slots: " + name, True, "Binary/PNG reader check; NOT native GPU load.")
    for option in recipes["choose_one"].values():
        for bg in option:
            assert bg["BGMovement"] == {"X": 0, "Y": 0} and not bg["RepeatX"] and not bg["RepeatY"]
            assert bg["BGAnim"]["FrameTime"] == 1 and bg["BGAnim"]["StartFrame"] == 0 and bg["BGAnim"]["EndFrame"] == 239
            assert (bgroot / (bg["BGAnim"]["AnimIndex"] + ".dir")).is_file()
    check("PMDO recipes: names resolve, 240-frame loop, one tick per frame, no scroll/wrap", True)

    times = [0]
    for row in samples:
        times.append(times[-1] + row["preview_ms"])
    for name, ims in [("background", full), ("scene", [compose(im, static) for im in full])]:
        movie = Image.open(OUT / "review" / (name + ".webp"))
        elapsed = 0
        for i in range(movie.n_frames):
            movie.seek(i); movie.load()
            duration = movie.info["duration"]
            start_tick = bisect.bisect_right(times, elapsed) - 1
            # A WebP encoder may merge adjacent identical images, but not time or pixels.
            for t in range(start_tick, 240):
                if times[t] >= elapsed + duration:
                    break
                assert movie.convert("RGBA").tobytes() == ims[samples[t]["state"]].tobytes()
            elapsed += duration
        check("Lossless WebP pixels and complete timeline: " + name, elapsed == 4000 and movie.info.get("loop") == 0,
              f"{movie.n_frames} encoded frames after identical-frame merging")

    manifest = json.loads((OUT / "manifest.json").read_text())
    check("Testing and color-port limits are explicit", not manifest["native_game_capture"] and not manifest["PMDO_gpu_or_gameplay_validated"] and "RGB555" in manifest["color_port"])
    report = {"status": "PASS", "count": len(results), "checks": results,
              "method": "Pinned-file hashes, source-derived math models, PNG composition and .dir container/slot audits",
              "native_ARM_executed": False, "DS_emulator_tested": False, "PMDO_runtime_tested": False,
              "PMDO_GPU_tested": False, "collision_or_gameplay_tested": False}
    (OUT / "audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    files = {str(p.relative_to(OUT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.rglob("*"))
             if p.is_file() and p.name != "files.sha256.json"}
    (OUT / "files.sha256.json").write_text(json.dumps(files, indent=2) + "\n")
    print(f"{len(results)} checks PASS. No emulator, PMDO runtime/GPU, collision or gameplay validation claimed.")


if __name__ == "__main__":
    main()
