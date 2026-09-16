"""Mechanical regression tests; not a substitute for anatomical or PMDO review."""
import unittest
import xml.etree.ElementTree as ET
from PIL import Image
from source.transformations_v1.crown_attachment.attach import marker, seat_from_markers, resolve_nodes, place, load_profiles


class AttachmentTests(unittest.TestCase):
    def test_marker_requires_exactly_one_visible_pixel(self):
        image = Image.new('RGBA', (8, 8))
        self.assertIsNone(marker(image, (0, 0, 0)))
        image.putpixel((2, 3), (0, 0, 0, 255))
        self.assertEqual(marker(image, (0, 0, 0)), [2, 3])
        image.putpixel((4, 5), (0, 0, 0, 255))
        self.assertIsNone(marker(image, (0, 0, 0)))

    def test_anatomical_seat_scales_with_character(self):
        self.assertEqual(seat_from_markers([12, 8], [10, 20], [-1, -3], 2), [2, -30])
        with self.assertRaises(ValueError):
            seat_from_markers(None, [10, 20], [0, 0])
        with self.assertRaises(ValueError):
            seat_from_markers([12, 8], [10, 20], [0, 0], 0)

    def test_alias_resolution_and_cycle(self):
        root = ET.fromstring('<Root><Anims><Anim><Name>Idle</Name></Anim><Anim><Name>Wait</Name><CopyOf>Idle</CopyOf></Anim></Anims></Root>')
        _, resolve = resolve_nodes(root)
        self.assertEqual(resolve('Wait')[0], 'Idle')
        with self.assertRaises(ValueError):
            resolve('Missing')
        root.find('./Anims/Anim').append(ET.fromstring('<CopyOf>Wait</CopyOf>'))
        with self.assertRaises(ValueError):
            resolve('Wait')

    def test_blocked_pose_never_placed(self):
        with self.assertRaises(ValueError):
            place(None, 'fire', {'state': 'blocked_pose_requires_manual_override'}, [0, 0])

    def test_profiles_have_eight_anatomical_settings(self):
        for name, profile in load_profiles().items():
            with self.subTest(profile=name):
                self.assertEqual(len(profile['seat_offsets']), 8)
                self.assertEqual(len(profile['head_widths']), 8)
                self.assertTrue(all(width > 0 for width in profile['head_widths']))


if __name__ == '__main__':
    unittest.main()
