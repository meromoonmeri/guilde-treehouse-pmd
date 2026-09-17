import json
from pathlib import Path
import tempfile
import unittest
from source.guild_members_audit.audit import xml_actions, OUT


class GuildAuditTests(unittest.TestCase):
    def parse(self, text, files):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'AnimData.xml'
            p.write_text(text)
            return xml_actions(p,{name:{} for name in files})

    def test_alias_resolves_to_real_png_triple(self):
        result=self.parse('<Root><Anims><Anim><Name>Idle</Name><FrameWidth>40</FrameWidth><FrameHeight>48</FrameHeight><Durations><Duration>8</Duration></Durations></Anim><Anim><Name>Pose</Name><CopyOf>Idle</CopyOf></Anim></Anims></Root>', ['Idle-Anim.png','Idle-Offsets.png','Idle-Shadow.png'])
        self.assertTrue(result['Pose']['png_triple_present'])
        self.assertEqual(result['Pose']['source_action'],'Idle')
        self.assertEqual(result['Pose']['durations_ticks'],[8])

    def test_alias_cycle_is_not_available(self):
        result=self.parse('<Root><Anims><Anim><Name>A</Name><CopyOf>B</CopyOf></Anim><Anim><Name>B</Name><CopyOf>A</CopyOf></Anim></Anims></Root>', [])
        self.assertFalse(result['A']['png_triple_present'])
        self.assertIn('cycle',result['A']['error'])

    def test_missing_target_is_recorded(self):
        result=self.parse('<Root><Anims><Anim><Name>A</Name><CopyOf>Missing</CopyOf></Anim></Anims></Root>', [])
        self.assertFalse(result['A']['png_triple_present'])
        self.assertIn('missing target',result['A']['error'])

    def test_missing_offsets_blocks_triple(self):
        result=self.parse('<Root><Anims><Anim><Name>Idle</Name><FrameWidth>40</FrameWidth><FrameHeight>48</FrameHeight><Durations><Duration>8</Duration></Durations></Anim></Anims></Root>', ['Idle-Anim.png','Idle-Shadow.png'])
        self.assertFalse(result['Idle']['png_triple_present'])
        self.assertEqual(result['Idle']['missing_files'],['Idle-Offsets.png'])

    def test_saved_report_covers_exact_requested_members(self):
        report=json.loads((OUT/'audit.json').read_text())
        members={r['slot']:r for r in report['members']}
        self.assertEqual(set(members),{'0282','0083','0674','0371','0285','0440','0417','0461','0186'})
        self.assertEqual(report['totals']['missing_required_portraits'],12)
        self.assertEqual(report['totals']['missing_dungeon_actions'],0)
        self.assertEqual([r['slot'] for r in report['members'] if r['missing_required_portraits']],['0186'])
        self.assertTrue(all(r['idle_triple_geometry_verified'] for r in report['members']))
        self.assertTrue(all(not members[s]['missing_project_full_actions'] for s in ['0371','0440','0417']))


if __name__=='__main__':unittest.main()
