"""Build native-size, game-timed GIF previews for Falinks #0870."""
from __future__ import annotations

import json
import shutil
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SPRITE_DIR = ROOT / "sprite" / "0870" / "0002"
OUT = ROOT / "gifs" / "0870" / "0002"
ZIP_OUT = ROOT / "gifs-0870-0002.zip"
ZIP_ALIAS = ROOT / "gifs-0870.zip"
TICKS_PER_SECOND = 60
MIN_DELAY_MS = 20


def delay_ms(ticks: int) -> int:
    return max(MIN_DELAY_MS, round((ticks * 1000 / TICKS_PER_SECOND) / 10) * 10)


def entries() -> list[dict[str, object]]:
    root = ET.parse(SPRITE_DIR / "AnimData.xml").getroot()
    raw: dict[str, dict[str, object]] = {}
    for anim in root.findall("./Anims/Anim"):
        name = anim.findtext("Name", "")
        copy_of = anim.findtext("CopyOf")
        if copy_of:
            raw[name] = {"name": name, "source": copy_of}
        else:
            raw[name] = {
                "name": name,
                "source": name,
                "frame_width": int(anim.findtext("FrameWidth", "0")),
                "frame_height": int(anim.findtext("FrameHeight", "0")),
                "ticks": [int(x.text or "0") for x in anim.findall("./Durations/Duration")],
            }

    def resolve(name: str, stack: tuple[str, ...] = ()) -> dict[str, object]:
        if name in stack:
            raise ValueError("CopyOf cycle")
        item = raw[name]
        if item["source"] == name:
            return dict(item)
        result = resolve(str(item["source"]), stack + (name,))
        result["name"] = name
        return result

    return [resolve(name) for name in raw]


def source_frames(item: dict[str, object]) -> list[Image.Image]:
    source = str(item["source"])
    fw, fh = int(item["frame_width"]), int(item["frame_height"])
    ticks = list(item["ticks"])  # type: ignore[arg-type]
    sheet = Image.open(SPRITE_DIR / f"{source}-Anim.png").convert("RGBA")
    return [sheet.crop((i * fw, 0, (i + 1) * fw, fh)) for i in range(len(ticks))]


def indexed_frames(frames: list[Image.Image]) -> list[Image.Image]:
    colors: list[tuple[int, int, int]] = []
    seen: set[tuple[int, int, int]] = set()
    for frame in frames:
        for r, g, b, a in frame.getdata():
            if a and (r, g, b) not in seen:
                seen.add((r, g, b))
                colors.append((r, g, b))
    if len(colors) > 255:
        raise ValueError("GIF palette overflow")
    palette = [0, 0, 0] + [c for color in colors for c in color]
    palette += [0] * (768 - len(palette))
    lookup = {color: i + 1 for i, color in enumerate(colors)}
    result = []
    for frame in frames:
        indexed = Image.new("P", frame.size, 0)
        indexed.putpalette(palette)
        indexed.putdata([0 if a == 0 else lookup[(r, g, b)] for r, g, b, a in frame.getdata()])
        indexed.info["transparency"] = 0
        result.append(indexed)
    return result


def coalesce(frames: list[Image.Image], delays: list[int]) -> tuple[list[Image.Image], list[int]]:
    out_frames = [frames[0]]
    out_delays = [delays[0]]
    for frame, delay in zip(frames[1:], delays[1:]):
        if frame.tobytes() == out_frames[-1].tobytes():
            out_delays[-1] += delay
        else:
            out_frames.append(frame)
            out_delays.append(delay)
    return out_frames, out_delays


def build_gif(item: dict[str, object]) -> dict[str, object]:
    frames = indexed_frames(source_frames(item))
    source_delays = [delay_ms(int(x)) for x in item["ticks"]]  # type: ignore[arg-type]
    frames, delays = coalesce(frames, source_delays)
    name = str(item["name"])
    frames[0].save(
        OUT / f"{name}.gif",
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=delays,
        loop=0,
        disposal=2,
        transparency=0,
        optimize=False,
    )
    return {
        "name": name,
        "file": f"{name}.gif",
        "direction": 0,
        "frame_size": [int(item["frame_width"]), int(item["frame_height"])],
        "source_frames": len(source_delays),
        "frames": len(frames),
        "duration_game_ticks": list(item["ticks"]),
        "duration_gif_ms": delays,
        "loop_gif_ms": sum(delays),
    }


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    records = [build_gif(item) for item in entries()]
    (OUT / "timing.json").write_text(json.dumps({
        "pokemon": "Falinks",
        "dex": 870,
        "variant": "0002",
        "direction": 0,
        "timing_source": "sprite/0870/0002/AnimData.xml",
        "game_ticks_per_second": TICKS_PER_SECOND,
        "gif_min_delay_ms": MIN_DELAY_MS,
        "animations": records,
    }, indent=2) + "\n", encoding="utf-8")
    (OUT / "README.md").write_text(
        "# Falinks GIF previews\n\n"
        "One native-size looping GIF per AnimData entry, direction 0 (down/front). "
        "Durations use the PMD 60 Hz clock; identical consecutive poses are "
        "coalesced without changing total time. The authoritative PMD sheets "
        "remain in `sprite/0870/0002/`.\n",
        encoding="utf-8",
    )
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(OUT.iterdir()):
            if not path.is_file():
                continue
            info = zipfile.ZipInfo(path.name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    shutil.copyfile(ZIP_OUT, ZIP_ALIAS)
    print(f"Wrote {len(records)} Falinks GIF previews to {OUT}")
    print(f"Wrote {ZIP_OUT}")


if __name__ == "__main__":
    build()
