# Публікація update repository

1. Створити GitHub repository, наприклад `fpv-uhyliant-updates`.
2. Розпакувати цей шаблон у корінь repository та push у branch `main`.
3. У GitHub repository Settings -> Pages вибрати GitHub Actions як source.
4. Після першого deployment GitHub Pages надасть URL сайту.
5. Використати цей URL як `BaseUrl` під час формування release manifest.
6. Підписати manifest локально приватним Ed25519 ключем через `tools/finalize_release.ps1`.
7. Commit/push тільки підписаний `release.json` та package. Приватний ключ не додавати.
8. Manifest URL для станції: `<Pages URL>/test/release.json`.

## Приклад локальної команди

PowerShell:

    .\tools\finalize_release.ps1 `
      -Channel test `
      -Version 1.5.1 `
      -Build 1510 `
      -Package .\test\packages\fpv-uhyliant-1.5.1-win64.zip `
      -BaseUrl https://OWNER.github.io/fpv-uhyliant-updates `
      -PrivateKey C:\secure\fpv-release-private-key.pem `
      -KeyId fpv-uhyliant-test-2026 `
      -Notes "Перший online update"

До появи реальної Pages URL не підписуйте manifest із placeholder URL, бо package URL входить у підписані дані.
