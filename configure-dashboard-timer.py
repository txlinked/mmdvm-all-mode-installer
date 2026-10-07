#!/usr/bin/env python3
"""Seed the full-stack default once; preserve saved policy and legacy defaults."""
import argparse
import json
import os
from pathlib import Path
import shutil

def seed(root=Path('/'), existing=False):
    path = root / 'var/lib/mmod/state/dynamic-timer.json'
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    # MMOD V2.0.8 uses 15 minutes when no policy file exists. Updates retain it.
    with path.open('x') as stream:
        json.dump({'enabled': True, 'minutes': 15 if existing else 10}, stream)
        stream.write('\n')
    path.chmod(0o600)
    if root == Path('/') and os.name == 'posix':
        shutil.chown(path, user='mmod', group='mmod')
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--existing', choices=('0','1'), default='0')
    args = parser.parse_args()
    seed(existing=args.existing == '1')
