#!/usr/bin/env python3
"""Build a reproducible inventory of public PMUniverse graphical resources.

The manifest deliberately stores provenance and hashes, not third-party pixels.
By default this script only reads GitHub metadata.  Supplying --checkout-root
adds SHA-256 digests from local, commit-verified checkouts and inspects ZIP
central directories without extracting their contents.

Requires: Python 3.9+ and the authenticated GitHub CLI (gh).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import urllib.parse
import zipfile
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

ORG = "PMUniverse"
# Kept explicit so an audit cannot silently classify an unfamiliar binary as art.
DIRECT_VISUAL_EXTENSIONS = {
    ".png": "raster_png",
    ".gif": "animated_raster",
    ".jpg": "raster_jpeg",
    ".jpeg": "raster_jpeg",
    ".bmp": "raster_bmp",
    ".ico": "icon",
    ".pdn": "paintdotnet_source",
}
CONTAINER_EXTENSIONS = {
    ".tile": "pmu_tileset_container",
    ".sprite": "pmu_sprite_container",
    ".portrait": "pmu_portrait_container",
}
FONT_EXTENSIONS = {".ttf": "font_truetype", ".otf": "font_opentype"}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
VERIFIED_CHECKOUTS: set[tuple[Path, str, str]] = set()


def run(command: list[str]) -> bytes:
    """Run a local command and show its stderr on a failure."""
    completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode:
        sys.stderr.buffer.write(completed.stderr)
        raise RuntimeError("command failed: " + " ".join(command))
    return completed.stdout


def api_json(route: str) -> Any:
    return json.loads(run(["gh", "api", route]).decode("utf-8"))


def api_json_pages(route: str) -> list[Any]:
    """Fetch every REST list page without relying on optional gh extensions.

    GitHub's REST list endpoints accept a maximum of 100 results per page.  Asking
    for an extra page whenever a page is full protects the audit from silently
    stopping at the first 100 records.
    """
    page = 1
    entries: list[Any] = []
    separator = "&" if "?" in route else "?"
    while True:
        values = api_json(f"{route}{separator}page={page}")
        if not isinstance(values, list):
            raise RuntimeError(f"unexpected paginated API response for {route}")
        entries.extend(values)
        if len(values) < 100:
            return entries
        page += 1


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def classify(path: str) -> tuple[str, str] | None:
    """Return (scope, format) for every file germane to the asset audit."""
    lower_path = path.lower()
    suffix = Path(lower_path).suffix
    if suffix in DIRECT_VISUAL_EXTENSIONS:
        return "direct_visual", DIRECT_VISUAL_EXTENSIONS[suffix]
    if suffix in CONTAINER_EXTENSIONS:
        return "visual_container", CONTAINER_EXTENSIONS[suffix]
    if suffix in FONT_EXTENSIONS:
        return "typography", FONT_EXTENSIONS[suffix]
    if suffix == ".dat" and "/mapdata/" in lower_path:
        return "map_data", "pmu_map_data"
    if suffix == ".resx":
        return "resource_descriptor", "dotnet_resx"
    if suffix == ".zip":
        return "archive_review", "zip_archive"
    return None


def provenance_note(repo_name: str, scope: str) -> str:
    if repo_name in {"PMU-Client", "PMU-Server"}:
        if scope in {"direct_visual", "visual_container", "typography", "map_data"}:
            return (
                "PMU resource. The repository carries an MIT source-code license, "
                "but Asset Credits.txt attributes groups of sprites/audio to PMU "
                "contributors and third-party sites; no per-file reuse grant was found."
            )
        return "PMU repository file; inspect before redistributing."
    if repo_name == "Installer":
        return (
            "Installer resource. The repository is GPL-3.0; no individual artwork "
            "provenance or separate asset license was found in the audited tree."
        )
    return "No graphical asset attribution or separate asset license was found."


def verified_checkout(checkout_root: Path, repo_name: str, commit: str) -> Path:
    checkout = checkout_root / repo_name
    if not checkout.exists():
        raise RuntimeError(f"missing local checkout: {checkout}")
    marker = (checkout_root.resolve(), repo_name, commit)
    if marker not in VERIFIED_CHECKOUTS:
        head = run(["git", "-C", str(checkout), "rev-parse", "HEAD"]).decode().strip()
        if head != commit:
            raise RuntimeError(f"{checkout} is at {head}, expected audited commit {commit}")
        VERIFIED_CHECKOUTS.add(marker)
    return checkout


def local_sha(checkout_root: Path | None, repo_name: str, commit: str, path: str) -> str | None:
    if checkout_root is None:
        return None
    file_path = verified_checkout(checkout_root, repo_name, commit) / path
    if not file_path.is_file():
        raise RuntimeError(f"missing checked-out blob: {file_path}")
    return sha256(file_path)


def png_streams(data: bytes) -> list[tuple[int, int, int]]:
    """Locate raw PNG streams and read their IHDR dimensions without decoding art."""
    streams: list[tuple[int, int, int]] = []
    start = 0
    while True:
        offset = data.find(PNG_SIGNATURE, start)
        if offset < 0:
            return streams
        if offset + 24 > len(data) or data[offset + 12 : offset + 16] != b"IHDR":
            raise RuntimeError(f"invalid PNG signature at byte {offset}")
        width = int.from_bytes(data[offset + 16 : offset + 20], "big")
        height = int.from_bytes(data[offset + 20 : offset + 24], "big")
        streams.append((offset, width, height))
        start = offset + len(PNG_SIGNATURE)


def dimension_counts(streams: list[tuple[int, int, int]]) -> dict[str, int]:
    counts = Counter(f"{width}x{height}" for _, width, height in streams)
    return dict(sorted(counts.items()))


def png_family(path: str) -> str:
    if path.startswith("resources/GFX/Status/"):
        return "GFX status icons"
    if path.startswith("resources/GFX/Spells/"):
        return "GFX spell animations"
    if path.startswith("resources/GFX/Items/"):
        return "GFX item sheet"
    if path.startswith("resources/GFX/Updater/"):
        return "GFX updater"
    if path.startswith("resources/Skins/Main Theme/"):
        return "skin Main Theme"
    if path.startswith("resources/Skins/Terra's Theme/"):
        return "skin Terra's Theme"
    if path.startswith("resources/Help/Controls/"):
        return "help control diagrams"
    return "other PNG"


def inspect_pmu_client_containers(checkout_root: Path | None, commit: str) -> dict[str, Any]:
    """Audit inner PNGs in PMU's custom art containers, retaining no pixels."""
    if checkout_root is None:
        return {"inspected": False, "reason": "--checkout-root was not supplied"}
    client = verified_checkout(checkout_root, "PMU-Client", commit)

    def scan_files(file_paths: list[Path]) -> tuple[list[dict[str, Any]], Counter[str]]:
        per_file: list[dict[str, Any]] = []
        dimensions: Counter[str] = Counter()
        for file_path in file_paths:
            data = file_path.read_bytes()
            streams = png_streams(data)
            dimensions.update(dimension_counts(streams))
            per_file.append(
                {
                    "path": file_path.relative_to(client).as_posix(),
                    "bytes": len(data),
                    "sha256": sha256(file_path),
                    "embedded_png_count": len(streams),
                    "dimensions": dimension_counts(streams),
                }
            )
        return per_file, dimensions

    tile_files: list[dict[str, Any]] = []
    tile_png_total = 0
    for file_path in sorted((client / "resources/GFX/Tiles").glob("*.tile")):
        data = file_path.read_bytes()
        first_png = data.find(PNG_SIGNATURE)
        if first_png < 8 or (first_png - 8) % 12:
            raise RuntimeError(f"unrecognised .tile index layout: {file_path}")
        tile_count = (first_png - 8) // 12
        dimensions: Counter[str] = Counter()
        for index in range(tile_count):
            table_offset = 8 + index * 12
            relative_offset = int.from_bytes(data[table_offset : table_offset + 8], "little")
            png_size = int.from_bytes(data[table_offset + 8 : table_offset + 12], "little")
            png_offset = first_png + relative_offset
            if data[png_offset : png_offset + len(PNG_SIGNATURE)] != PNG_SIGNATURE:
                raise RuntimeError(f"non-PNG .tile payload: {file_path} tile {index}")
            if png_offset + png_size > len(data):
                raise RuntimeError(f"out-of-range .tile payload: {file_path} tile {index}")
            width = int.from_bytes(data[png_offset + 16 : png_offset + 20], "big")
            height = int.from_bytes(data[png_offset + 20 : png_offset + 24], "big")
            dimensions[f"{width}x{height}"] += 1
        tile_png_total += tile_count
        tile_files.append(
            {
                "path": file_path.relative_to(client).as_posix(),
                "bytes": len(data),
                "sha256": sha256(file_path),
                "embedded_png_count": tile_count,
                "dimensions": dict(sorted(dimensions.items())),
            }
        )

    sprite_files, sprite_dimensions = scan_files(sorted(client.glob("resources/GFX/Sprites/*.sprite")))
    portrait_files, portrait_dimensions = scan_files(sorted(client.glob("resources/GFX/Mugshots/*.portrait")))
    direct_png_files, _ = scan_files(
        sorted(path for path in (client / "resources").rglob("*") if path.is_file() and path.suffix.lower() == ".png")
    )
    families: dict[str, dict[str, Any]] = {}
    for record in direct_png_files:
        family = png_family(record["path"])
        accumulator = families.setdefault(family, {"count": 0, "bytes": 0, "dimensions": Counter()})
        accumulator["count"] += 1
        accumulator["bytes"] += record["bytes"]
        accumulator["dimensions"].update(record["dimensions"])
    for accumulator in families.values():
        accumulator["dimensions"] = dict(sorted(accumulator["dimensions"].items()))

    return {
        "inspected": True,
        "repository": "PMUniverse/PMU-Client",
        "snapshot_commit": commit,
        "method": (
            "PNG signatures and IHDR headers were inspected in local files. .tile "
            "payload offsets were validated against its 12-byte offset/size index."
        ),
        "tile": {
            "containers": len(tile_files),
            "bytes": sum(record["bytes"] for record in tile_files),
            "embedded_pngs": tile_png_total,
            "per_file": tile_files,
        },
        "sprite": {
            "containers": len(sprite_files),
            "bytes": sum(record["bytes"] for record in sprite_files),
            "embedded_pngs": sum(record["embedded_png_count"] for record in sprite_files),
            "dimensions": dict(sorted(sprite_dimensions.items())),
            "per_file": sprite_files,
        },
        "portrait": {
            "containers": len(portrait_files),
            "bytes": sum(record["bytes"] for record in portrait_files),
            "embedded_pngs": sum(record["embedded_png_count"] for record in portrait_files),
            "dimensions": dict(sorted(portrait_dimensions.items())),
            "empty_container_paths": [
                record["path"] for record in portrait_files if record["embedded_png_count"] == 0
            ],
            "per_file": portrait_files,
        },
        "png": {
            "files": len(direct_png_files),
            "bytes": sum(record["bytes"] for record in direct_png_files),
            "families": dict(sorted(families.items())),
            "per_file": direct_png_files,
        },
    }


def inspect_zip(checkout_root: Path | None, repo_name: str, commit: str, path: str) -> dict[str, Any]:
    result: dict[str, Any] = {"inspected": False}
    if checkout_root is None:
        return result
    archive_path = checkout_root / repo_name / path
    # local_sha validates the checkout commit and yields a reproducible archive digest
    result["sha256"] = local_sha(checkout_root, repo_name, commit, path)
    with zipfile.ZipFile(archive_path) as archive:
        files = [item for item in archive.infolist() if not item.is_dir()]
        extensions = Counter(Path(item.filename.lower()).suffix or "[none]" for item in files)
        result.update(
            {
                "inspected": True,
                "file_count": len(files),
                "uncompressed_bytes": sum(item.file_size for item in files),
                "compressed_bytes": sum(item.compress_size for item in files),
                "extension_counts": dict(sorted(extensions.items())),
                "entries": [
                    {
                        "path": item.filename,
                        "uncompressed_size": item.file_size,
                        "compressed_size": item.compress_size,
                        "crc32": f"{item.CRC:08x}",
                    }
                    for item in files
                ],
            }
        )
    return result


def raw_url(full_name: str, commit: str, path: str) -> str:
    return "https://raw.githubusercontent.com/{}/{}/{}".format(
        full_name, commit, urllib.parse.quote(path, safe="/")
    )


def github_url(full_name: str, commit: str, path: str) -> str:
    return "https://github.com/{}/blob/{}/{}".format(
        full_name, commit, urllib.parse.quote(path, safe="/")
    )


def build(out_dir: Path, checkout_root: Path | None, audit_date: str) -> None:
    repositories = api_json_pages(f"orgs/{ORG}/repos?per_page=100&type=all")
    repositories.sort(key=lambda item: item["name"].lower())
    assets: list[dict[str, Any]] = []
    repo_records: list[dict[str, Any]] = []
    releases: list[dict[str, Any]] = []
    archives: list[dict[str, Any]] = []

    for repo in repositories:
        full_name = repo["full_name"]
        name = repo["name"]
        branch = repo["default_branch"]
        commit = api_json(f"repos/{full_name}/commits/{urllib.parse.quote(branch, safe='')}")
        snapshot = commit["sha"]
        tree = api_json(f"repos/{full_name}/git/trees/{snapshot}?recursive=1")
        if tree.get("truncated"):
            # Failing is safer than publishing an inventory that only looks complete.
            raise RuntimeError(f"recursive tree was truncated for {full_name}")
        blob_count = sum(1 for item in tree["tree"] if item["type"] == "blob")
        license_info = repo.get("license") or {}
        repo_record = {
            "name": name,
            "full_name": full_name,
            "url": repo["html_url"],
            "visibility": repo.get("visibility", "public"),
            "archived": repo["archived"],
            "fork": repo["fork"],
            "default_branch": branch,
            "snapshot_commit": snapshot,
            "snapshot_commit_date": commit["commit"]["author"]["date"],
            "snapshot_message": commit["commit"]["message"].splitlines()[0],
            "tree_sha": commit["commit"]["tree"]["sha"],
            "tree_blob_count": blob_count,
            "repository_license_spdx": license_info.get("spdx_id"),
            "repository_license_url": license_info.get("html_url"),
        }
        repo_records.append(repo_record)

        repo_releases = api_json_pages(f"repos/{full_name}/releases?per_page=100")
        release_record = {
            "repository": full_name,
            "release_count": len(repo_releases),
            "assets": [],
        }
        for release in repo_releases:
            for asset in release.get("assets", []):
                release_record["assets"].append(
                    {
                        "release_tag": release["tag_name"],
                        "release_name": release.get("name"),
                        "published_at": release.get("published_at"),
                        "name": asset["name"],
                        "size": asset["size"],
                        "download_url": asset["browser_download_url"],
                    }
                )
        releases.append(release_record)

        for item in tree["tree"]:
            if item["type"] != "blob":
                continue
            classified = classify(item["path"])
            if classified is None:
                continue
            scope, asset_format = classified
            record: dict[str, Any] = {
                "repository": full_name,
                "snapshot_commit": snapshot,
                "path": item["path"],
                "scope": scope,
                "format": asset_format,
                "size_bytes": item.get("size", 0),
                "git_blob_sha1": item["sha"],
                "sha256": local_sha(checkout_root, name, snapshot, item["path"]),
                "github_url": github_url(full_name, snapshot, item["path"]),
                "raw_url": raw_url(full_name, snapshot, item["path"]),
                "provenance_and_license_note": provenance_note(name, scope),
            }
            assets.append(record)
            if scope == "archive_review":
                archives.append({**record, "inspection": inspect_zip(checkout_root, name, snapshot, item["path"])})

    assets.sort(key=lambda item: (item["repository"].lower(), item["path"].lower()))
    pmu_client_commit = next(record["snapshot_commit"] for record in repo_records if record["name"] == "PMU-Client")
    container_analysis = inspect_pmu_client_containers(checkout_root, pmu_client_commit)
    category_counts = Counter((item["repository"], item["scope"], item["format"]) for item in assets)
    category_sizes = Counter()
    for item in assets:
        category_sizes[(item["repository"], item["scope"], item["format"])] += item["size_bytes"]
    summary_categories = [
        {
            "repository": repository,
            "scope": scope,
            "format": asset_format,
            "file_count": count,
            "size_bytes": category_sizes[(repository, scope, asset_format)],
        }
        for (repository, scope, asset_format), count in sorted(category_counts.items())
    ]

    manifest = {
        "schema_version": 1,
        "organization": ORG,
        "audit_date": audit_date,
        "scope": (
            "All repositories visible through the public GitHub API, all recursive "
            "Git trees, and every release asset. No tree response was truncated."
        ),
        "important_rights_note": (
            "A repository license is not proof that every bundled game-art asset is "
            "cleared for reuse. This manifest preserves provenance rather than copying "
            "third-party pixels into this project."
        ),
        "repositories": repo_records,
        "asset_files": assets,
        "summary_by_category": summary_categories,
        "release_assets": releases,
        "inspected_archives": archives,
        "pmuniverse_client_container_analysis": container_analysis,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / "container_analysis.json").write_text(
        json.dumps(container_analysis, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    with (out_dir / "inventory.csv").open("w", newline="", encoding="utf-8") as stream:
        fields = [
            "repository", "snapshot_commit", "path", "scope", "format", "size_bytes",
            "git_blob_sha1", "sha256", "github_url", "raw_url", "provenance_and_license_note",
        ]
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(assets)
    (out_dir / "summary.json").write_text(
        json.dumps(
            {
                "organization": ORG,
                "audit_date": audit_date,
                "repository_count": len(repo_records),
                "asset_file_count": len(assets),
                "asset_byte_count": sum(item["size_bytes"] for item in assets),
                "summary_by_category": summary_categories,
                "release_assets": releases,
                "inspected_archives": archives,
                "pmuniverse_client_container_analysis": {
                    "inspected": container_analysis["inspected"],
                    "embedded_pngs": {
                        category: container_analysis.get(category, {}).get("embedded_pngs", 0)
                        for category in ("tile", "sprite", "portrait")
                    },
                },
            },

            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )
    print(
        f"PMUniverse: {len(repo_records)} repositories, {len(assets)} catalogued files, "
        f"{sum(item['size_bytes'] for item in assets)} source bytes -> {out_dir}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("audit_pmuniverse_assets"), help="output directory")
    parser.add_argument(
        "--checkout-root",
        type=Path,
        help="directory containing commit-checked-out repository folders, for SHA-256/archive inspection",
    )
    parser.add_argument(
        "--audit-date",
        default=date.today().isoformat(),
        help="date shown in the report; use the local audit date when reproducibility matters",
    )
    args = parser.parse_args()
    build(args.out, args.checkout_root, args.audit_date)


if __name__ == "__main__":
    main()
