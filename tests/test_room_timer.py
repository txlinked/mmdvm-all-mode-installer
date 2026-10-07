import json,tempfile,sys,unittest
from pathlib import Path
from unittest.mock import patch
from test_crossmode_setup import SetupTests,setup
class RoomTimerTests(unittest.TestCase):
 def test_disable_change_and_preserve(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);cfg=SetupTests().fixture(root)
   for args,enabled,minutes in [(['--room-timeout','0'],False,None),([],False,None),(['--room-timeout','25'],True,25)]:
    with patch.object(sys,'argv',['setup','--root',d,'--apply',*args]):setup.main()
    self.assertIn('MMOD_ROOM_IDLE_MINUTES=0',(cfg/'room-timeout.env').read_text())
    selected=json.loads((root/'var/lib/mmod/state/gateway-policy.json').read_text())['2|FCS|FCS00334']
    self.assertEqual(selected['enabled'],enabled)
    self.assertEqual(selected.get('minutes'),minutes)
 def test_preserve_static_off_and_other_rooms(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);cfg=SetupTests().fixture(root)
   p=root/'var/lib/mmod/state/gateway-policy.json';p.parent.mkdir(parents=True)
   original={'2|FCS|FCS00334':{'static':True,'enabled':False,'minutes':45},'1|BrandMeister|*':{'enabled':False}}
   p.write_text(json.dumps(original))
   with patch.object(sys,'argv',['setup','--root',d,'--apply']):setup.main()
   self.assertEqual(json.loads(p.read_text()),original)
   self.assertIn('MMOD_ROOM_IDLE_MINUTES=0',(cfg/'room-timeout.env').read_text())
