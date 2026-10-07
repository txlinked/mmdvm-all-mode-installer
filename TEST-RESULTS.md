# rc4 verification

This report replaces rc3 results; rc3 binary checks do not verify the changed converter.

Local checks passed on Windows with Python 3.12:

- Setup routing and station configuration preservation; Off and Static dashboard settings survive setup; converter compatibility environment remains disabled.
- Fresh dashboard default is enabled at 10 minutes. Updates retain saved policy byte-for-byte or preserve the legacy implicit 15-minute default.
- Bundled dashboard checksum and extraction.
- RF-only room expiry, independent room settings, whole-timeslot BrandMeister RF activity, other-slot isolation, and Static/Off/unsupported-mode exemptions.
- Global timer API persistence, input validation, unsupported-mode rejection and queued timeout cancellation after Off/Static/policy changes.
- Network migration preserves the dashboard port and disables old proxy units; no local-interface enumeration is required for wildcard binding.
- The revised converter patch applies to manifest-pinned sources. Linked-room JavaScript passes Node syntax checking.

Required Debian CI checks before release publication:

- All installer shell syntax and argument tests.
- Dashboard per-room and BrandMeister slot API writes using real Linux file locks.
- Complete builds of every pinned radio program, including the changed DMR2YSF converter.
- Native converter link/unlink/relink and failed-command tests; AMBE voice-bit roundtrip.
- Generated bundle checksums, x86_64 ELF architecture, runtime dependencies and executable smoke checks.

The release workflow runs these checks before uploading artifacts or publishing. No full stack has been deployed to a repeater. Hardware and over-the-air validation remain prerequisites for promotion beyond prerelease.
