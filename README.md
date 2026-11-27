# FPV Uhyliant

Наземна станція для FPV-польотів з камерами OpenIPC під Windows: пошук камер у мережі, відео, OSD з телеметрією (MAVLink / MSP / CRSF), попередження в польоті, пульт через USB, пресети налаштувань під кожен дрон, запис відео польоту в MP4 (кнопка «● REC» або F9), зашифровані резервні копії та безпечне оновлення прошивки камер і самої програми.

Програма написана на Python + PySide6 (Qt Quick / QML).

## З чого почати

| Що потрібно | Де |
|---|---|
| Запустити з вихідного коду (Windows) | `BOOTSTRAP.bat` у корені, далі `src/RUN.bat` |
| Як влаштована програма і правила безпеки | [`DEVELOPMENT_GUIDE.md`](DEVELOPMENT_GUIDE.md) |
| Що зроблено і що далі | [`DELIVERY_ROADMAP.md`](DELIVERY_ROADMAP.md) |
| Як має поводитися інтерфейс | [`PRODUCT_UX.md`](PRODUCT_UX.md) |
| Стан проєкту (машиночитний) | [`PROJECT_STATE.json`](PROJECT_STATE.json), [`PROJECT_STATE.md`](PROJECT_STATE.md) |
| Перевірка на реальній камері OpenIPC | [`HARDWARE_E2E.md`](HARDWARE_E2E.md) |
| Діагностика мережі, публікація оновлень | [`docs/`](docs/) |
| Нотатки до старих версій, архів | [`docs/release-notes/`](docs/release-notes/), [`docs/archive/`](docs/archive/) |

## Перевірки

```bash
pip install -r src/requirements-dev.txt
python tools/project_doctor.py
```

Project Doctor запускає компіляцію, усі тести застосунку й інструментів і перевіряє узгодженість документів стану. Той самий набір, а також lint (`ruff`), запуск інтерфейсу та перевірку Windows-пакета, виконує CI на кожен pull request.

Програмні тести й симулятор не замінюють перевірку на реальному обладнанні.

## Репозиторій оновлень

Цей репозиторій також є статичним сховищем оновлень для станції.

### Структура

- `test/release.json` - signed test channel manifest after publishing.
- `test/packages/` - update ZIP packages.
- `stable/` - stable channel, intentionally empty until a production release exists.
- `development/` - development channel placeholder.
- `tools/` - release build, signing, local serving and verification utilities.

### Публікація

The repository can be published as a static site. Set the station Manifest URL to:

`<BASE_URL>/test/release.json`

The package URL embedded in the signed manifest must use the same real public base URL.

### Підпис

Do not commit a private Ed25519 release key. The client contains only its pinned public key. `release.json` is signed before publication.

### Локальна перевірка

1. Produce/sign `test/release.json` using a private key matching `test/release-public-key.pem`.
2. Run `tools\\serve_local.bat` on Windows.
3. Use `http://127.0.0.1:8080/test/release.json` as the station manifest URL.

The checked-in `release.unsigned.json` intentionally contains `__BASE_URL__` and is not a publishable signed manifest.
