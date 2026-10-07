import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('dashboard_timer',ROOT/'configure-dashboard-timer.py')
timer=importlib.util.module_from_spec(spec);spec.loader.exec_module(timer)

class DefaultsTests(unittest.TestCase):
 def test_fresh_ten_and_legacy_fifteen(self):
  for existing,minutes in ((False,10),(True,15)):
   with tempfile.TemporaryDirectory() as folder:
    root=Path(folder);self.assertTrue(timer.seed(root,existing))
    self.assertEqual(json.loads((root/'var/lib/mmod/state/dynamic-timer.json').read_text()),{'enabled':True,'minutes':minutes})
 def test_updates_preserve_exact_saved_policy(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);p=root/'var/lib/mmod/state/dynamic-timer.json';p.parent.mkdir(parents=True)
   for policy in ({'enabled':False,'minutes':37,'updated':123},{'enabled':True,'minutes':45}):
    original=json.dumps(policy);p.write_text(original)
    self.assertFalse(timer.seed(root,True));self.assertEqual(p.read_text(),original)
