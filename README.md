# FPV Uhyliant Update Repository

Static update repository template for the FPV Uhyliant ground station.

## Layout

- `test/release.json` - signed test channel manifest after publishing.
- `test/packages/` - update ZIP packages.
- `stable/` - stable channel, intentionally empty until a production release exists.
- `development/` - development channel placeholder.
- `tools/` - release build, signing, local serving and verification utilities.

## Publishing model

The repository can be published as a static site. Set the station Manifest URL to:

`<BASE_URL>/test/release.json`

The package URL embedded in the signed manifest must use the same real public base URL.

## Important signing rule

Do not commit a private Ed25519 release key. The client contains only its pinned public key. `release.json` is signed before publication.

## Local test

1. Produce/sign `test/release.json` using a private key matching `test/release-public-key.pem`.
2. Run `tools\\serve_local.bat` on Windows.
3. Use `http://127.0.0.1:8080/test/release.json` as the station manifest URL.

The checked-in `release.unsigned.json` intentionally contains `__BASE_URL__` and is not a publishable signed manifest.
