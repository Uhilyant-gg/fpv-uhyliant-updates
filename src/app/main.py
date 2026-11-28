import argparse, json, os, sys, time, traceback
from pathlib import Path

PROCESS_STARTED_AT = time.monotonic()
# FFmpeg in Qt Multimedia opens only whitelisted protocols. Video pushed by the camera
# ("Static IP") arrives as RTP over UDP described by a local SDP file.
os.environ.setdefault('QT_FFMPEG_PROTOCOL_WHITELIST', 'file,crypto,data,rtsp,rtp,udp,tcp')
from version import VERSION, WINDOW_TITLE

DATA = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'FPV-Uhyliant'


def write_json_atomic(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(payload), encoding='utf-8')
    os.replace(tmp, path)


def signal_ok(t):
    if t:
        write_json_atomic(DATA / 'startup-ok.json', {'status': 'ok', 'token': t, 'version': VERSION})


def signal_smoke(path):
    write_json_atomic(
        Path(path), {'status': 'ok', 'version': VERSION, 'pid': os.getpid(), 'timestamp': int(time.time())}
    )


def log_startup():
    DATA.mkdir(parents=True, exist_ok=True)
    try:
        (DATA / 'startup.log').write_text(traceback.format_exc(), encoding='utf-8')
    except Exception:
        pass


def compile_qml_smoke(here):
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    engine = QQmlEngine()
    errors = []
    for path in sorted(here.glob('*.qml')):
        component = QQmlComponent(engine)
        component.loadUrl(path.as_uri())
        if component.isError():
            errors.extend(f'{path.name}: {error.toString()}' for error in component.errors())
    if errors:
        raise RuntimeError('QML smoke compile failed:\n' + '\n'.join(errors))


def main():
    a = argparse.ArgumentParser(add_help=False)
    a.add_argument('--self-test', action='store_true')
    a.add_argument('--mavlink-self-test', action='store_true')
    a.add_argument('--smoke-test', action='store_true')
    a.add_argument('--smoke-marker')
    a.add_argument('--install-root')
    a.add_argument('--startup-token')
    a.add_argument('--startup-diagnostics', action='store_true')
    a.add_argument('--startup-marker')
    a.add_argument('--acceptance-report', action='store_true')
    a.add_argument('--first-run-acceptance-smoke', action='store_true')
    x, _ = a.parse_known_args()
    here = Path(__file__).resolve().parent
    from startup_harness import StartupHarness, default_path, read_startup_acceptance, run_import_probes, run_qt_probe

    harness = StartupHarness(x.startup_marker or default_path(DATA), VERSION, PROCESS_STARTED_AT)
    if x.acceptance_report:
        report = read_startup_acceptance(harness.path)
        print(json.dumps(report, ensure_ascii=False, separators=(',', ':')))
        return 0 if report['status'] == 'accepted' else 1
    harness.mark('main-entry')
    harness.mark('launch', detail={'phase': 'process-started'})
    if x.self_test:
        harness.mark('self-test')
        print(json.dumps({'status': 'ok', 'version': VERSION}))
        return 0
    if x.startup_diagnostics:
        try:
            run_import_probes(harness)
            return run_qt_probe(harness, sys.argv)
        except BaseException as exc:
            harness.failed('startup-diagnostics', exc)
            raise
    if x.smoke_test:
        harness.mark('smoke-qtcore-begin')
        from PySide6.QtCore import QCoreApplication

        harness.mark('smoke-qtcore-complete')
        app = QCoreApplication(sys.argv)
        compile_qml_smoke(here)
        signal_smoke(x.smoke_marker or str(DATA / 'smoke-test-ok.json'))
        harness.mark('smoke-complete')
        return 0
    harness.mark('qt-imports-begin')
    from PySide6.QtCore import QUrl, QTimer
    from PySide6.QtGui import QFont, QGuiApplication, QIcon
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuickControls2 import QQuickStyle

    harness.mark('qt-imports-complete')
    harness.mark('application-imports-begin')
    from backend import Station, HomeDashboard
    from devices_routeaware import Devices
    from updater_engine import Updater
    from video import VideoWorkspaceRuntime
    from stream_workspace import StreamWorkspace
    from firmware_center import FirmwareCenter
    from firmware_executor import FirmwareExecutor
    from firmware_update_session import FirmwareUpdateSession
    from openipc_firmware_acquisition import OpenIPCFirmwareAcquisition
    from camera_credentials import CameraCredentials
    from camera_presets import CameraPresets
    from camera_preset_executor import CameraPresetExecutor
    from link_diagnostics import LinkDiagnostics
    from diagnostic_events import DiagnosticEvents
    from timeline_runtime import TimelineRuntime
    from display_runtime import DisplayRuntime
    from diagnostics_runtime import DiagnosticsRuntime
    from hardware_e2e_runtime import HardwareE2ERuntime
    from station_backup import StationBackup
    from automatic_backup import AutomaticBackup
    from windows_secret_store import WindowsCredentialSecretStore
    from pairing import JsonMetadataStore, PairingRegistry
    from mavlink_runtime import MavlinkRuntime
    from msp_runtime import MspRuntime
    from crsf_runtime import CrsfRuntime
    from serial_telemetry import MspSerialTransport, CrsfSerialTransport
    from telemetry_provider import CrsfProvider, MavlinkProvider, MspProvider, TelemetryRouter
    from vehicle import VehicleRuntime
    from controller_discovery import default_source as default_controller_source
    from controller_onboarding import ControllerOnboarding
    from controller_profile_store import JsonControllerProfileStore
    from controller_runtime import ControllerRuntime
    from flight_alerts_runtime import FlightAlertsRuntime
    from presets_runtime import PresetsRuntime
    from dvr_runtime import DvrRuntime
    from link_monitor import LinkMonitor
    from link_doctor import LinkDoctor
    import video_presets
    from rtp_relay import RtpRelay
    from connection_profiles import ConnectionStore
    from connections_runtime import ConnectionsRuntime
    from zerotier_local import ZeroTierLocal
    import camera_setup
    import camera_inspect
    from settings_presets import PresetStore

    harness.mark('application-imports-complete')
    DATA.mkdir(parents=True, exist_ok=True)
    qtlog = DATA / 'qt-startup.log'

    def qt_message(kind, context, message):
        line = f'{time.strftime("%Y-%m-%d %H:%M:%S")} {int(kind)} {message}'
        try:
            with qtlog.open('a', encoding='utf-8') as f:
                f.write(line + '\n')
        except Exception:
            pass
        print(line, file=sys.stderr, flush=True)

    harness.mark('qgui-application-begin')
    app = QGuiApplication(sys.argv)
    app.setFont(QFont('Segoe UI'))
    app.setApplicationName('FPV-Uhyliant')
    app.setApplicationVersion(VERSION)
    harness.mark('qgui-application-complete')
    harness.mark('protocol-runtimes-begin')
    m = MavlinkRuntime(auto_start=False)
    msp = MspRuntime()
    crsf = CrsfRuntime()
    msp_serial = MspSerialTransport(msp)
    crsf_serial = CrsfSerialTransport(crsf)
    harness.mark('protocol-runtimes-complete')
    if x.mavlink_self_test:
        QTimer.singleShot(0, m.start)
        QTimer.singleShot(350, app.quit)
        rc = app.exec()
        m.shutdown()
        msp_serial.stop()
        crsf_serial.stop()
        print(json.dumps({'status': 'ok', 'backend': 'mavlink', 'telemetry': 'not simulated'}))
        return rc
    icon = here / 'fpv-uhyliant.ico'
    if icon.exists():
        app.setWindowIcon(QIcon(str(icon)))
    harness.mark('application-objects-begin')
    QQuickStyle.setStyle('Basic')
    e = QQmlApplicationEngine()
    s = Station()
    d = Devices()
    harness.mark('restore', detail={'savedDevices': d.count})
    home = HomeDashboard(d)
    video = VideoWorkspaceRuntime(d)
    v = video.primary
    secondary = video.secondary
    streams = StreamWorkspace(d)
    fw = FirmwareCenter(d)
    acquisition = OpenIPCFirmwareAcquisition(fw, DATA / 'firmware-cache')
    fwexec = FirmwareExecutor(fw)
    credentials = CameraCredentials()
    presets = CameraPresets(d)
    presetexec = CameraPresetExecutor(presets)
    links = LinkDiagnostics()
    automatic = AutomaticBackup(DATA / 'automatic-backups', WindowsCredentialSecretStore(), d, s)
    preset_store = PresetStore(DATA / 'presets.json')
    backup = StationBackup(d, automatic, station=s, presets=preset_store)
    pairing = PairingRegistry(metadata_store=JsonMetadataStore(DATA / 'pairing-trust.json'))
    telemetry = TelemetryRouter([MavlinkProvider(m), MspProvider(msp), CrsfProvider(crsf)])
    vehicle = VehicleRuntime(telemetry, v)
    u = Updater(x.install_root, s.canInstallUpdate, network=not x.first_run_acceptance_smoke)
    diag_events = DiagnosticEvents()
    timeline = TimelineRuntime()
    fwsession = FirmwareUpdateSession(fwexec, d, events=diag_events)
    diag = DiagnosticsRuntime(VERSION, d, links, telemetry, u, diag_events, DATA, video)
    hardware_e2e = HardwareE2ERuntime(d, diag, credentials, fw, fwsession)
    app._runtime_refs = (
        e,
        s,
        d,
        home,
        video,
        v,
        secondary,
        streams,
        fw,
        acquisition,
        fwexec,
        fwsession,
        credentials,
        presets,
        presetexec,
        links,
        backup,
        pairing,
        telemetry,
        vehicle,
        u,
        diag_events,
        timeline,
        diag,
        hardware_e2e,
        m,
        msp,
        crsf,
        msp_serial,
        crsf_serial,
    )
    harness.mark('application-objects-complete')
    d.streamsChanged.connect(streams.autoSelect)
    streams.autoSelect()
    pairing.reconcile()
    display_runtime = DisplayRuntime(app)
    controller_source = default_controller_source()
    controller = ControllerRuntime(
        ControllerOnboarding(controller_source, JsonControllerProfileStore(DATA / 'controller-profiles.json'))
    )
    from controller_actions import ControllerActions

    controller_actions = ControllerActions(controller_source, DATA / 'controller-actions.json')
    app._runtime_refs = app._runtime_refs + (display_runtime, controller, controller_actions)
    home.setController(controller)
    flight_alerts = FlightAlertsRuntime(telemetry, s)
    presets = PresetsRuntime(preset_store, s)
    backup.restored.connect(presets.reload)
    dvr_runtime = DvrRuntime()
    link_monitor = LinkMonitor()

    def configure_camera(host, address, port):
        session = [(credentials.username or 'root', credentials.secret())]
        return camera_setup.configure_push(
            host,
            address,
            port,
            session + list(camera_setup.DEFAULT_CREDENTIALS),
            lambda h, u, p: camera_setup.CameraShell(h, u, p, DATA / 'camera_known_hosts'),
        )

    inspector = camera_inspect.InspectorPool(
        lambda: [(credentials.username or 'root', credentials.secret())] + list(camera_setup.DEFAULT_CREDENTIALS),
        lambda h, u, p: camera_setup.CameraShell(h, u, p, DATA / 'camera_known_hosts'),
    )

    connections = ConnectionsRuntime(
        d,
        ConnectionStore(DATA / 'connections.json'),
        camera_setup=configure_camera,
        camera_inspect=inspector.inspect,
        camera_inspect_close=inspector.close_all,
        zerotier=ZeroTierLocal(),
        listen=not x.first_run_acceptance_smoke,
        sdp_folder=DATA / 'push-video',
        relay=RtpRelay,
    )
    from starlink_runtime import StarlinkRuntime

    def dish_shell(host):
        logins = [(u, p) for u, p in [(credentials.username or 'root', credentials.secret())] if p]
        username, password = (logins + list(camera_setup.DEFAULT_CREDENTIALS))[0]
        return camera_setup.CameraShell(host, username, password, DATA / 'camera_known_hosts')

    starlink_dish = StarlinkRuntime(d, connections, dish_shell)
    from camera_audio import AudioRuntime
    from camera_features import CameraFeaturesRuntime

    def not_armed():
        return (telemetry.telemetry or {}).get('armed') is not True

    camera_features = CameraFeaturesRuntime(d, connections, dish_shell, may_restart_video=not_armed)
    camera_audio = AudioRuntime(
        d, connections, camera_features, logins=lambda: camera_logins(), store_path=DATA / 'camera-audio.json'
    )
    if not x.first_run_acceptance_smoke:
        camera_features.start()
    link_doctor = LinkDoctor(link_monitor, d, connections, starlink=starlink_dish, camera=camera_features)
    from fc_link import FcLinkRuntime

    fc_link = FcLinkRuntime(
        d,
        connections,
        dish_shell,
        DATA / 'fc-link.json',
        mavlink=m,
        msp=msp,
        crsf=crsf,
        router=telemetry,
        may_probe=not_armed,
    )
    from extra_windows import ExtraWindowsRuntime

    extra_windows = ExtraWindowsRuntime(d, streams, DATA / 'extra-windows.json', host_resolver=connections.host_for)
    camera_logins = lambda: (
        [(credentials.username or 'root', credentials.secret())]
        + list(  # noqa: E731
            camera_setup.DEFAULT_CREDENTIALS
        )
    )
    video_preset_runtime = video_presets.VideoPresetsRuntime(
        video_presets.VideoPresetStore(DATA / 'video-presets.json'),
        d,
        connections,
        lambda host, lines: video_presets.run_on_camera(
            host,
            camera_logins(),
            lambda h, u, p: camera_setup.CameraShell(h, u, p, DATA / 'camera_known_hosts'),
            lines,
        ),
    )
    v.host_resolver = connections.host_for
    secondary.host_resolver = connections.host_for
    v.push_resolver = connections.push_url_for
    dvr_runtime.recordingChanged.connect(lambda: s.setRecordingActive(dvr_runtime.recording))

    def feed_auto():
        # Once a second in flight: how the link behaves, for the "Auto" video preset.
        device_id = d.activeId
        kind = connections.selected.get(device_id, '')
        status = connections.statuses.get(device_id, {}).get(kind, {})
        details = link_doctor.details
        video_preset_runtime.observe(
            {
                'lost': link_monitor.lost,
                'lossPct': details.get('lossPct', 0),
                'jitterMs': details.get('jitterMs', 0),
                'latencyMs': status.get('latencyMs'),
                'smoothingMs': details.get('smoothingMs', 0),
            }
        )

    link_doctor.changed.connect(feed_auto)
    from flight_log import BlackBoxRuntime

    def flight_sample():
        # Once a second in flight: what the station sees, for the black box.
        device_id = d.activeId
        kind = connections.selected.get(device_id, '')
        status = connections.statuses.get(device_id, {}).get(kind, {})
        details = link_doctor.details
        tel = telemetry.telemetry or {}
        dish = starlink_dish.status if starlink_dish.available else {}
        sample = {
            'fps': link_monitor.fps,
            'lost': link_monitor.lost,
            'frameSize': link_monitor.frameSize,
            'latencyMs': status.get('latencyMs'),
            'verdictLevel': link_doctor.level,
            'verdictText': link_doctor.text if link_doctor.level != 'ok' else '',
            'preset': video_preset_runtime.label,
            'recording': dvr_runtime.recording,
            'windows': extra_windows.openCount,
            'sound': camera_audio.playing,
        }
        if wind_runtime.available:
            sample['windMs'] = wind_runtime.wind.get('speedMs')
            sample['windFromDeg'] = wind_runtime.wind.get('fromDeg')
        for key in ('lossPct', 'jitterMs', 'kbps', 'smoothingMs', 'internet'):
            if key in details:
                sample[key] = details[key]
        for key in (
            'armed',
            'flightMode',
            'batteryVoltage',
            'batteryRemaining',
            'altitude',
            'groundSpeed',
            'heading',
            'satellites',
            'homeDistance',
            'linkQuality',
        ):
            if tel.get(key) is not None:
                sample[key] = tel[key]
        if dish:
            sample['starlinkLatencyMs'] = dish.get('latencyMs')
            sample['starlinkDropPct'] = dish.get('dropPct')
            sample['starlinkObstructed'] = bool(dish.get('currentlyObstructed'))
        return sample

    def flight_header():
        device_id = d.activeId
        kind = connections.selected.get(device_id, '')
        label = next((t['label'] for t in connections.types if t.get('key') == kind), kind)
        return {'camera': d.activeName, 'link': label, 'station': WINDOW_TITLE}

    black_box = BlackBoxRuntime(flight_sample, flight_header)
    from map_marks import MapMarksRuntime

    map_marks = MapMarksRuntime(DATA / 'map-marks.json')
    from wind import WindRuntime

    wind_runtime = WindRuntime(telemetry)
    from map_tiles import MapTilesRuntime

    map_tiles = MapTilesRuntime(DATA / 'map-tiles', telemetry, serve=not x.first_run_acceptance_smoke)
    from link_test import LinkTestRuntime

    def link_test_sample():
        device_id = d.activeId
        kind = connections.selected.get(device_id, '')
        status = connections.statuses.get(device_id, {}).get(kind, {})
        sample = {'reachable': status.get('state') == 'available', 'latencyMs': status.get('latencyMs')}
        if link_monitor.watching:
            details = link_doctor.details
            sample.update(video=True, fps=link_monitor.fps, lost=link_monitor.lost)
            # Video that arrives is an answer too (a camera that pushes to a static IP is not pinged).
            sample['reachable'] = sample['reachable'] or (not link_monitor.lost and link_monitor.fps > 0)
            if kind == 'static':
                sample.update(latencyMs=None, pushed=True)
            for key in ('lossPct', 'jitterMs', 'smoothingMs'):
                if key in details:
                    sample[key] = details[key]
        return sample

    link_test = LinkTestRuntime(link_test_sample, probe=lambda: connections.probeSelected(d.activeId))
    app._runtime_refs = app._runtime_refs + (
        starlink_dish,
        camera_features,
        camera_audio,
        black_box,
        link_test,
        map_marks,
        wind_runtime,
        map_tiles,
        fc_link,
        flight_alerts,
        presets,
        dvr_runtime,
        connections,
        link_monitor,
        link_doctor,
    )
    ctx = e.rootContext()
    for name, obj in [
        ('station', s),
        ('homeDashboard', home),
        ('devicesModel', d),
        ('videoRuntime', v),
        ('secondaryVideoRuntime', secondary),
        ('videoWorkspaceRuntime', video),
        ('streamWorkspace', streams),
        ('firmwareCenter', fw),
        ('firmwareAcquisition', acquisition),
        ('firmwareExecutor', fwexec),
        ('firmwareUpdateSession', fwsession),
        ('cameraCredentials', credentials),
        ('cameraPresets', presets),
        ('cameraPresetExecutor', presetexec),
        ('linkDiagnostics', links),
        ('stationBackup', backup),
        ('pairingRegistry', pairing),
        ('mavlinkRuntime', m),
        ('mspSerial', msp_serial),
        ('crsfSerial', crsf_serial),
        ('telemetryRuntime', telemetry),
        ('vehicleRuntime', vehicle),
        ('timelineRuntime', timeline),
        ('displayRuntime', display_runtime),
        ('updater', u),
        ('diagnosticsRuntime', diag),
        ('hardwareE2ERuntime', hardware_e2e),
        ('controllerRuntime', controller),
        ('flightAlerts', flight_alerts),
        ('presetsRuntime', presets),
        ('dvrRuntime', dvr_runtime),
        ('linkMonitor', link_monitor),
        ('linkDoctor', link_doctor),
        ('extraWindows', extra_windows),
        ('starlinkDish', starlink_dish),
        ('cameraFeatures', camera_features),
        ('cameraAudio', camera_audio),
        ('blackBox', black_box),
        ('linkTest', link_test),
        ('mapMarks', map_marks),
        ('windRuntime', wind_runtime),
        ('mapTiles', map_tiles),
        ('fcLink', fc_link),
        ('controllerActions', controller_actions),
        ('videoPresets', video_preset_runtime),
        ('connectionsRuntime', connections),
    ]:
        ctx.setContextProperty(name, obj)
    ctx.setContextProperty('appWindowTitle', WINDOW_TITLE)
    ctx.setContextProperty('mapTilesDir', str(DATA / 'map-cache'))
    harness.mark('qml-load-begin')
    e.load(QUrl.fromLocalFile(str(here / 'Main.qml')))
    harness.mark('qml-load-complete')

    def shutdown():
        hardware_e2e.reset()
        credentials.clear()
        dvr_runtime.shutdown()
        connections.stop()
        camera_features.stop()
        camera_audio.setActive(False)
        black_box.setActive(False)
        map_tiles.shutdown()
        fc_link.setActive(False)
        inspector.close_all()
        video.stopAll()
        links.clear()
        pairing.clearPending()
        m.shutdown()
        msp_serial.stop()
        crsf_serial.stop()
        controller.stopIdleObservation()
        controller.deactivate()
        u.shutdown()

    if not e.rootObjects():
        harness.mark('launch', 'error', {'reasonCode': 'qml-root-not-created'})
        shutdown()
        raise RuntimeError('QML root object failed to load')
    app.aboutToQuit.connect(shutdown)
    root = e.rootObjects()[0]

    def start_discovery():
        if x.first_run_acceptance_smoke:
            harness.mark(
                'discovery',
                detail={
                    'mode': 'network-free-packaged-first-run-fixture',
                    'networkRequestsSuppressed': True,
                    'started': False,
                },
            )
            return
        connections.start()
        try:
            d.discoverOpenIPC()
            harness.mark('discovery', detail={'started': True, 'savedDevices': d.count})
        except Exception as exc:
            harness.failed('discovery', exc)

    def show_home():
        root.showMaximized()
        app.processEvents()
        visible = root.isVisible()
        harness.mark('window-visible', 'ok' if visible else 'error', {'windowVisible': visible})
        start_discovery()
        harness.mark('health', detail={'health': home.health, 'summary': home.summary})
        harness.mark(
            'devices',
            detail={
                'devices': [{'type': item.get('type', '')} for item in d.items],
                'verifiedCount': home.verifiedCount,
            },
        )
        action_available = bool(home.nextAction.get('available'))
        harness.mark(
            'next-action',
            'ok' if action_available else 'error',
            {'available': action_available, 'action': home.nextAction.get('action')},
        )
        if x.first_run_acceptance_smoke:
            QTimer.singleShot(0, app.quit)

    QTimer.singleShot(0, show_home)
    if not x.first_run_acceptance_smoke:
        QTimer.singleShot(0, m.start)
        QTimer.singleShot(1500, controller.startIdleObservation)
    QTimer.singleShot(1200, lambda: signal_ok(x.startup_token))
    QTimer.singleShot(1200, lambda: harness.mark('startup-ready'))
    harness.mark('event-loop-begin')
    code = app.exec()
    # Destroy QML before the Python objects it binds to; otherwise bindings re-evaluate against
    # already-deleted context objects during interpreter teardown ("Cannot read property of null").
    from PySide6.QtCore import QEvent

    for window in e.rootObjects():
        window.deleteLater()
    app.sendPostedEvents(None, QEvent.Type.DeferredDelete.value)
    root = None
    e.deleteLater()
    app.sendPostedEvents(None, QEvent.Type.DeferredDelete.value)
    del e
    return code


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except BaseException:
        log_startup()
        raise
