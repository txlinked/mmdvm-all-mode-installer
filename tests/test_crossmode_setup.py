import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('setup', ROOT / 'configure-dmr2ysf.py')
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class SetupTests(unittest.TestCase):
    def fixture(self, root, passall=False):
        cfg = root / 'etc/mmod-radio'
        cfg.mkdir(parents=True)
        (cfg / 'MMDVM.ini').write_text('[General]\nCallsign=N3DMC\nId=3202139\n[Info]\nRXFrequency=446312500\nTXFrequency=441312500\n[Modem]\nPTTInvert=0\n[DMR]\nSlot1=1\nSlot2=1\nColorCode=9\n')
        bm = 'PassAllTG1=2' if passall else 'TGRewrite1=2,1,2,1,16777215'
        (cfg / 'DMRGateway.ini').write_text('[DMR Network 1]\nEnabled=1\nName=BM\nPassword=keep-this-secret\nTGRewrite0=1,1,1,1,16777215\n' + bm + '\n[DMR Network 2]\nEnabled=1\nName=CBridge2\nPort=54026\nTGRewrite=\nTGRewrite0=2,3148,2,3148,1\n[DMR Network 5]\nEnabled=0\nName=HBLink2\n')
        (cfg / 'DMR2YSF.ini').write_text('[YSF Network]\nCallsign=OLD\n[DMR Network]\nId=1\n')
        (cfg / 'YSFGateway.ini').write_text('[Info]\nRXFrequency=446312500\nTXFrequency=441312500\n[YSF Network]\nHosts=/var/lib/mmod-radio/YSFHosts.json\n')
        return cfg

    def test_mapping_and_station_preservation(self):
        for passall in (False, True):
            with self.subTest(passall=passall), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                cfg = self.fixture(root, passall)
                original = (cfg / 'MMDVM.ini').read_text()
                _, files, _, _ = setup.plan(root)
                self.assertEqual(files['MMDVM.ini'], original)
                c = setup.parse(files['DMRGateway.ini'])
                self.assertEqual(c['DMR Network 1']['Password'], 'keep-this-secret')
                self.assertEqual(c['DMR Network 1']['TGRewrite0'], '1,1,1,1,16777215')
                self.assertEqual(c['DMR Network 2']['TGRewrite0'], '2,3148,2,3148,1')
                self.assertEqual(c['DMR Network 5']['TGRewrite0'], '2,7000000,2,0,999999')
                self.assertEqual(c['DMR Network 5']['SrcRewrite0'], '2,0,2,7000000,999999')
                routes = [list(map(int, v.split(','))) for k, v in c['DMR Network 1'].items() if k.startswith('TGRewrite')]
                def bm_contains(tg):
                    return any(r[0] == 2 and r[1] <= tg < r[1] + r[4] for r in routes)
                self.assertFalse(bm_contains(7100334))
                self.assertFalse(bm_contains(3148))
                self.assertTrue(bm_contains(91))
                self.assertTrue(bm_contains(7999999))
                self.assertEqual(7100334 - 7000000, 100334)
                self.assertEqual(100334 + 7000000, 7100334)
                for name, content in files.items():
                    (cfg / name).write_text(content)
                _, again, _, _ = setup.plan(root)
                self.assertEqual(again, files, 'Repeated setup must not accumulate routes')

    def test_enabled_network_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cfg = self.fixture(root)
            p = cfg / 'DMRGateway.ini'
            p.write_text(p.read_text().replace('Enabled=0\nName=HBLink2', 'Enabled=1\nName=HBLink2'))
            before = p.read_bytes()
            with self.assertRaises(ValueError):
                setup.plan(root)
            self.assertEqual(p.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
