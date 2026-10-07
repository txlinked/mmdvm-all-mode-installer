# MMDVM All-Mode Installer with MMOD Dashboard

Reference target: Dell Wyse 3040 running Debian 13 amd64. The same release targets other Debian 13 x86_64 PCs. Debian 12 and 32-bit x86 are not supported by this binary build.

This separate project packages g4klx radio programs with the existing [txlinked/mmod](https://github.com/txlinked/mmod) dashboard. The bundled MMOD V2.0.8 dashboard includes full-stack timer scope fixes. `manifest.json` pins upstream commits and the dashboard archive checksum.

Included: MMDVM-Host, DMRGateway, YSFGateway, DGIdGateway, P25Gateway, NXDNGateway, M17Gateway, DAPNETGateway, ircddbgatewayd and DMR2YSF. See [station setup](STATION-SETUP.md) for mode and hardware requirements.

The stack includes a local Mosquitto broker for current upstream MQTT dependencies. The dashboard reads console logs; it does not need a rewritten MQTT UI. Reflector directory provisioning, callsign/ID, network credentials and hardware calibration remain station setup tasks.

## Install a built release

Download the `mmod-stack-VERSION-debian13-amd64.tar.gz` release asset and its `SHA256SUMS` from the chosen GitHub repository. Verify the archive, extract it, and run:

```bash
sha256sum --ignore-missing --check SHA256SUMS
mkdir mmod-stack
tar -xzf mmod-stack-0.1.0-rc4-debian13-amd64.tar.gz -C mmod-stack
cd mmod-stack
sudo bash install.sh --site 'Your Repeater'
```

For monitoring an existing station config, supply `--ini /absolute/path/MMDVM.ini`. This does not migrate it to the new host version. The dashboard listens on all IPv4 interfaces (`0.0.0.0`) on port 8000 by default: use any reachable LAN, ZeroTier, or WireGuard/44net address. No local IP is required. Legacy `--bind` arguments are ignored. Existing firewall and routing rules still apply. Debian and Python runtime dependencies require internet access; no radio compiler is installed or run on end-user systems.

Radio services are installed stopped, with a station-ready condition. Existing radio configuration is preserved. Existing unmanaged units cause installation to stop for review. A timestamped configuration/application backup is saved in `/var/backups/mmod-stack-*`; dashboard installation also makes its original backups. Repeating installation preserves managed station configuration and existing dashboard credentials. Upgrades require stopping the radio services first.

## Build once for distribution

On Debian 13 amd64:

```bash
sudo apt-get install build-essential git libmosquitto-dev libwxgtk3.2-dev nlohmann-json3-dev python3
bash build.sh
bash verify.sh work/build-0.1.0-rc4/bundle
```

The GitHub workflow builds pinned sources and runs executable checks. A matching `vVERSION` tag publishes a prerelease containing binaries, checksums, and the corresponding upstream source archive for GPL compliance. Workflow dispatch provides downloadable build artifacts without publishing. The initial package remains a prerelease until modem and over-the-air tests pass.

Runtime binaries are stored under `/opt/mmod-radio`; station configuration is under `/etc/mmod-radio`. MMOD remains under `/opt/mmod`, with its original updater. Updating the dashboard does not replace radio binaries. Update upstream pins deliberately and create a new release to upgrade the radio stack.

Installer scripts use the MIT license. The bundled g4klx programs retain their GPL licenses and are accompanied by the corresponding source release asset. The dashboard retains its original license.

## Recovered configuration
MMOD V2.0.5 restores Administration Ã¢â€ â€™ Configuration for station, modem, frequencies, modes and gateway settings. Existing values and passwords are preserved. Review and Save create a backup; Apply restarts only affected running services.

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

TS2 TG7100334 maps to converter TG100334 and FCS00334 (TEXAS-NEXUS). Return traffic gets the 7000000 prefix back. TS2 TG7100000Ã¢â‚¬â€œ7199999 selects FCS rooms; TG7200000Ã¢â‚¬â€œ7299999 selects YSF rooms from your provisioned directory. TG7004000 unlinks. The helper reserves TG7000000Ã¢â‚¬â€œ7999998 from other TS2 networks, retains TS1 and existing CBridge routes such as TG3148, preserves network passwords and modem frequencies, and backs up edited files. It refuses an occupied enabled Network 5.

Room auto-disconnect is selectable in the dashboard after login: expand Auto-disconnect beside a linked YSF/FCS room and set Enable plus 1–1440 RF-inactivity minutes. BrandMeister uses a whole-timeslot dynamic timer because its disconnect command clears the slot. Administration contains the global timer enable switch and default (10 minutes for a fresh full-stack install). Static links and AllStar are exempt. Existing timer settings are preserved. The full installer removes the converter's independent timer so it cannot override dashboard Off/static selections. Keying the same room again sends a new link command. A command submission is not proof of a remote link: check YSFGateway logs for `Linked to FCS003-34`, then verify audio with radios. This release remains a prerelease while that audio test is pending.

On upgrades the installer preserves existing INI files. Run the helper explicitly to adopt this routing. Do not run the cross-mode YSFGateway and a native YSF modem gateway on the same local ports. These bundled dashboard changes apply only to this full-stack package.
