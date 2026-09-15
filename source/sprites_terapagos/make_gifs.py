"""Build readable GIF previews for every Terapagos Stellar PMD animation.

The GIFs are previews, not a replacement for the SpriteCollab sheets.  They
show PMD direction 0 (down/front) at native pixel size and use the durations
from AnimData.xml.  PMD timing is expressed in 60 Hz game ticks; GIF timing is
rounded to 10 ms and clamped to 20 ms because browsers commonly discard
shorter GIF delays.
"""
from __future__ import annotations

import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SPRITE_DIR = ROOT / "sprite" / "1024"
OUT = ROOT / "gifs" / "1024"
ZIP_OUT = ROOT / "gifs-1024.zip"
TICKS_PER_SECOND = 60
GIF_MIN_DELAY_MS = 20


def _duration_ms(ticks: int) -> int:
    """Convert a PMD 60 Hz duration into a browser-safe GIF delay."""
    exact = ticks * 1000 / TICKS_PER_SECOND
    # GIF stores delays in centiseconds. Keep the PMD rhythm while avoiding
    # 0/10 ms delays, which many browsers play too quickly or ignore.
    return max(GIF_MIN_DELAY_MS, round(exact / 10) * 10)


def _animations() -> list[dict[str, object]]:
    root = ET.parse(SPRITE_DIR / "AnimData.xml").getroot()
    entries: dict[str, dict[str, object]] = {}
    for anim in root.findall("./Anims/Anim"):
        name = anim.findtext("Name", "")
        copy_of = anim.findtext("CopyOf")
        if copy_of:
            entries[name] = {"name": name, "source": copy_of}
            continue
        durations = [int(node.text or "0") for node in anim.findall("./Durations/Duration")]
        entries[name] = {
            "name": name,
            "source": name,
            "frame_width": int(anim.findtext("FrameWidth", "0")),
            "frame_height": int(anim.findtext("FrameHeight", "0")),
            "durations_ticks": durations,
        }

    def resolve(name: str, stack: tuple[str, ...] = ()) -> dict[str, object]:
        if name in stack:
            raise ValueError(f"CopyOf cycle: {' -> '.join(stack + (name,))}")
        entry = entries[name]
        source = str(entry["source"])
        if source == name:
            return dict(entry)
        resolved = resolve(source, stack + (name,))
        resolved["name"] = name
        return resolved

    return [resolve(name) for name in entries]


def _frames(entry: dict[str, object]) -> list[Image.Image]:
    source = str(entry["source"])
    fw = int(entry["frame_width"])
    fh = int(entry["frame_height"])
    durations = list(entry["durations_ticks"])  # type: ignore[arg-type]
    sheet = Image.open(SPRITE_DIR / f"{source}-Anim.png").convert("RGBA")
    if sheet.width < fw * len(durations) or sheet.height < fh:
        raise ValueError(f"{source}: Anim sheet is smaller than AnimData.xml")
    return [
        sheet.crop((index * fw, 0, (index + 1) * fw, fh))
        for index in range(len(durations))
    ]


def _gif_frames(frames: list[Image.Image]) -> list[Image.Image]:
    """Make all frames share one exact palette and a transparent index."""
    colors: list[tuple[int, int, int]] = []
    seen: set[tuple[int, int, int]] = set()
    for frame in frames:
        for r, g, b, a in frame.getdata():
            if a and (r, g, b) not in seen:
                seen.add((r, g, b))
                colors.append((r, g, b))
    if len(colors) > 255:
        raise ValueError(f"GIF palette overflow: {len(colors)} opaque colors")

    palette = [0, 0, 0]
    palette.extend(channel for color in colors for channel in color)
    palette.extend([0] * (768 - len(palette)))
    indices = {color: index + 1 for index, color in enumerate(colors)}
    result: list[Image.Image] = []
    for frame in frames:
        indexed = Image.new("P", frame.size, 0)
        indexed.putpalette(palette)
        indexed.putdata([
            0 if a == 0 else indices[(r, g, b)]
            for r, g, b, a in frame.getdata()
        ])
        indexed.info["transparency"] = 0
        result.append(indexed)
    return result


def _coalesce_identical(
    frames: list[Image.Image], delays: list[int]
) -> tuple[list[Image.Image], list[int]]:
    """Merge consecutive identical poses while preserving their total time."""
    if not frames:
        return [], []
    result_frames = [frames[0]]
    result_delays = [delays[0]]
    for frame, delay in zip(frames[1:], delays[1:]):
        if frame.tobytes() == result_frames[-1].tobytes():
            result_delays[-1] += delay
        else:
            result_frames.append(frame)
            result_delays.append(delay)
    return result_frames, result_delays


def _write_gif(entry: dict[str, object]) -> dict[str, object]:
    name = str(entry["name"])
    ticks = [int(value) for value in entry["durations_ticks"]]  # type: ignore[arg-type]
    frames = _frames(entry)
    indexed = _gif_frames(frames)
    source_delays = [_duration_ms(value) for value in ticks]
    indexed, delays = _coalesce_identical(indexed, source_delays)
    output = OUT / f"{name}.gif"
    indexed[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=indexed[1:],
        duration=delays,
        loop=0,
        disposal=2,
        transparency=0,
        optimize=False,
    )
    return {
        "name": name,
        "source_sheet": f"{entry['source']}-Anim.png",
        "direction": 0,
        "frame_size": [int(entry["frame_width"]), int(entry["frame_height"])],
        "source_frames": len(ticks),
        "frames": len(indexed),
        "duration_game_ticks": ticks,
        "source_duration_gif_ms": source_delays,
        "duration_gif_ms": delays,
        "loop_game_ticks": sum(ticks),
        "loop_gif_ms": sum(delays),
        "file": f"{name}.gif",
    }


def _write_readme() -> None:
    (OUT / "README.md").write_text(
        "# Terapagos Stellar — GIF previews\n\n"
        "One GIF is provided for every animation index from `AnimData.xml`, "
        "including the `Strike` copy. Each preview shows PMD direction 0 "
        "(down/front) at native pixel size and loops continuously.\n\n"
        "Timing is taken directly from the PMD animation data: one game tick "
        "is treated as 1/60 second. GIF delays are rounded to 10 ms and never "
        "go below 20 ms, the practical browser-safe minimum. Consecutive "
        "identical poses are merged with their delays added, so the visual "
        "timing stays unchanged without redundant GIF frames. The authoritative "
        "SpriteCollab sheets remain in `sprite/0186/`; these GIFs are only for "
        "visual review.\n\n"
        "Regenerate from the repository root with:\n\n"
        "```bash\n"
        "python source/sprites_politoed/make_gifs.py\n"
        "```\n",
        encoding="utf-8",
    )


def _write_zip() -> None:
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(OUT.iterdir()):
            if not path.is_file():
                continue
            info = zipfile.ZipInfo(path.relative_to(OUT).as_posix(), date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    records = [_write_gif(entry) for entry in _animations()]
    (OUT / "timing.json").write_text(
        json.dumps(
            {
                "pokemon": "Terapagos Stellar",
                "dex": 186,
                "direction": 0,
                "direction_name": "down/front",
                "timing_source": "sprite/0186/AnimData.xml",
                "game_ticks_per_second": TICKS_PER_SECOND,
                "gif_min_delay_ms": GIF_MIN_DELAY_MS,
                "animations": records,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_readme()
    _write_zip()
    print(f"Wrote {len(records)} GIF previews to {OUT}")
    print(f"Wrote {ZIP_OUT}")


if __name__ == "__main__":
    build()
