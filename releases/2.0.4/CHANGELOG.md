# FPV Uhyliant 2.0.4

- Introduced a packaged Windows launcher and update helper that do not require Python on the user PC.
- Installer now creates an OTA-ready `app/current` layout and shortcuts launch through `FPV-Uhyliant-Launcher.exe`.
- OTA payload is a built Windows application directory rather than Python source files.
- Preserved Ed25519 manifest verification, SHA-256 package verification, startup-OK and rollback.
