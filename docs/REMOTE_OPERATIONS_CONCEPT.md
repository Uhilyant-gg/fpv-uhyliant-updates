# Remote operations: agreed concept

This records decisions agreed with the product owner, so later work builds on them.
"Done" marks what is in the station today; everything else is planned.

## Hardware path
- OpenIPC camera (mainly SigmaStar SSC30KQ; other models possible).
- The flight controller is wired to the camera (MAVLink or CRSF/MSP, chosen automatically or by the
  technician from the camera's settings preset). There is no ELRS receiver on the drone.
- Starlink Mini on the drone is the main link. The station may also be on Starlink; the station's
  Starlink is not managed by the app.
- All processing (telemetry parsing, map, wind) runs on the PC, not on the camera.

## Accounts and access
- A local account on the station (name and password) works without internet or a server. It moves
  to another PC as a password-encrypted file; later it can be linked to the cloud with the same identity.
- **All participants have equal rights to a camera.** Whoever first adds a camera shares it with other
  accounts; everyone with access can share it further, archive and restore it. There are no roles.
- Archive: anyone with access can archive and restore. Not while someone is flying the camera.
  Who archived or restored and when is logged. An archived camera fully loses access to the server.
  *Done locally:* archive, restore, delete only from the archive (with confirmation), kept in backups.

## Connections
- Before flying, the pilot picks a connection type on the camera card; "Fly" lights up only for a
  type that is reachable right now. *Done:* Local, Static IP/DDNS, ZeroTier, Starlink IPv6 with live
  status probed every 5 s; the video uses the chosen address.
- **Static IP** = the pilot's public ("white") IPv4 from the provider. Starlink gives the drone a shared
  CGNAT IPv4, so the station cannot reach the camera over IPv4; instead the camera sends RTP video to
  the pilot's address. *Done (station):* each camera gets its own UDP port (5600, 5602, ...); the card
  shows "waiting for camera" / "camera sends" from incoming packets; the ports are freed for the player
  while flying; "Bind to this network" finds the public address, detects a grey (CGNAT) address and
  forwards the port on the router via UPnP (or says which port to forward manually); the player opens
  the stream through a local SDP file (RTP payload type 97 for H.265, 96 for H.264).
  *Done (camera):* as soon as the camera answers on the station's local network and the address is known,
  the station configures the camera itself over SSH (majestic `outgoing.server`/`outgoing.enabled`, reload),
  reads its codec, remembers that it is configured and re-applies it when the address or port changes.
  Login tries the session password, then the OpenIPC factory password, and asks only if both fail.
  The camera's SSH host key is remembered on first use; a different key later is refused. The RTP payload
  type is learnt from the packets that arrive. Tapping "Static IP" on a card without an address binds
  the network automatically.
- Cloud = **ZeroTier** (ready-made service instead of an own server). One ZeroTier network per camera:
  sharing = authorizing a PC in that network, revoking = deauthorizing it, archive = deauthorizing
  the camera. Addresses never need syncing: a camera's address follows from the network and node IDs
  (RFC4193). *Done:* local ZeroTier service status, the PC's node ID, joining the camera's network,
  direct/relayed path and latency on the card.
  - Equal rights with ZeroTier: everyone who shares a camera needs permission to manage its network
    (a shared controller account/organization, or a self-hosted controller such as ztnet). To decide.
- Reading the camera instead of typing (*done*): whenever a camera is reachable (local network or ZeroTier)
  the station reads over SSH, with read-only commands, its ZeroTier node and network IDs, its public IPv6,
  firmware variant/version, flash size and free space. ZeroTier IDs fill in by themselves unless a person
  entered other values; the Starlink IPv6 is taken only when the camera is seen through ZeroTier (in the
  field, so the address is Starlink's). Read at once when the camera appears and then every 5 seconds over one
  SSH session that stays open; never in flight (the session is closed before the flight); a failed login is
  retried after a minute.
- Camera firmware: official OpenIPC plus selected add-ons installed during or after flashing:
  ZeroTier, a flight-controller bridge (raw bytes to/from the network), settings sync, watchdog.
  The station checks over SSH whether an add-on fits (firmware variant, flash size, free space).

## Flight control over Starlink
- Control is taken automatically and never taken away by the station; the flight controller has its
  own failsafe for link loss.

## Link-loss diagnosis (agreed 2026-11-28)
The pilot must see at once where the chain camera → Starlink → internet → pilot's PC → decoder broke,
in plain words, and the station fixes what it can by itself.
1. Stream analysis on the PC: packets arriving, loss, jitter, bitrate, packets without frames.
2. Internet check on the pilot's PC.
3. Starlink dish data: outage causes, obstruction map, position and heading (also for the map).
4. Camera health from a firmware helper: CPU temperature and load, video service, real bitrate.
5. Video vs telemetry: video gone but telemetry alive means the camera, not the network.
6. The banner names the cause ("Пропав інтернет на ПК пілота", "Starlink: перешкода в небі", ...).
7. Automatic bitrate reduction on a weak link: **a separate video-stream preset** the pilot chooses,
   not always on.
8. Flight black box: every flight writes its own log with all details into **a separate folder**
   (its own setting, like the DVR folder); a short summary after landing.
9. A 20-second link test in Preflight before take-off.
Order: 1+2+6, then 3, then 4+5 with telemetry forwarding, then 8+9, then 7 on real hardware.

## Video presets, streams and controls (agreed 2026-11-28)
- Flight menu holds only what is needed in the air; every other setting lives in the home menu.
- The pilot sees the stream itself: codec, size, frame rate, real bitrate, loss, how often a full
  frame comes, and what the camera is set to.
- Video presets belong to each camera and change the camera's own settings, in flight too.
- Bitrate is controlled per stream: by presets and by a quick change on the flight bar; an "Auto"
  preset moves between the camera's own presets by itself to hold a target latency: one step
  down after 3 bad seconds (at most every 10 s), one step up after 30 good seconds.
- PC keyboard: key 1 turns on "Auto"; keys 2…0 switch the camera presets, 2 is the weakest link,
  up to 0. Choosing a preset by hand turns Auto off.
- A controller channel swaps the streams (main ↔ additional).
- The presets are built by the station (owner's choice, 2026-11-28): for each of nine bitrates the
  largest picture that still gets enough data per pixel to stay free of blocks, never below 30 fps
  and 60 fps as soon as the bitrate carries it; an even (CBR) stream; a short full-frame interval on
  weak links. The pilot may edit any preset and rebuild them all.
- Starlink on the drone carried at most ~6 Mbit/s in the owner's tests and works reliably up to
  ~2.5 Mbit/s: the ladder runs 0.5–6 Mbit/s with most steps at or below 2.5.
- A stream that is not shown is paused so it spends no bitrate.
- Windows: at the start of a flight only the main stream is shown. Layouts are switched by the
  pilot (flight bar, keys, click on the small window); the small window is dragged to a corner and
  resized by the pilot. The station never moves or arranges windows by itself. No second controller
  switch for layouts; the existing one swaps the streams.
- Additional windows (agreed 2026-11-28): a left side panel of the flight screen holds one icon per
  additional stream (a click opens its window, another closes it and stops the stream) and a layouts
  button. Up to three windows. On a window, small buttons appear while the mouse is over it: swap
  with the main video, full screen, to another display (only when one is connected), close; the
  window is moved by dragging and resized from its bottom-left corner; a click on its picture swaps
  it with the main video. Layout presets: "only the main video", "as last time", and arrangements
  the pilot saved; nothing opens unless the pilot presses it.
  Windows over the main video never lie over each other: a dropped or enlarged window stops next to
  its neighbour, shrinks if it must, or stays where it was.
- Delay target: at most 150 ms from the camera to the pilot's screen. A small smoothing buffer on
  the PC is allowed inside that budget.
- Additional camera (thermal) on the camera's USB through UVC or a capture card: first tried on the
  official OpenIPC firmware, without a custom build. Picture-in-picture made on the camera to save
  bitrate comes after the separate stream works.
- Side panel without captions (agreed 2026-11-28): video streams at the top (only those present),
  sound, map and layouts at the bottom; square tiles with an icon of the source (camera,
  USB, thermal, map, sound) and its number (1 is the main video); the window of a stream carries
  the same icon and number. The name, what a click does and the settings (⚙ in the corner under the
  mouse, or the right button) appear under the mouse.
- Streams appear by themselves (agreed 2026-11-28): every 15 s, also in flight, the station asks the
  camera over SSH whether its second stream (video1) is on and whether a USB video device is
  plugged in; present streams show up on the side panel, gone ones disappear (their settings stay).
- USB video is encoded by the camera itself (majestic `usbcam.codec: transcode`, RTSP `/stream=3`).
  Only firmware with the `usbcam` keys can do it (per the OpenIPC wiki: Goke gk7205v200/v500 OTG
  builds); there the station switches it on by itself while the drone is not armed (it restarts the
  camera's video for a moment). On other cameras the hardware panel says why there is no USB stream.
  Still to verify on hardware: the RTSP path and the bitrate control of the USB stream.
- Sound from the camera's microphone: majestic Lite/Ultimate only (the FPV build has no audio).
  The station plays `/audio.alaw` (64 kbit/s at 8 kHz; falls back to `/audio.pcm`) with at most
  ~120 ms buffered, mutes with M or the "Звук" tile (a muted sound is not fetched, no bitrate), and
  sets the camera's microphone (on/off, sensitivity, 8/16/48 kHz) from the sound panel.

## Map and wind
- Satellite base map (Esri World Imagery); download a selected area in advance, or automatically
  around the drone. Orientation: north-up, track-up or follow the drone. Picture-in-picture (movable,
  resizable) or a separate window. Points by MGRS coordinates.
- Position source selectable: flight-controller GPS or Starlink.
- Wind: forecast for the drone's point and altitude; arrow and speed on the map; no wind warnings.

## Out of scope
- Payload-drop / impact-point calculators are not built by this project.
