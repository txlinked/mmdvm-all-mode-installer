#!/bin/bash
# Install a previously built release. No compiler or source build is used.
set -euo pipefail
cd "$(dirname "$0")"
if [[ ${1:-} == --help ]]; then
  echo 'sudo bash install.sh [--port 8000] [--site NAME] [--ini EXISTING_INI]'
  echo 'Debian 13 amd64. Radio services remain stopped until station setup is complete.'
  exit 0
fi
[[ $(id -u) == 0 ]] || { echo 'Run as root'; exit 1; }
. /etc/os-release
[[ -d /run/systemd/system ]] || { echo 'Boot Debian with systemd before installation.'; exit 1; }
[[ $ID == debian && $VERSION_ID == 13 && $(dpkg --print-architecture) == amd64 ]] || {
  echo 'This release requires Debian 13 amd64 (Dell Wyse 3040 or other x86_64 PC).'; exit 1;
}
sha256sum --check --strict SHA256SUMS
dashboard_existing=0
[[ ! -e /etc/mmod/config.json && ! -e /opt/mmod/VERSION ]] || dashboard_existing=1
bind=0.0.0.0 port=8000 site='MMOD Test Repeater' ini=
while (($#)); do
  case $1 in
    --bind) echo 'Dashboard uses all IPv4 interfaces; --bind is ignored.' >&2;; --port) port=$2;; --site) site=$2;; --ini) ini=$2;;
    *) echo "Unknown option: $1" >&2; exit 1;;
  esac
  shift 2
done
if ! command -v python3 >/dev/null || ! command -v ip >/dev/null; then
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3 iproute2
fi
python3 - "$bind" "$port" "$ini" <<'PY'
import ipaddress,sys,json,subprocess,pathlib
a=ipaddress.IPv4Address(sys.argv[1]);p=int(sys.argv[2]);assert a.is_unspecified and 1024<=p<=65535
if sys.argv[3]:assert pathlib.Path(sys.argv[3]).is_file() and pathlib.Path(sys.argv[3]).is_absolute()
PY
# Refuse to replace a running radio stack or existing unmanaged unit.
python3 - <<'PY'
import json,subprocess,pathlib
for p in json.load(open('manifest.json'))['programs']:
    unit=p['service']+'.service'
    if subprocess.run(['systemctl','is-active','--quiet',unit]).returncode==0:raise SystemExit('Stop '+unit+' before upgrading')
    fragment=subprocess.run(['systemctl','show',unit,'--property=FragmentPath','--value'],capture_output=True,text=True).stdout.strip()
    f=pathlib.Path(fragment) if fragment else pathlib.Path('/etc/systemd/system')/unit
    if f.exists() and 'Managed by MMOD stack installer' not in f.read_text():raise SystemExit('Unmanaged service exists: '+unit)
PY
stamp=$(date -u +%Y%m%dT%H%M%S)-$$
backup=/var/backups/mmod-stack-$stamp
install -d -m 700 "$backup"
for path in /etc/mmod-radio /opt/mmod-radio /etc/mmod; do
  if [[ -e $path ]]; then
    name=${path#/}; name=${name//\//-}
    tar -czf "$backup/$name.tar.gz" -C / "${path#/}"
  fi
done
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends libmosquitto1 mosquitto mosquitto-clients libwxbase3.2-1t64 python3 python3-venv curl ca-certificates iproute2
id mmdvm >/dev/null 2>&1 || useradd --system --home /var/lib/mmod-radio --shell /usr/sbin/nologin mmdvm
usermod -a -G dialout mmdvm
install -d -m 755 /opt/mmod-radio/bin /opt/mmod-radio/data /etc/mmod-radio
install -d -m 750 -o mmdvm -g mmdvm /var/lib/mmod-radio /var/log/mmod-radio
install -m 755 configure-dmr2ysf.py /usr/local/sbin/mmod-configure-dmr2ysf
install -m 755 bin/* /opt/mmod-radio/bin/
# Keep station-owned room maps, ID additions and reflector directories on upgrade.
cp -an data/. /opt/mmod-radio/data/
install -m 644 manifest.json /opt/mmod-radio/manifest.json
export MMOD_STACK_BACKUP="$backup"
python3 - <<'PY'
import json,pathlib,shutil,configparser,os
manifest=json.load(open('manifest.json'));cfg=pathlib.Path('/etc/mmod-radio');units=pathlib.Path('/etc/systemd/system')
for p in manifest['programs']:
    target=cfg/p['config_name']
    if not target.exists():
        shutil.copy2(pathlib.Path('config')/p['config_name'],target)
        if p['name']!='ircddbgatewayd':
            c=configparser.ConfigParser(interpolation=None,strict=False);c.optionxform=str;c.read(target)
            for section in c.sections():
                for key in list(c[section]):
                    if key.lower() in ('enable','enabled','daemon'):c[section][key]='0'
            if p['name']=='MMDVM-Host':c['Modem']['Protocol']='null'
            if 'Log' in c:
                c['Log']['DisplayLevel']='1'
                if 'FilePath' in c['Log']:c['Log']['FilePath']='/var/log/mmod-radio'
            if p['name']=='DMR2YSF':
                for section,values in {
                    'YSF Network':{'GatewayAddress':'127.0.0.1','GatewayPort':'4200','LocalAddress':'127.0.0.1','LocalPort':'3200','FCSRooms':'/opt/mmod-radio/data/YSFGateway/FCSRooms.txt','DT1':'1,34,97,95,43,3,17,0,0,0','DT2':'0,0,0,0,108,32,28,32,3,8'},
                    'DMR Network':{'RptAddress':'127.0.0.1','RptPort':'62034','LocalAddress':'127.0.0.1','LocalPort':'62033','DefaultDstTG':'100334','TGListFile':'/opt/mmod-radio/data/DMR2YSF/TG-YSFList.txt'},
                    'DMR Id Lookup':{'File':'/opt/mmod-radio/data/DMR2YSF/DMRIds.dat'},
                    'Log':{'FilePath':'/var/log/mmod-radio','FileRoot':'DMR2YSF'},
                }.items():
                    if section not in c:c[section]={}
                    c[section].update(values)
            if p['name']=='YSFGateway':
                c['YSF Network']['Hosts']='/var/lib/mmod-radio/YSFHosts.json'
                c['FCS Network']['Rooms']='/opt/mmod-radio/data/YSFGateway/FCSRooms.txt'
            with target.open('w') as f:c.write(f,space_around_delimiters=False)
    target.chmod(0o640);shutil.chown(target,user='root',group='mmdvm')
    unit=units/(p['service']+'.service')
    if unit.exists():shutil.copy2(unit,pathlib.Path(os.environ['MMOD_STACK_BACKUP'])/unit.name)
    command='/opt/mmod-radio/bin/'+p['name']+' '+str(target)
    if p['name']=='ircddbgatewayd':command='/opt/mmod-radio/bin/ircddbgatewayd -foreground -confdir /etc/mmod-radio -logdir /var/log/mmod-radio'
    unit.write_text('[Unit]\n# Managed by MMOD stack installer\nDescription=MMOD '+p['name']+'\nAfter=network-online.target mosquitto.service\nWants=network-online.target\nConditionPathExists=/etc/mmod-radio/station-ready\n\n[Service]\nType=simple\nEnvironmentFile=-/etc/mmod-radio/room-timeout.env\nUser=mmdvm\nGroup=mmdvm\nSupplementaryGroups=dialout\nWorkingDirectory=/opt/mmod-radio/data/'+p['name']+'\nExecStart='+command+'\nRestart=on-failure\nRestartSec=5\nNoNewPrivileges=true\nProtectSystem=strict\nProtectHome=true\nReadWritePaths=/var/log/mmod-radio /var/lib/mmod-radio\nUMask=0027\n\n[Install]\nWantedBy=multi-user.target\n')
PY
# Current YSFGateway opens its JSON directory read/write, even when loading.
if [[ ! -e /var/lib/mmod-radio/YSFHosts.json ]]; then
  printf '{"reflectors":[]}\n' > /var/lib/mmod-radio/YSFHosts.json
  chown mmdvm:mmdvm /var/lib/mmod-radio/YSFHosts.json
  chmod 640 /var/lib/mmod-radio/YSFHosts.json
fi
systemctl daemon-reload
systemd-analyze verify /etc/systemd/system/{mmdvmhost,dmrgateway,ysfgateway,dgidgateway,p25gateway,nxdngateway,m17gateway,dapnetgateway,ircddbgateway,dmr2ysf}.service
stage=$(mktemp -d /tmp/mmod-dashboard.XXXXXXXX)
proxy_restore=0
proxy_units=()
cleanup_dashboard_stage() {
  if ((proxy_restore)); then
    for unit in "${proxy_units[@]}"; do systemctl start "$unit" || true; done
  fi
  case "$stage" in /tmp/mmod-dashboard.*) rm -rf -- "$stage";; esac
}
trap cleanup_dashboard_stage EXIT
tar -xzf mmod-source.tar.gz -C "$stage"
# Run the bundled full-stack dashboard installer.
[[ -n $ini ]] || ini=/etc/mmod-radio/MMDVM.ini
# Upstream's port check sees its own secondary-IP proxy as a conflicting process.
# Briefly stop only that dashboard socket and restore it on every exit path.
for unit in mmod-network.socket mmod-44net.socket mmod-network.service mmod-44net.service; do
  if systemctl is-active --quiet "$unit"; then proxy_units+=("$unit"); fi
done
if ((${#proxy_units[@]})); then
  proxy_restore=1
  systemctl stop "${proxy_units[@]}"
fi
if bash "$stage/mmod/install.sh" --bind "$bind" --port "$port" --site "$site" --ini "$ini" --host-service mmdvmhost.service 2>&1 | tee "$backup/dashboard-install.log"; then
  echo 'Original dashboard installer passed.'
else
  # Upstream requires an active radio log even on a fresh dashboard installation.
  # Accept only its exact no-log postcheck after verifying source, UI and configs.
  python3 accept-idle-dashboard.py "$backup/dashboard-install.log" "$stage/mmod" "http://127.0.0.1:$port"
  python3 /opt/mmod/link_status.py --prepare-access
  systemctl daemon-reload
  systemctl enable --now mmod-updates.timer
fi
python3 - <<'PY'
import json,pathlib
p=pathlib.Path('/etc/mmod/config.json');c=json.loads(p.read_text());m=json.load(open('manifest.json'))
c['services']=list(dict.fromkeys(c['services']+[x['service']+'.service' for x in m['programs']]))
c['backup_files']=list(dict.fromkeys(c['backup_files']+['/etc/mmod-radio/'+x['config_name'] for x in m['programs']]))
p.write_text(json.dumps(c,indent=2)+'\n')
PY
# Dashboard owns the room timer so per-link Off/static choices cannot be
# overridden by the converter's independent fallback timer.
if [[ -f /etc/mmod-radio/room-timeout.env ]]; then
  cp -a /etc/mmod-radio/room-timeout.env "$backup/room-timeout.env"
fi
printf 'MMOD_ROOM_IDLE_MINUTES=0\n' > /etc/mmod-radio/room-timeout.env
chmod 644 /etc/mmod-radio/room-timeout.env
python3 configure-dashboard-timer.py --existing "$dashboard_existing"
python3 /opt/mmod/network_access.py
proxy_restore=0
systemctl restart mmod mmod-collector.service
echo "Dashboard installed: http://<server-IP>:$port (all IPv4 interfaces)"
echo "Radio binaries installed; station configuration required. Backup: $backup"
echo 'DMR to Texas Nexus: review sudo mmod-configure-dmr2ysf, then run with --apply.'
echo 'See STATION-SETUP.md before creating /etc/mmod-radio/station-ready.'
