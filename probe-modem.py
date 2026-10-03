#!/usr/bin/env python3
"""Query MMDVM firmware version only; never send mode, frequency, or TX commands."""
import argparse
import copy
import fcntl
import json
import os
from pathlib import Path
import select
import termios
import time
import tty


def probe(device):
    target = str(Path(device).resolve(strict=True))
    for entry in Path('/proc').glob('[0-9]*/fd/*'):
        try:
            if os.readlink(entry) == target:
                raise RuntimeError('Serial device is already in use: ' + target)
        except (FileNotFoundError, PermissionError):
            pass
    fd = os.open(target, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    previous = copy.deepcopy(termios.tcgetattr(fd))
    try:
        fcntl.ioctl(fd, termios.TIOCEXCL)
        tty.setraw(fd)
        settings = termios.tcgetattr(fd)
        settings[2] = (settings[2] & ~(termios.CSIZE | termios.PARENB | termios.CSTOPB | termios.CRTSCTS)) | termios.CS8 | termios.CLOCAL | termios.CREAD
        settings[4] = settings[5] = termios.B115200
        termios.tcsetattr(fd, termios.TCSANOW, settings)
        time.sleep(2)
        data = bytearray()
        for _ in range(3):
            os.write(fd, b'\xe0\x03\x00')  # MMDVM_GET_VERSION, as in upstream CModem::readVersion.
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                if not select.select([fd], [], [], 0.1)[0]:
                    continue
                data.extend(os.read(fd, 1024))
                while len(data) >= 3:
                    if data[0] != 0xE0 or data[1] < 4:
                        del data[0]
                        continue
                    length = data[1]
                    if len(data) < length:
                        break
                    frame = bytes(data[:length]); del data[:length]
                    if frame[2] != 0:
                        continue
                    protocol = frame[3]
                    if protocol not in (1, 2):
                        raise RuntimeError('Unexpected MMDVM protocol: ' + str(protocol))
                    offset = 4 if protocol == 1 else 23
                    if len(frame) <= offset:
                        raise RuntimeError('Incomplete firmware version response')
                    result = dict(device=device, protocol=protocol, firmware=frame[offset:].split(b'\x00', 1)[0].decode('ascii', errors='replace'))
                    if protocol == 2:
                        result['reported_modes'] = [name for bit, name in ((1,'D-Star'),(2,'DMR'),(4,'YSF'),(8,'P25'),(16,'NXDN'),(64,'FM')) if frame[4] & bit]
                        if frame[5] & 1:
                            result['reported_modes'].append('POCSAG')
                    else:
                        result['note'] = 'Legacy protocol does not report individual capability flags.'
                    return result
        raise RuntimeError('No MMDVM firmware response at 115200 baud')
    finally:
        termios.tcsetattr(fd, termios.TCSANOW, previous)
        os.close(fd)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('device', help='Stable /dev/serial/by-id/... path')
    args = parser.parse_args()
    print(json.dumps(probe(args.device), indent=2))
