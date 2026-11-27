# FPV Uhyliant 2.0.7 per-user foundation

Version 2.0.7 moves the application from the protected `Program Files` directory to the current user's writable application directory:

`%LOCALAPPDATA%\Programs\FPV Uhyliant`

This is required so that future OTA releases can safely create `app\staging`, replace `app\current`, preserve `app\rollback`, and restart without administrator elevation.

## Migration

1. Install 2.0.7 once using Setup.exe.
2. Use the new Start menu or desktop shortcut.
3. Confirm that the application title shows 2.0.7 and opens maximized.
4. The old Program Files installation may then be removed separately.
5. Runtime data remains in `%LOCALAPPDATA%\FPV-Uhyliant`.

## Next validation

Publish 2.0.8 and validate `2.0.7 -> 2.0.8` using OTA only, without Setup.exe and without UAC.
