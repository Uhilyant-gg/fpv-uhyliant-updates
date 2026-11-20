# FPV Uhyliant 2.0.2

- Product window title is now `ФПВ Ухилянт 2.0.2`.
- Application runtime version is centralized in `src/app/version.py`.
- Windows application uses the FPV Uhyliant icon at runtime and in the executable/installer.
- Windows release focuses on `FPV-Uhyliant-Setup-2.0.2.exe` as the primary user asset.
- PyInstaller excludes several unused Qt modules conservatively while retaining Qt Quick/QML dependencies.
- Existing Ed25519 manifest verification, SHA-256 package verification, signed test-channel OTA, startup-OK and rollback are preserved.
- User-facing updater status strings were corrected to UTF-8 Ukrainian text.
