from __future__ import annotations

import hashlib
import io
import json
import unittest
import xml.etree.ElementTree as ET
import zipfile
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

from . import build as b


class GrotteGlaciaireBorealeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((b.OUTPUT / "manifest.json").read_text())
        cls.terrain = Image.open(b.OUTPUT / "review/terrain_detoure.png").convert("RGBA")
        cls.masks = {
            layer_id: np.array(Image.open(b.OUTPUT / "masques" / f"GrotteGlaciaireV1_{layer_id}.png")) > 0
            for layer_id in b.TERRAIN_LAYER_LABELS
        }
        cls.frames = [
            Image.open(b.OUTPUT / "animation/aurore_frames" / f"GrotteGlaciaireV1_Aurore_{index:02d}.png").convert("RGBA")
            for index in range(b.FINAL_AURORA_FRAMES)
        ]

    def test_inputs_and_raw_copies_have_recorded_hashes(self) -> None:
        for entry in self.manifest["inputs"]:
            source = b.ROOT / entry["file"]
            self.assertTrue(source.is_file())
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), entry["sha256"])
            self.assertEqual((b.OUTPUT / "bruts" / source.name).read_bytes(), source.read_bytes())

    def test_canvas_grid_and_layers_are_aligned(self) -> None:
        self.assertEqual(self.manifest["canvas_px"], [768, 640])
        self.assertEqual(768 % b.GRID, 0)
        self.assertEqual(640 % b.GRID, 0)
        for path in (b.OUTPUT / "calques").glob("*.png"):
            with Image.open(path) as image:
                self.assertEqual(image.size, (768, 640))
        for frame in self.frames:
            self.assertEqual(frame.size, (768, 640))

    def test_exterior_magenta_is_not_opaque_in_output_layers(self) -> None:
        forbidden = [(253, 1, 251), (249, 52, 247), (255, 0, 255)]
        paths = list((b.OUTPUT / "calques").glob("*.png")) + list((b.OUTPUT / "animation/aurore_frames").glob("*.png"))
        for path in paths:
            pixels = np.array(Image.open(path).convert("RGBA"))
            opaque = pixels[:, :, 3] > 0
            for colour in forbidden:
                self.assertFalse(np.any(np.all(pixels[:, :, :3] == colour, axis=2) & opaque), path.name)

    def test_terrain_masks_are_disjoint_and_complete(self) -> None:
        count = np.zeros((b.CANVAS_H, b.CANVAS_W), dtype=np.uint8)
        for mask in self.masks.values():
            count += mask.astype(np.uint8)
        valid = np.array(self.terrain)[:, :, 3] > 0
        self.assertTrue(np.array_equal(count, valid.astype(np.uint8)))

    def test_terrain_layers_recompose_the_cutout_exactly(self) -> None:
        composition = Image.new("RGBA", (b.CANVAS_W, b.CANVAS_H))
        for layer_id in b.TERRAIN_LAYER_LABELS:
            composition.alpha_composite(Image.open(b.OUTPUT / "calques" / f"GrotteGlaciaireV1_{layer_id}.png").convert("RGBA"))
        self.assertEqual(composition.tobytes(), self.terrain.tobytes())

    def test_south_to_north_path_is_connected_and_clear_of_cliff_layers(self) -> None:
        path = self.masks["03_chemin_sud_nord"]
        starts = [(b.CANVAS_H - 1, x) for x in range(b.CANVAS_W) if path[b.CANVAS_H - 1, x]]
        self.assertGreater(len(starts), 32)
        seen = set(starts)
        todo = deque(starts)
        reached_north_threshold = False
        while todo:
            y, x = todo.popleft()
            if y <= 412 and 340 <= x <= 430:
                reached_north_threshold = True
            for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= yy < b.CANVAS_H and 0 <= xx < b.CANVAS_W and path[yy, xx] and (yy, xx) not in seen:
                    seen.add((yy, xx))
                    todo.append((yy, xx))
        self.assertTrue(reached_north_threshold)
        for layer_id in ("05_falaise_nord", "06_falaise_gauche", "07_falaise_droite", "08_rochers_cristaux_avant"):
            self.assertFalse(np.any(self.masks[layer_id] & path), layer_id)

    def test_cave_is_dark_and_sits_north_of_the_route(self) -> None:
        cave = self.masks["04_grotte_et_seuil"]
        self.assertGreater(cave.sum(), 8000)
        pixels = np.array(Image.open(b.OUTPUT / "calques/GrotteGlaciaireV1_04_grotte_et_seuil.png"))
        lum = 0.299 * pixels[:, :, 0] + 0.587 * pixels[:, :, 1] + 0.114 * pixels[:, :, 2]
        self.assertLess(float(lum[cave].mean()), 100)
        ys, _ = np.where(cave)
        self.assertLess(ys.mean(), 410)

    def test_aurora_has_sixteen_real_in_place_frames_and_exact_virtual_loop(self) -> None:
        self.assertEqual(len(self.frames), 16)
        encoded = [frame.tobytes() for frame in self.frames]
        self.assertGreaterEqual(len(set(encoded)), 14)
        end = b.aurora_frame_at(
            [Image.open(b.OUTPUT / "animation/keyposes" / f"GrotteGlaciaireV1_pose_{index:02d}_ancree.png").convert("RGBA") for index in b.SELECTED_AURORA_POSES],
            b.FINAL_AURORA_FRAMES,
        )
        self.assertEqual(end.tobytes(), self.frames[0].tobytes())
        self.assertFalse(self.manifest["aurora"]["wrap"])
        self.assertTrue(all(np.array(frame)[330:, :, 3].max() == 0 for frame in self.frames))

    def test_aurora_transitions_are_bounded_and_alpha_only_overlays(self) -> None:
        differences = []
        for index, frame in enumerate(self.frames):
            first = np.array(frame).astype(np.int16)
            second = np.array(self.frames[(index + 1) % len(self.frames)]).astype(np.int16)
            differences.append(float(np.abs(first - second).mean()))
            self.assertEqual(int(first[:, :1, 3].max()), 0)
            self.assertEqual(int(first[:, -1:, 3].max()), 0)
        self.assertGreater(max(differences), 0.05)
        self.assertLess(max(differences), 18.0)

    def test_animation_previews_have_correct_frame_count_and_duration(self) -> None:
        with Image.open(b.OUTPUT / "animation/aurore_16frames.webp") as image:
            self.assertEqual(image.n_frames, 16)
        for name in ("animation_scene.gif", "animation_aurore_seule.gif"):
            duration = 0
            with Image.open(b.OUTPUT / "review" / name) as image:
                self.assertEqual(image.n_frames, 16)
                for index in range(image.n_frames):
                    image.seek(index)
                    duration += image.info.get("duration", 0)
            self.assertEqual(duration, 1920)

    def test_ora_recomposes_phase_zero(self) -> None:
        with zipfile.ZipFile(b.OUTPUT / "grotte_glaciaire_boreale_v1.ora") as archive:
            root = ET.fromstring(archive.read("stack.xml"))
            composite = Image.new("RGBA", (b.CANVAS_W, b.CANVAS_H))
            for layer in reversed(root.findall("./stack/layer")):
                composite.alpha_composite(Image.open(io.BytesIO(archive.read(layer.get("src")))).convert("RGBA"))
            merged = Image.open(io.BytesIO(archive.read("mergedimage.png"))).convert("RGBA")
        expected = Image.open(b.OUTPUT / "review/COMPOSITION_PHASE_00.png").convert("RGBA")
        self.assertEqual(composite.tobytes(), merged.tobytes())
        self.assertEqual(composite.tobytes(), expected.tobytes())


if __name__ == "__main__":
    unittest.main()
