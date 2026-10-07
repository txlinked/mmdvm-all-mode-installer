# Station setup

The installer leaves radio services stopped pending station setup. The test board passes its firmware query and receives DMR calls; end-to-end cross-mode audio confirmation is pending.

1. Connect a working USB data cable. Check `lsusb`, `dmesg`, and `ls -l /dev/serial/by-id/`. Use a stable `/dev/serial/by-id/...` modem path when available. Do not assume a C-Media audio device is the MMDVM modem.

   To check firmware without configuring or transmitting, run `sudo python3 probe-modem.py /dev/serial/by-id/YOUR_DEVICE`. This utility sends only the upstream version query and refuses a serial device already in use. The Wyse 3040 test board identifies as **MMDVM_HS_Dual_Hat v1.5.2**, using protocol 1. That legacy protocol does not report individual mode capability flags; do not assume it supports every mode available in the installed software.
2. Back up and review existing station configuration. Existing `/opt/MMDVMHost` and `/opt/DMRGateway` files are preserved. New managed configuration lives under `/etc/mmod-radio` and uses disabled modes and networks. The release does not migrate old MMDVMHost configuration automatically; current upstream uses `Protocol=uart` and `UARTPort=...`, which differ from older releases.
3. Set the licensed callsign, station ID, correct RX/TX frequencies, duplex setting, modem levels, and modem protocol/path. Enable only supported modes. Hardware firmware determines available modes; the installer does not flash firmware.
4. Set gateway addresses, network credentials, hosts files and local UDP port pairs. DMRGateway and each network need your station settings. Choose YSFGateway or DGIdGateway; do not run both on the same local port. The included D-Star and XLX reflector files are pinned snapshots and should be reviewed for currency. Current YSF/P25/NXDN gateways need JSON directory files; M17 needs its hosts file. Obtain these from a source you are authorized to use and save them under the corresponding `/opt/mmod-radio/data/PROGRAM` directory (for example, `/opt/mmod-radio/data/YSFGateway/YSFHosts.json`). Upstream's old RefCheck direct download URLs currently return 404; its [current service](https://hostfiles.refcheck.radio/) requires a callsign and access token. No token is bundled, and these missing directories must be configured before network use.
5. The current MMDVM-Host supports D-Star, DMR, YSF, P25 Phase 1, NXDN, POCSAG and FM. M17Gateway is included, but requires a separate compatible M17 host/modem path. DMR2YSF is included. Other cross-mode converters and AllStar/Asterisk remain separate.
6. When ready, create `sudo touch /etc/mmod-radio/station-ready`, then start only the configured services: for example `sudo systemctl enable --now dmrgateway mmdvmhost`. Do not start every gateway indiscriminately.
7. Verify service logs with `journalctl -u mmdvmhost -f` and the MMOD dashboard. The unchanged dashboard captures host console logs from the journal. Test each configured mode with a radio and confirm network routing.

The dashboard retains its existing login and administration behavior. On a fresh installation, the upstream installer sets `admin` / `mmodadmin`; change this in Administration before allowing access from other networks. Existing credentials are preserved. The default web port remains 8000.

The dashboard listens on all IPv4 interfaces on port 8000. Open `http://<server-IP>:8000/` using the LAN, ZeroTier, or WireGuard/44net address. The installer does not change firewall rules; existing firewall rules must allow the networks you intend to use.

## DMR to YSF/FCS on TS2

DMR2YSF is prebuilt from pinned juribeparada/MMDVM_CM sources with the working Waco native MQTT room-linking approach. No compiler runs during installation. After setting your station callsign and DMR ID, review and apply:

```bash
sudo mmod-configure-dmr2ysf
sudo mmod-configure-dmr2ysf --apply
sudo touch /etc/mmod-radio/station-ready
sudo systemctl enable --now mosquitto
sudo systemctl restart ysfgateway dmrgateway dmr2ysf
sudo systemctl enable ysfgateway dmrgateway dmr2ysf
```

TS2 TG7100334 maps to converter TG100334 and FCS00334 (TEXAS-NEXUS). Return traffic gets the 7000000 prefix back. TS2 TG7100000–7199999 selects FCS rooms; TG7200000–7299999 selects YSF rooms from your provisioned directory. TG7004000 unlinks. The helper reserves TG7000000–7999998 from other TS2 networks, retains TS1 and existing CBridge routes such as TG3148, preserves network passwords and modem frequencies, and backs up edited files. It refuses an occupied enabled Network 5.

Use the dashboard Auto-disconnect control beside a supported YSF/FCS room to enable or disable its timer and set RF-inactivity minutes. BrandMeister timers apply to the whole timeslot, because clearing dynamic groups clears that slot. Static links and AllStar are exempt. Administration controls the global enable switch and default minutes. Fresh full-stack installs default to 10 minutes; updates preserve saved choices or the legacy 15-minute dashboard default. Incoming network traffic does not reset RF inactivity.

The converter has no independent inactivity timer. Running the setup helper preserves dashboard selections; optional `--room-timeout 0` disables the FCS00334 room timer and `--room-timeout 25` selects 25 minutes for that room. The global switch must also be enabled and Static still takes precedence. Keying the same room again sends a new link command. A command submission is not proof of a remote link: check YSFGateway logs for `Linked to FCS003-34`, then verify audio with radios. This release remains a prerelease while that audio test is pending.

On upgrades the installer preserves existing INI files. Run the helper explicitly to adopt this routing. Do not run the cross-mode YSFGateway and a native YSF modem gateway on the same local ports. These bundled dashboard changes apply only to this full-stack package.
