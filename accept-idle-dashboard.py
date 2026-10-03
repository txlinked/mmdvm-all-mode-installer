"""Validate the upstream install's specific no-radio postcheck on a fresh station."""
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.request

log, source, url = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
text = log.read_text()
if not re.search(r'File "<stdin>", line 11, in <module>\nAssertionError\s*$', text):
    raise SystemExit('Dashboard install failed; see ' + str(log))
with urllib.request.urlopen(url + '/api/health', timeout=5) as response:
    assert json.load(response)['ok']
with urllib.request.urlopen(url + '/api/radio', timeout=5) as response:
    assert json.load(response).get('error') == 'No radio log source found; check MMDVM logging settings'
for original in source.glob('*.py'):
    installed = Path('/opt/mmod') / original.name
    # Build/setup-only scripts are not installed by the original installer.
    if installed.exists():
        assert installed.read_bytes() == original.read_bytes(), 'Dashboard source changed: ' + original.name
for original in (source / 'static').iterdir():
    assert (Path('/opt/mmod/static') / original.name).read_bytes() == original.read_bytes()
backups = sorted(Path('/var/backups').glob('mmod-preinstall-*/radio-checksums.json'))
assert backups
for name, digest in json.loads(backups[-1].read_text()).items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest, 'Radio file changed: ' + name
print('Dashboard health and unchanged source/config checks passed. Radio log source awaits station activation.')
