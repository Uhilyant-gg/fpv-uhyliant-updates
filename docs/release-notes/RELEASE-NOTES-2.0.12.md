# FPV Uhyliant 2.0.12

Test-channel build focused on the guarded OpenIPC camera update lifecycle.

- route-aware bounded camera discovery and verified OpenIPC identity;
- session-only masked camera credentials;
- password-capable SSH transport without password in process argv;
- authentication and identity revalidation before fixed `sysupgrade -k -r`;
- reboot-pending state followed by bounded rediscovery;
- fresh OpenIPC, platform, sensor and observed firmware verification;
- no automatic destructive transport activation;
- no inferred Ultimate/Lite variant;
- expanded safety, secret-boundary and packaged smoke tests.
