#!/usr/bin/env python3
"""Apply the MMOD native room control and RF standby patch to pinned sources."""
from pathlib import Path
import sys

p = Path(sys.argv[1]) / 'DMR2YSF.cpp'
s = '#include <cstdlib>\n#include <cstring>\n' + p.read_text()
if 'MMOD native room control' in s:
    raise SystemExit('Source already patched; use a clean pinned checkout')

def replace(old, new):
    global s
    assert s.count(old) == 1, 'Pinned converter source changed: ' + old[:70]
    s = s.replace(old, new, 1)

replace('void CDMR2YSF::connectYSF(unsigned int id)\n{\n', '''void CDMR2YSF::connectYSF(unsigned int id)
{
	// MMOD native room control: the working Waco MQTT approach.
	if (id == m_tgUnlink) {
		if (::system("/usr/bin/timeout 5 /usr/bin/mosquitto_pub -h 127.0.0.1 -p 1883 -q 1 -t ysf-gateway/command -m Unlink") == 0)
			m_lastTG = 0U;
		return;
	}
	if (id >= 100000U && id <= 299999U) {
		const bool fcs = id < 200000U;
		const unsigned int room = id - (fcs ? 100000U : 200000U);
		char command[256U];
		::snprintf(command, sizeof(command), "/usr/bin/timeout 5 /usr/bin/mosquitto_pub -h 127.0.0.1 -p 1883 -q 1 -t ysf-gateway/command -m '%s %05u'", fcs ? "LinkFCS" : "LinkYSF", room);
		if (::system(command) == 0) {
			m_lastTG = id;
			LogMessage("MMOD room command sent: TG %u -> %s%05u", id, fcs ? "FCS" : "YSF", room);
		} else LogMessage("MMOD room command failed for TG %u", id);
		return;
	}
''')
p.write_text(s)
print('Applied MMOD native room control; dashboard exclusively owns inactivity timers')
