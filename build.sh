#!/bin/bash
# Release builder only. End-user machines never run this script.
set -euo pipefail
cd "$(dirname "$0")"
[[ $(dpkg --print-architecture) == amd64 ]] || { echo 'Build requires amd64'; exit 1; }
version=${1:-0.1.0-rc2}
[[ $version =~ ^[0-9A-Za-z.+-]+$ ]] || exit 1
stage="$PWD/work/build-$version"
mkdir -p "$stage/src" "$stage/bundle/bin" "$stage/bundle/config" "$stage/bundle/data" "$stage/bundle/licenses" dist
cp install.sh manifest.json "$stage/bundle/"
cp accept-idle-dashboard.py "$stage/bundle/"
cp probe-modem.py "$stage/bundle/"
cp STATION-SETUP.md README.md RELEASE-NOTES.md LICENSE "$stage/bundle/"
cp vendor/mmod-source.tar.gz "$stage/bundle/"
python3 - <<'PY'
import hashlib,json,pathlib
manifest=json.load(open('manifest.json'))
assert hashlib.sha256(pathlib.Path('vendor/mmod-source.tar.gz').read_bytes()).hexdigest()==manifest['dashboard']['sha256'], 'Dashboard archive checksum mismatch'
PY
python3 - "$stage" <<'PY'
import json,sys,subprocess,pathlib
root=pathlib.Path(sys.argv[1]); manifest=json.load(open('manifest.json'))
for item in manifest['upstream']:
    name,commit=item['repo'],item['commit']; target=root/'src'/name
    if not (target/'.git').exists():
        target.mkdir(parents=True,exist_ok=True)
        subprocess.run(['git','init','--quiet',str(target)],check=True)
        subprocess.run(['git','-C',str(target),'remote','add','origin','https://github.com/g4klx/'+name+'.git'],check=True)
        subprocess.run(['git','-C',str(target),'fetch','--quiet','--depth','1','origin',commit],check=True)
    subprocess.run(['git','-C',str(target),'checkout','--quiet','--detach',commit],check=True)
    actual=subprocess.check_output(['git','-C',str(target),'rev-parse','HEAD'],text=True).strip()
    assert actual==commit
PY
jobs=${BUILD_JOBS:-2}
for repo in MMDVM-Host DMRGateway YSFClients P25Clients NXDNClients M17Gateway DAPNETGateway; do
  make -C "$stage/src/$repo" -j"$jobs"
done
make -C "$stage/src/ircDDBGateway" -j"$jobs" BUILD=release DATADIR=/opt/mmod-radio/data LOGDIR=/var/log/mmod-radio CONFDIR=/etc/mmod-radio ircDDBGateway/ircddbgatewayd
python3 - "$stage" <<'PY'
import json,sys,pathlib,shutil,subprocess,hashlib
root=pathlib.Path(sys.argv[1]); bundle=root/'bundle'; manifest=json.load(open('manifest.json'))
for item in manifest['programs']:
    source=root/'src'/item['repo']/item['binary']
    dest=bundle/'bin'/item['name']; shutil.copy2(source,dest)
    subprocess.run(['strip','--strip-unneeded',str(dest)],check=True)
    if item.get('config'): shutil.copy2(root/'src'/item['repo']/item['config'],bundle/'config'/item['config_name'])
    assets=bundle/'data'/item['name']; assets.mkdir(exist_ok=True)
    if item['name']=='ircddbgatewayd':
        shutil.copytree(root/'src'/item['repo']/'Data',assets,dirs_exist_ok=True)
        # ircDDB uses its compiled data path for voice announcements.
        shutil.copytree(root/'src'/item['repo']/'Data',bundle/'data',dirs_exist_ok=True)
    else:
        for f in source.parent.iterdir():
            if f.is_file() and f.suffix in ('.dat','.csv','.txt','.json') and f.name!='schema.json':shutil.copy2(f,assets/f.name)
        if (source.parent/'Audio').is_dir():shutil.copytree(source.parent/'Audio',assets/'Audio',dirs_exist_ok=True)
for item in manifest['upstream']:
    src=root/'src'/item['repo']; dest=bundle/'licenses'/item['repo']; dest.mkdir(exist_ok=True)
    for pattern in ('LICENSE*','COPYING*','LICENCE*'):
        for f in src.glob(pattern):
            if f.is_file(): shutil.copy2(f,dest/f.name)
with open(bundle/'SHA256SUMS','w') as out:
    for f in sorted(bundle.rglob('*')):
        if f.is_file() and f.name!='SHA256SUMS':out.write(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.relative_to(bundle).as_posix()+'\n')
PY
archive="mmod-stack-${version}-debian13-amd64.tar.gz"
tar -czf "dist/$archive" -C "$stage/bundle" .
tar --exclude=.git --exclude='*.o' --exclude='*.d' -czf "dist/mmod-stack-${version}-sources.tar.gz" -C "$stage" src
(cd dist; sha256sum "$archive" "mmod-stack-${version}-sources.tar.gz" > SHA256SUMS)
echo "Built dist/$archive"
