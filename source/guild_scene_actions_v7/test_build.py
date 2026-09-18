"""Independent checks for batch V7: every visible pixel of Pain/DeepBreath must
be a translated copy of the pinned native Hurt/Idle frame, loops must close and
alpha must stay binary. Reads provenance recorded by build.py.
"""
import unittest, json
from pathlib import Path
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
O = R/'exports/guild_scene_actions_v7'
REF = R/'source/guild_members_audit/references'
SHEET = {'Pain': 'Hurt', 'DeepBreath': 'Idle'}


class V7Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rep = json.loads((O/'verification.json').read_text())

    def _native(self, slot, name):
        f = REF/slot/'sprite'
        import xml.etree.ElementTree as ET
        root = ET.parse(f/'AnimData.xml').getroot()
        a = next(a for a in root.findall('./Anims/Anim') if a.findtext('Name') == name)
        w, h = int(a.findtext('FrameWidth')), int(a.findtext('FrameHeight'))
        cols = Image.open(f/f'{name}-Anim.png').size[0]//w
        return w, h, cols, np.array(Image.open(f/f'{name}-Anim.png').convert('RGBA'))

    def test_actions_recorded(self):
        self.assertEqual(len(self.rep['actions']), 12)
        for k, v in self.rep['actions'].items():
            self.assertEqual(v['state'], 'technical_pass')
            self.assertEqual(v['directions'], 8)

    def test_every_pixel_is_translated_native(self):
        for key, v in self.rep['actions'].items():
            slug, act = key.split('/')
            slot = self.rep['packs'][slug]['slot']
            w, h, cols, nat = self._native(slot, SHEET[act])
            anim = np.array(Image.open(O/slug/f'{act}-Anim.png').convert('RGBA'))
            prov = v['provenance']
            for di in range(8):
                for fi, (nfi, dx, dy) in enumerate(prov[di]):
                    got = anim[di*h:(di+1)*h, fi*w:(fi+1)*w]
                    base = np.zeros((h, w, 4), np.uint8)
                    src = nat[di*h:(di+1)*h, (nfi % cols)*w:((nfi % cols)+1)*w]
                    ys, xs = np.nonzero(src[:, :, 3])
                    base[ys+dy, xs+dx] = src[ys, xs]
                    self.assertTrue(np.array_equal(got, base), f'{key} dir{di} frame{fi} not a translated native frame')

    def test_loop_closes_and_alpha_binary(self):
        for key in self.rep['actions']:
            slug, act = key.split('/')
            a = np.array(Image.open(O/slug/f'{act}-Anim.png').convert('RGBA'))
            h = a.shape[0]//8
            import xml.etree.ElementTree as ET
            root = ET.parse(O/slug/'AnimData.xml').getroot()
            n = next(x for x in root.findall('./Anims/Anim') if x.findtext('Name') == act)
            w = int(n.findtext('FrameWidth'))
            nfr = len(n.findall('./Durations/Duration'))
            for di in range(8):
                d = a[di*h:(di+1)*h]
                self.assertEqual(d[:, :w].tobytes(), d[:, (nfr-1)*w:nfr*w].tobytes(), f'{key} dir{di} loop open')
            self.assertTrue(set(np.unique(a[:, :, 3])).issubset({0, 255}), f'{key} non-binary alpha')


if __name__ == '__main__':
    unittest.main()
