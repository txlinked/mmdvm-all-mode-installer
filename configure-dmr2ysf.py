#!/usr/bin/env python3
"""Review/apply the Waco TS2 cross-mode layout without replacing station INIs."""
import argparse
import configparser
import datetime
import json
import os
from pathlib import Path
import re
import shutil


def parse(text):
    c = configparser.ConfigParser(interpolation=None, strict=False)
    c.optionxform = str
    c.read_string(text)
    return c


def update(text, section, key, value):
    lines = text.splitlines()
    if '[' + section + ']' not in lines:
        lines += ['', '[' + section + ']']
    start = lines.index('[' + section + ']') + 1
    end = next((i for i in range(start, len(lines)) if lines[i].startswith('[')), len(lines))
    matches = [i for i in range(start, end) if re.match(r'^\s*' + re.escape(key) + r'\s*=', lines[i])]
    for i in reversed(matches):
        del lines[i]
    if value is not None:
        lines.insert(start, key + '=' + str(value))
    return '\n'.join(lines) + '\n'


def subtract(lo, hi, blocked):
    parts = [(lo, hi)]
    for a, b in blocked:
        result = []
        for x, y in parts:
            if b < x or a > y:
                result.append((x, y))
            else:
                if x < a:
                    result.append((x, a - 1))
                if b < y:
                    result.append((b + 1, y))
        parts = result
    return parts


def plan(root):
    cfg = root / 'etc/mmod-radio'
    files = {name: (cfg / name).read_text() for name in ('MMDVM.ini', 'DMRGateway.ini', 'DMR2YSF.ini', 'YSFGateway.ini')}
    host = parse(files['MMDVM.ini'])
    if host.get('System Fusion Network', 'Enable', fallback='0') == '1':
        raise ValueError('Native YSF already uses the host gateway path; choose a separate cross-mode port layout first')
    callsign = host.get('General', 'Callsign')
    station_id = host.get('DMR', 'Id', fallback=host.get('General', 'Id', fallback=''))
    if not callsign or not station_id.isdigit() or int(station_id) <= 0:
        raise ValueError('Configure your callsign and DMR ID first')
    gateway = parse(files['DMRGateway.ini'])
    target = 'DMR Network 5'
    if gateway.has_section(target):
        existing = gateway.get(target, 'Name', fallback='').lower()
        if gateway.get(target, 'Enabled', fallback='0') == '1' and 'dmr2ysf' not in existing:
            raise ValueError('Network 5 is already enabled for another network; no settings changed')
    blockers = [(7000000, 7999998)]
    # Retain exclusive routes such as CBridge TG3148 when replacing BM PassAllTG2.
    for section in gateway.sections():
        if not section.startswith('DMR Network ') or section in ('DMR Network 1', target):
            continue
        if gateway.get(section, 'Enabled', fallback='0') != '1':
            continue
        for key, value in gateway.items(section):
            if re.fullmatch(r'TGRewrite\d*', key) and value.strip():
                values = [int(v.strip()) for v in value.split(',')]
                if len(values) == 5 and values[0] == 2:
                    blockers.append((values[1], values[1] + values[4] - 1))
    text = files['DMRGateway.ini']
    for section in gateway.sections():
        if not section.startswith('DMR Network ') or section == target:
            continue
        blocked = blockers if section == 'DMR Network 1' else blockers[:1]
        used = {key for key in gateway[section]}
        def add_route(value):
            nonlocal text
            index = next(i for i in range(1000) if 'TGRewrite' + str(i) not in used)
            key = 'TGRewrite' + str(index)
            used.add(key)
            text = update(text, section, key, value)
        for key, value in gateway.items(section):
            if re.fullmatch(r'TGRewrite\d*', key) and value.strip():
                nums = [int(v.strip()) for v in value.split(',')]
                if len(nums) != 5 or nums[0] != 2:
                    continue
                rfslot, rf, netslot, net, count = nums
                parts = subtract(rf, rf + count - 1, blocked)
                if parts == [(rf, rf + count - 1)]:
                    continue
                text = update(text, section, key, None)
                for a, b in parts:
                    add_route(f'{rfslot},{a},{netslot},{net + a - rf},{b - a + 1}')
            elif re.fullmatch(r'PassAllTG\d*', key) and value.strip() == '2':
                text = update(text, section, key, None)
                for a, b in subtract(1, 16777215, blocked):
                    add_route(f'2,{a},2,{a},{b - a + 1}')
    if gateway.has_section(target):
        for key in gateway[target]:
            if re.fullmatch(r'(TGRewrite|SrcRewrite|PassAllTG|PassAllPC)\d*', key):
                text = update(text, target, key, None)
    for key, value in {'Enabled': '1', 'Name': 'DMR2YSF', 'Id': station_id,
                       'Address': '127.0.0.1', 'Port': '62033', 'Local': '62034',
                       'Password': 'passw0rd', 'Location': '0', 'Debug': '0',
                       'TGRewrite0': '2,7000000,2,0,999999',
                       'SrcRewrite0': '2,0,2,7000000,999999'}.items():
        text = update(text, target, key, value)
    files['DMRGateway.ini'] = text
    for section, values in {
        'YSF Network': {'Callsign': callsign, 'GatewayAddress': '127.0.0.1', 'GatewayPort': '4200',
                        'LocalAddress': '127.0.0.1', 'LocalPort': '3200', 'Daemon': '0',
                        'FCSRooms': '/opt/mmod-radio/data/YSFGateway/FCSRooms.txt',
                        'DT1': '1,34,97,95,43,3,17,0,0,0', 'DT2': '0,0,0,0,108,32,28,32,3,8'},
        'DMR Network': {'Id': station_id, 'RptAddress': '127.0.0.1', 'RptPort': '62034',
                        'LocalAddress': '127.0.0.1', 'LocalPort': '62033',
                        'DefaultDstTG': '100334', 'TGUnlink': '4000',
                        'TGListFile': '/opt/mmod-radio/data/DMR2YSF/TG-YSFList.txt'},
        'DMR Id Lookup': {'File': '/opt/mmod-radio/data/DMR2YSF/DMRIds.dat'},
        'Log': {'FilePath': '/var/log/mmod-radio', 'FileRoot': 'DMR2YSF', 'DisplayLevel': '1'},
    }.items():
        for key, value in values.items():
            files['DMR2YSF.ini'] = update(files['DMR2YSF.ini'], section, key, value)
    for section, values in {
        'General': {'Callsign': callsign, 'Id': station_id, 'RptAddress': '127.0.0.1', 'RptPort': '3200',
                    'LocalAddress': '127.0.0.1', 'LocalPort': '4200', 'Daemon': '0'},
        'Network': {'Startup': '', 'Reconnect': '0', 'Revert': '0', 'InactivityTimeout': '0'},
        'FCS Network': {'Enable': '1', 'Rooms': '/opt/mmod-radio/data/YSFGateway/FCSRooms.txt'},
        'YSF Network': {'Hosts': '/var/lib/mmod-radio/YSFHosts.json'},
        'Remote Commands': {'Enable': '1'},
        'MQTT': {'Host': '127.0.0.1', 'Port': '1883', 'Name': 'ysf-gateway', 'Auth': '0'},
    }.items():
        for key, value in values.items():
            files['YSFGateway.ini'] = update(files['YSFGateway.ini'], section, key, value)
    return cfg, files, station_id, callsign


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--apply', action='store_true', help='Back up and save the reviewed routing')
    ap.add_argument('--root', type=Path, default=Path('/'), help=argparse.SUPPRESS)
    args = ap.parse_args()
    cfg, files, station_id, callsign = plan(args.root)
    print(f'{callsign} / {station_id}: TS2 TG7100334 -> converter TG100334 -> FCS00334; reverse TG mapping enabled.')
    print('Reserve TS2 TG7000000–7999998 for cross-mode; retain other network credentials and CBridge routes.')
    print('Room unlinks after 10 minutes without local RF; converter stays running.')
    if not args.apply:
        print('Review only. Run again with --apply to save; no services restarted.')
        return
    original_ysf = parse((cfg / 'YSFGateway.ini').read_text())
    old_path = original_ysf.get('YSF Network', 'Hosts', fallback='')
    old_hosts = args.root / old_path.lstrip('/') if old_path.startswith('/') else None
    state = args.root / 'var/lib/mmod-radio/YSFHosts.json'
    hosts = None
    if old_hosts and old_hosts != state and old_hosts.is_file():
        hosts = old_hosts.read_text()
        directory = json.loads(hosts)
        if not isinstance(directory, dict) or not isinstance(directory.get('reflectors'), list):
            raise ValueError('Existing YSF directory is invalid; no settings changed')
    backup = args.root / 'var/backups' / ('mmod-crossmode-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
    backup.mkdir(parents=True, mode=0o700)
    if hosts is not None or not state.exists():
        if state.exists():
            shutil.copy2(state, backup / 'YSFHosts.json')
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text(hosts if hosts is not None else '{"reflectors":[]}\n')
        state.chmod(0o640)
        if args.root == Path('/') and os.name == 'posix':
            shutil.chown(state, user='mmdvm', group='mmdvm')
    for name, text in files.items():
        p = cfg / name
        if p.read_text() != text:
            shutil.copy2(p, backup / name)
            p.write_text(text)
    data = args.root / 'opt/mmod-radio/data/DMR2YSF'
    data.mkdir(parents=True, exist_ok=True)
    table = data / 'TG-YSFList.txt'
    room_lines = table.read_text().splitlines() if table.exists() else []
    if table.exists():
        shutil.copy2(table, backup / table.name)
    room_lines = [line for line in room_lines if line.split(';', 1)[0].strip() != '100334']
    table.write_text('\n'.join(room_lines + ['100334;FCS00334']) + '\n')
    ids = data / 'DMRIds.dat'
    if ids.exists():
        original = ids.read_text()
        if not any(line.split()[:1] == [station_id] for line in original.splitlines()):
            shutil.copy2(ids, backup / ids.name)
            ids.write_text(original.rstrip() + '\n' + station_id + '\t' + callsign + '\n')
    print('Saved. Backup: ' + str(backup))
    print('Restart configured services: sudo systemctl restart ysfgateway dmrgateway dmr2ysf')


if __name__ == '__main__':
    main()
