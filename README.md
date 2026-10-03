# MMDVM All-Mode Installer with MMOD Dashboard

Reference target: Dell Wyse 3040 running Debian 13 amd64. The same release targets other Debian 13 x86_64 PCs. Debian 12 and 32-bit x86 are not supported by this binary build.

This separate project packages g4klx radio programs with the existing [txlinked/mmod](https://github.com/txlinked/mmod) dashboard. Dashboard Python files and UI assets are shipped unchanged. `manifest.json` pins upstream commits and the dashboard archive checksum.

Included: MMDVM-Host, DMRGateway, YSFGateway, DGIdGateway, P25Gateway, NXDNGateway, M17Gateway, DAPNETGateway and ircddbgatewayd. See [station setup](STATION-SETUP.md) for mode and hardware requirements.

The stack includes a local Mosquitto broker for current upstream MQTT dependencies. The unchanged dashboard reads console logs; it does not need a rewritten MQTT UI. Reflector directory provisioning, callsign/ID, network credentials and hardware calibration remain station setup tasks.

## Install a built release

Download the `mmod-stack-VERSION-debian13-amd64.tar.gz` release asset and its `SHA256SUMS` from the chosen GitHub repository. Verify the archive, extract it, and run:

```bash
sha256sum --ignore-missing --check SHA256SUMS
mkdir mmod-stack
tar -xzf mmod-stack-0.1.0-rc2-debian13-amd64.tar.gz -C mmod-stack
cd mmod-stack
sudo bash install.sh --bind YOUR_LOCAL_IP --site 'Your Repeater'
```

For monitoring an existing station config, supply `--ini /absolute/path/MMDVM.ini`. This does not migrate it to the new host version. The web port defaults to the unchanged dashboard's port 8000. Debian and Python runtime dependencies require internet access; no radio compiler is installed or run on end-user systems.

Radio services are installed stopped, with a station-ready condition. Existing radio configuration is preserved. Existing unmanaged units cause installation to stop for review. A timestamped configuration/application backup is saved in `/var/backups/mmod-stack-*`; dashboard installation also makes its original backups. Repeating installation preserves managed station configuration and existing dashboard credentials. Upgrades require stopping the radio services first.

## Build once for distribution

On Debian 13 amd64:

```bash
sudo apt-get install build-essential git libmosquitto-dev libwxgtk3.2-dev nlohmann-json3-dev python3
bash build.sh
bash verify.sh work/build-0.1.0-rc2/bundle
```

The GitHub workflow builds pinned sources and runs executable checks. A matching `vVERSION` tag publishes a prerelease containing binaries, checksums, and the corresponding upstream source archive for GPL compliance. Workflow dispatch provides downloadable build artifacts without publishing. The initial package remains a prerelease until modem and over-the-air tests pass.

Runtime binaries are stored under `/opt/mmod-radio`; station configuration is under `/etc/mmod-radio`. MMOD remains under `/opt/mmod`, with its original updater. Updating the dashboard does not replace radio binaries. Update upstream pins deliberately and create a new release to upgrade the radio stack.

Installer scripts use the MIT license. The bundled g4klx programs retain their GPL licenses and are accompanied by the corresponding source release asset. The dashboard retains its original license.

## Recovered configuration
MMOD V2.0.5 restores Administration → Configuration for station, modem, frequencies, modes and gateway settings. Existing values and passwords are preserved. Review and Save create a backup; Apply restarts only affected running services.
