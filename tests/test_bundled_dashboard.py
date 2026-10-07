import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class BundledDashboardTests(unittest.TestCase):
 def test_checksum_and_timer_network_integration(self):
  archive=ROOT/'vendor/mmod-source.tar.gz'
  manifest=json.loads((ROOT/'manifest.json').read_text())
  self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(),manifest['dashboard']['sha256'])
  with tempfile.TemporaryDirectory() as folder:
   with tarfile.open(archive) as source:source.extractall(folder,filter='data')
   dashboard=Path(folder)/'mmod'
   for pattern in ('test_timer_choice.py','test_full_stack_timer.py','test_fusion_activity.py'):
    subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p',pattern,'-v'],cwd=dashboard,check=True)
   subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_network_access.py','-v'],cwd=dashboard,check=True)
   if os.environ.get('MMOD_TEST_API')=='1':
    subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_full_stack_timer_api.py','-v'],cwd=dashboard,check=True)
