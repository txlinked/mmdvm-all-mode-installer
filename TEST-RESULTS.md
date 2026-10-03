# MMOD installer test results

Test date: October 3, 2026, America/Chicago. Package: `0.1.0-rc1`, Debian 13 amd64.

## Tested equipment

- Dell Wyse 3040 Thin Client, Debian 13.6, x86_64.
- Existing MMDVMHost/DMRGateway files and an existing AllStar installation were present.
- Serial modem: `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0`.
- Version-only query identified `MMDVM_HS_Dual_Hat-v1.5.2`, protocol 1, firmware dated 20201108. No transmit, frequency, or mode-configuration commands were sent.

## Passed checks

- All eight pinned upstream repositories built successfully in an isolated Debian 13 amd64 container.
- All nine packaged executables passed x86_64 ELF, dynamic-library dependency and executable smoke checks, both in the build environment and on the Wyse.
- Installed programs: MMDVM-Host, DMRGateway, YSFGateway, DGIdGateway, P25Gateway, NXDNGateway, M17Gateway, DAPNETGateway and ircddbgatewayd.
- Release/archive checksums verified. A deliberately corrupted package was rejected before installation.
- The full installer completed on the Wyse using prebuilt radio binaries.
- A repeat installation completed successfully after both primary and secondary dashboard listeners had been used.
- Existing `/opt/MMDVMHost/MMDVM.ini` and `/opt/DMRGateway/DMRGateway.ini` remained byte-for-byte unchanged.
- Managed `/etc/mmod-radio` station configuration and dashboard credentials survived repeat installation unchanged.
- Dashboard Python files and UI assets matched the original bundled MMOD source. No dashboard source/UI changes were made.
- Dashboard HTTP health passed on both local LAN and ZeroTier listeners.
- Systemd unit verification passed. Radio host and all gateway services remain inactive; the station-ready marker is absent.
- Mosquitto listens only on loopback on the tested machine.

## Remaining validation and deployment work

Station callsign/ID, frequencies, modem levels, enabled modes, gateway credentials and reflector directories still require configuration. RF reception/transmission, network routing and every individual radio mode have not been tested. The protocol-1 board does not report individual capability flags; software availability does not establish hardware support for every mode. M17 requires a separate compatible host/modem path.

A clean-OS installation and installation on the user's later server have not been performed. GitHub Actions release automation is included but has not run on GitHub; the new repository name is pending.

TCP 8000 firewall rules for the LAN and ZeroTier subnets were not applied. Automatic approval review rejected those persistent access changes; explicit user approval remains pending. Local HTTP checks were performed through SSH.

The original dashboard installer requires a radio log even on a fresh station and rejects its own secondary-IP proxy during reinstalls. The separate stack installer handles these conditions, verifies the unchanged dashboard/configuration, and restores the dashboard proxy. It does not alter the dashboard code.
