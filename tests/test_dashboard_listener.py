import pathlib, subprocess, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class ListenerTests(unittest.TestCase):
 def test_arguments_use_all_interfaces(self):
  source=(ROOT/'install.sh').read_text()
  parser=source[source.index('bind=0.0.0.0'):source.index('if ! command -v python3')]
  for args in ([], ['--site','Test'], ['--bind','192.0.2.7']):
   run=subprocess.run(['bash','-c',parser+'\n[[ $bind == 0.0.0.0 && $port == 8000 ]]','test',*args],capture_output=True,text=True)
   self.assertEqual(run.returncode,0,run.stderr)
 def test_shell_syntax(self):
  for name in ('install.sh','get-mmod.sh','build.sh','verify.sh'):
   subprocess.run(['bash','-n',str(ROOT/name)],check=True)
