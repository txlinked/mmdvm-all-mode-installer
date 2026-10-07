# 0.1.0-rc4

Run `sudo bash install.sh --site 'Your Repeater'`. Dashboard listens on `0.0.0.0:8000` by default, including reachable LAN, ZeroTier and WireGuard/44net addresses. Legacy `--bind` arguments are ignored; obsolete fixed-address proxy services are retired.

Bundles MMOD V2.0.8 with full-stack fixes. Dashboard controls select auto-disconnect On/Off and RF-inactivity minutes per YSF/FCS room and per BrandMeister timeslot. Static links, AllStar and unsupported modes are exempt. Fresh installs start at 10 minutes; updates preserve saved settings and the legacy 15-minute dashboard default when no saved policy exists.

The converter has no independent inactivity timer. Cross-mode setup preserves dashboard policy; optional `--room-timeout` changes only the FCS00334 room policy. The global dashboard switch must also be enabled. Re-keying a room submits its link command again after a dashboard unlink. Station INIs and credentials remain preserved during upgrades.

Prerelease: hardware and over-the-air validation still required.
