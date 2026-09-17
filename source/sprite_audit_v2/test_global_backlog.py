import json
from pathlib import Path
import unittest
from source.sprite_audit_v2.global_backlog import classify, ROOT


class BacklogTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads((ROOT / 'source/pmd_character_pipeline/contract.json').read_text())
        self.row = {'path': '0001', 'name': 'Example', 'canonical': True, 'base': True,
                    'sprite_required': True, 'portrait_required': True,
                    'sprite_complete': 1, 'portrait_complete': 1,
                    'sprite_files': {'Idle': False}, 'portrait_files': {'Normal': False},
                    'sprite_pending': {}, 'portrait_pending': {}}

    def test_false_lock_is_still_presence(self):
        r = classify(self.row, self.contract)
        self.assertFalse(r['sprite_entirely_absent'])
        self.assertNotIn('Normal', r['missing_required_portraits'])

    def test_optional_slot_not_counted_as_required_absence(self):
        self.row.update(sprite_required=False, sprite_files={})
        self.assertFalse(classify(self.row, self.contract)['sprite_entirely_absent'])

    def test_project_actions_do_not_override_upstream_completion(self):
        self.row['sprite_complete'] = 2
        r = classify(self.row, self.contract)
        self.assertFalse(r['sprite_incomplete_upstream'])
        self.assertTrue(r['project_full_action_gaps_not_upstream_requirements'])

    def test_pending_submission_needs_coordination(self):
        self.row['sprite_pending'] = {'submission': {}}
        self.assertEqual(classify(self.row, self.contract)['gate'], 'coordinate_upstream_pending')


if __name__ == '__main__':
    unittest.main()
