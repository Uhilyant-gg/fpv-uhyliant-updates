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
  *Next:* write the address, port and payload type into the camera over SSH.
- Cloud = **ZeroTier** (ready-made service instead of an own server). One ZeroTier network per camera:
  sharing = authorizing a PC in that network, revoking = deauthorizing it, archive = deauthorizing
  the camera. Addresses never need syncing: a camera's address follows from the network and node IDs
  (RFC4193). *Done:* local ZeroTier service status, the PC's node ID, joining the camera's network,
  direct/relayed path and latency on the card.
  - Equal rights with ZeroTier: everyone who shares a camera needs permission to manage its network
    (a shared controller account/organization, or a self-hosted controller such as ztnet). To decide.
- Camera firmware: official OpenIPC plus selected add-ons installed during or after flashing:
  ZeroTier, a flight-controller bridge (raw bytes to/from the network), settings sync, watchdog.
  The station checks over SSH whether an add-on fits (firmware variant, flash size, free space).

## Flight control over Starlink
- Control is taken automatically and never taken away by the station; the flight controller has its
  own failsafe for link loss.

## Map and wind
- Satellite base map (Esri World Imagery); download a selected area in advance, or automatically
  around the drone. Orientation: north-up, track-up or follow the drone. Picture-in-picture (movable,
  resizable) or a separate window. Points by MGRS coordinates.
- Position source selectable: flight-controller GPS or Starlink.
- Wind: forecast for the drone's point and altitude; arrow and speed on the map; no wind warnings.

## Out of scope
- Payload-drop / impact-point calculators are not built by this project.
