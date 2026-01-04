# Shiz-and-giggles Arena Concepts

This repository documents arena layouts and implementation guidance for fast-paced combat spaces. See `docs/arena_specs.md` for two ready-to-build arenas with item placement, lighting profiles, and navigation mesh notes.
# Shiz-and-giggles HUD Prototype

Static prototype showcasing a game HUD, pause/settings menu, and lobby flow.

## Features
- HUD with health/armor bars, ammo, timer, scoreboard toggle, crosshair, and kill feed animations.
- Pause/settings menu covering keybinds, mouse sensitivity, FOV, audio, network region, and graphics presets.
- Server browser with region/mode filters plus lobby join, ready check, and cosmetic team selection (usable in FFA).

## Usage
Open `index.html` in a modern browser. Use `Esc` to toggle the pause menu; refresh servers and join to simulate lobby readiness.
# Shiz-and-giggles Build + Test Harness

This repository provides a lightweight Python client/server simulation, nightly build pipeline, regression tests for player movement and weapon handling, and load-test tooling suitable for smoke-testing a dedicated server with 16+ synthetic clients.

## Quickstart
1. Install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .[dev]
   ```
2. Run the dedicated server:
   ```bash
   shiz-server --port 8765
   ```
3. Connect a client and issue a few moves:
   ```bash
   shiz-client --port 8765 --player-id tester --moves "1,0" "0,1" --fire
   ```
4. Run the movement/weapon regression tests:
   ```bash
   pytest
   ```
5. Load test with 16 synthetic clients:
   ```bash
   shiz-load-test --port 8765 --clients 16
   ```

## Nightly builds
The GitHub Actions workflow `.github/workflows/nightly.yml` builds debug-friendly client and dedicated server binaries with PyInstaller, runs regression tests, and uploads artifacts nightly. Artifacts include the changelog and version file.

## Packaging for itch.io / Steam private beta
Use `scripts/package_release.py` after running `scripts/build_artifacts.py` to bundle the latest build into `releases/<version>-<channel>.zip`. Pass `--itch-target` to push via `butler` or `--steam-script` to call `steamcmd` when available.

## Versioning and changelog
The current version lives in `VERSION` and is mirrored in `shizgiggles.__init__.__version__`. Update `CHANGELOG.md` with user-facing notes for each release.

## Playable client + dedicated server builds
1. Install Godot 4.2+ and expose it as `godot` on your PATH or via `GODOT_BIN=/path/to/godot`.
2. Build the binaries (Godot exports plus PyInstaller Python tools) into `dist/`:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .[dev]
   python scripts/build_artifacts.py
   ```
   - Use `--skip-godot` if you only need the Python CLI builds; `--godot-bin /path/to/godot` overrides the Godot binary.
3. Run the dedicated arena server export (auto-hosts on port `8910`):
   ```bash
   ./dist/godot/server/ShizAndGigglesServer.x86_64 --headless
   ```
4. Launch the playable client export and host/join a match from the main menu:
   ```bash
   ./dist/godot/client/ShizAndGiggles.x86_64
   ```
5. Package a release-ready zip (Godot builds, PyInstaller CLIs, changelog, and version metadata):
   ```bash
   python scripts/package_release.py --channel beta
   ```
   The archive is written to `releases/<version>-<channel>.zip` and is ready for itch.io/Steam uploads using the optional flags.

# Performance Tuning Plan

This document outlines the actionable steps to optimize frame timing, rendering, and networking for the target hardware, with special attention to worst-case 16-player chaos scenarios.

## Profiling and Instrumentation
- Profile on target hardware early and continuously; collect captures for GPU, CPU, and memory during both solo play and 16-player stress scenes.
- Record frame time budgets separately for simulation (tick) and rendering, and log spikes with markers (e.g., weapon fire, VFX bursts, teleport events).
- Track perf regressions via automated captures on repeatable scenes (e.g., “16-player plaza chaos”), saving baseline CSVs for frame time, bandwidth, and CPU utilization.

## Frame Timing: Tick vs. Frame
- Decouple game tick from render frame when possible; clamp simulation rate (e.g., 60–120 Hz) and interpolate/extrapolate for display refresh variability.
- Tune tick rate to stay within CPU budget under peak load; use instrumentation to flag when the simulation overruns its budget.
- Enable frame pacing to smooth frame delivery; verify even frame spacing under VSync on/off and during large VFX bursts.
- Add a user-facing VSync toggle (with fallback to driver-controlled adaptive vsync) and persist the setting; default to VSync on for stability, but expose an unlocked option for latency-sensitive users.

## Rendering Optimizations
- Level of Detail (LOD): ensure meshes have at least 2–3 LODs; use screen-size thresholds validated on target displays. Audit hero assets visible in the 16-player chaos scene first.
- Lighting: bake static and stationary lighting where possible; minimize dynamic shadow casters. Use lightmaps/light probes for crowds and set conservative shadow draw distances.
- GPU instancing: instance repeatable props (cover objects, debris, foliage) and ensure material compatibility (no per-instance material variants where avoidable).
- VFX pooling: pool particle systems and decals; avoid per-spawn allocations. Pre-warm expensive effects used in chaotic encounters (e.g., explosions, ultimates).

## Networking and Bandwidth
- Monitor bandwidth and CPU usage during 16-player chaos scenes; log per-client and server CPU plus bandwidth (avg/peak).
- Tune net update rates per actor class (players > projectiles > ambient) and cap packet sizes to stay within MTU. Bundle small updates and avoid redundant component replication.
- Apply relevancy culling and priority-based throttling; lower update frequency for distant/occluded actors and cosmetic-only effects.
- Validate packet serialization costs on CPU; cache frequently sent payloads where safe and avoid per-frame heap allocations in replication paths.

## Checklist for Implementation
- [ ] Add automated perf capture on target hardware for the 16-player chaos scenario.
- [ ] Implement frame pacing verification and expose a VSync toggle with persisted user settings.
- [ ] Audit tick vs. frame timings; decouple and clamp simulation rate as needed.
- [ ] LOD audit and fixes for hero assets; enforce baked lighting on static geometry.
- [ ] Enable GPU instancing for repeatable props; ensure material compatibility.
- [ ] Introduce pooled VFX and pre-warm heavy effects.
- [ ] Instrument and tune network update rates, packet sizes, and relevancy rules during 16-player chaos tests.
Shiz-and-giggles is a fast-paced, Quake-inspired arena shooter. This guide covers how to host and join matches, the default controls, and best practices for configuring servers and contributing new content while preserving the game's classic feel.

## Quickstart

### Hosting a match
1. Launch a dedicated server:
   ```bash
   ./shiz-server +map q1dm1 +fraglimit 30 +timelimit 10 +sv_public 1
   ```
2. Open the necessary UDP port on your firewall (default: `27960`).
3. Share your IP/hostname and port with players.
4. Keep an eye on server logs for players joining and any configuration warnings.

### Joining a match
- From the main menu, choose **Find Server** and select a listed server.
- Or, connect directly via console:
  ```bash
  connect your.host.name:27960
  ```

### Default keybinds
| Action            | Key  |
| ----------------- | ---- |
| Move forward/back | W / S|
| Strafe left/right | A / D|
| Jump              | Space|
| Crouch            | Ctrl |
| Sprint            | Shift|
| Fire              | Mouse1 |
| Alternate fire    | Mouse2 |
| Use/Interact      | E |
| Weapon next/prev  | Mouse wheel |
| Scoreboard        | Tab |
| Console           | ` (backtick) |

## Server tuning guide

### Frag and time limits
- **Frag limit**: Set higher values (30–50) for duel/FFA maps with strong verticality; lower values (15–25) keep smaller maps brisk.
- **Time limit**: 10 minutes suits duels; 15–20 minutes helps FFA or team modes breathe. Consider enabling sudden death on ties.

### Item timers
- **Weapons**: 5–15 seconds depending on power. Keep staple weapons (SG/NG/GL/RL) on short timers; power weapons (LG/RG/BFG) longer.
- **Armor/Mega**: Common armor at 25 seconds, Mega Health at 35 seconds preserves route planning without over-stacking.
- **Power-ups**: Quad/Haste/Regeneration at 90–120 seconds to make them events rather than constants.
- **Ammo/Health shards**: 15–25 seconds to reward positional control without overfeeding.

### Map rotation
Create a rotation file (example: `config/maprotation.cfg`):
```cfg
set g_mapRotation "q1dm1 q1dm3 q3dm6 pro-q3tourney4"
set g_mapRotationMode "loop"   // loop, random, or vote
set g_intermissionTime 10
```
- Avoid repeating similar layouts back-to-back (e.g., two tight vertical arenas).
- Include at least one beginner-friendly map early to keep new players engaged.
- Refresh the rotation periodically to prevent meta stagnation.

### Additional recommendations
- Enable **warmup** so players can load in and test aim before live play.
- Keep **maxpackets** and **rate** defaults conservative for modem-like connections; allow opt-in higher rates for LAN/modern broadband.
- Publish a short **server rules** MOTD so players know what to expect.

## Contributing new maps and weapons (keeping it Quake-like)

### Maps
- **Scale and movement**: Design for strafe-jumping speed—avoid hallways narrower than double-strafe width and keep ceilings high enough for rocket jumps.
- **Flow**: Aim for 2–3 primary routes per room; include loops that reward control without dead-ends.
- **Item placement**: Separate strong weapons from top-tier armor/mega to prevent single-point domination. Use health/armor breadcrumbs to guide flow.
- **Verticality**: Provide meaningful vertical fights (ledges, jump pads) but ensure escape routes to prevent excessive camping.
- **Visuals**: Stick to readable, high-contrast lighting; avoid excessive particle clutter that obscures player silhouettes.
- **Technical**: Seal leaks, optimize vis/occlusion, add player clips to smooth movement, and confirm bot navigation meshes are baked.

### Weapons
- **Roles over redundancy**: Each weapon should fill a clear niche (e.g., hitscan poke, splash denial, close burst) without duplicating existing strengths.
- **Movement interaction**: Preserve momentum-friendly combat—avoid heavy slows, ironsights, or long ADS; keep recoil minimal and predictable.
- **Resource economy**: Tune ammo so power weapons require deliberate control; avoid infinite-ammo power weapons.
- **TTK expectations**: Duels should reward accuracy and positioning; avoid instant-win mechanics outside timed power-ups.
- **Counterplay**: Introduce weaknesses (range falloff, projectile speed, reload rhythm) so no single weapon dominates all ranges.

### Testing and submission
- Playtest with mixed skill groups; gather feedback on flow, item timing, and spawn safety.
- Validate bot behavior and performance (FPS stability, netcode smoothness).
- Update documentation/configs: add map names to rotations and weapon definitions to loadouts before submitting a PR.
- Follow repository conventions for asset naming and include source files (map sources, textures, scripts) where licensing permits.
