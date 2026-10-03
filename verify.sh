#!/bin/bash
set -euo pipefail
bundle=$(realpath "${1:?Supply bundle directory}")
cd "$bundle"
sha256sum --check --strict SHA256SUMS
python3 - <<'PY'
import json,hashlib,pathlib,subprocess,tarfile,tempfile
m=json.load(open('manifest.json'))
assert hashlib.sha256(pathlib.Path('mmod-source.tar.gz').read_bytes()).hexdigest()==m['dashboard']['sha256']
for p in m['programs']:
    binary=pathlib.Path('bin')/p['name']
    header=binary.read_bytes()[:20]
    assert header[:5]==b'\x7fELF\x02' and header[18:20]==b'\x3e\x00',p['name']+' is not x86_64 ELF'
    deps=subprocess.check_output(['ldd',str(binary)],text=True);assert 'not found' not in deps,deps
    if p['name']=='ircddbgatewayd':
        result=subprocess.run([str(binary),'-help'],capture_output=True,text=True,timeout=10)
        assert 'Usage:' in result.stdout+result.stderr
    else:
        result=subprocess.run([str(binary),'--version'],capture_output=True,text=True,timeout=10)
        assert result.returncode==0,(p['name'],result.stderr)
    print(p['name']+' executable smoke check passed')
print('Dashboard payload unchanged; binary architecture and dependencies verified')
PY
