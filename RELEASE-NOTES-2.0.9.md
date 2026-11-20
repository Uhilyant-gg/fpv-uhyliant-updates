# ФПВ Ухилянт 2.0.9

Тестова контрольна версія для інтеграційної перевірки Devices, SQLite, streams, video profiles та RTSP playback.

## Основні зміни

- Devices переведено на SQLite з міграцією legacy `devices.json`.
- Додано SQLite schema versioning і persistent `streams`.
- Кожен відеопотік може мати власний `video_profile_id`.
- Додано окрему persistent-модель `video_profiles`.
- Video profiles залишаються незалежними від camera/firmware presets та не застосовуються під час прошивки камер.
- Додано RTSP runtime для потоків активної камери.
- Додано реальне RTSP playback у UI через Qt Multimedia `MediaPlayer` + `VideoOutput`.
- Додано start/stop, F2, playback errors та базову RTSP diagnostics інформацію.
- Збережено OpenIPC discovery через mDNS, ONVIF, OpenIPC/Majestic fingerprint та локальне `/24` сканування з вибором мережевого інтерфейсу.

## Що перевірити

1. Оновлення на 2.0.9 через test OTA та запуск без повторного Setup.exe.
2. Міграцію існуючої бази Devices у SQLite зі збереженням пристроїв.
3. Пошук OpenIPC-камер, вибір інтерфейсу, скасування та повторний запуск discovery.
4. Додавання RTSP stream для активної камери.
5. Призначення окремого video profile конкретному stream та збереження після перезапуску.
6. Реальне відтворення RTSP, Stop/Start і клавішу F2.
7. Коректне повідомлення про помилку при недоступному RTSP endpoint.

## Важливі правила

- Camera preset і video profile є різними сутностями.
- Video profile не застосовується під час прошивки камери.
- BAT/fullflash призначений для камер, де вже встановлена відповідна OpenIPC прошивка, а не як універсальний основний метод прошивки.
