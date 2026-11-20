# FPV Uhyliant 2.0.3

- Fixed OTA package URL generation after the v2.0.2 malformed package-host incident.
- Added release-time URL validation before Ed25519 signing.
- Preserved SHA-256 package verification, signed manifests, atomic update, startup-OK and rollback.
