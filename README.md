# Shiz-and-Giggles

<div align="center">
  <img src="[docs/assets/shiz-and-giggles-logo.svg](https://cdn.discordapp.com/attachments/618971960092786699/1457258036694351872/shiz.png?ex=695b58ce&is=695a074e&hm=163534c577bc028154801f197744bd05e02f4d1eacd4caa6713a49625e8229df&)" alt="Shiz-and-giggles logo" width="520" />
  <p><strong>A cartoony arena shooter</strong> · <em>Built for big laughs and fast rounds</em></p>
</div>

## Overview
Shiz-and-Giggles is a bright, Quake-inspired arena FPS about zooming around and bonking friends with splash damage. It shines with 4–16 players jumping into quick rounds, and this repo holds everything that ships those builds, hosts servers, and packages releases.

## What’s inside
- **HUD and menus that feel like a Saturday morning show,** with clear scoreboards, kill feed, and a lobby browser that does not get in your way.
- **A handful of ready-to-run arenas** plus specs in `docs/arena_specs.md` for anyone who wants to block out new levels.
- **Dedicated server + client tools** (`shizgiggles` package) to smoke test movement, weapons, and up to 16 players worth of chaos.
- **Release scripts** that build nightly zips for itch.io or Steam private betas without extra hassle.

## Key features
- **Movement-first fun:** strafe jumps, rocket jumps, and forgiving air control so everyone gets to feel speedy.
- **Clear feedback:** poppy crosshair pings, obvious hit markers, and a scoreboard that stays legible mid-chaos.
- **Matchmaking that works for friends:** region-aware browsing, ready checks, and easy team colors that still play nice with free-for-all.
- **Runs well under load:** lightmapped scenes, pooled VFX, and network replication tuned for a 16-player pileup.

## Platforms & technology
- **Engine:** Godot for the playable client, HUD, and arena blockouts.
- **Backend/tooling:** Python-powered dedicated server simulation, load testing helpers, and PyInstaller packaging.
- **CI/CD:** GitHub Actions pipeline that churns out nightly builds and regression tests.

## Play with friends (and tinker locally)
1. Clone the repo and spin up a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .[dev]
   ```
2. Launch a dedicated server (default port `8765`) so the crew has a place to hop in:
   ```bash
   shiz-server --port 8765
   ```
3. Connect a client and move around:
   ```bash
   shiz-client --port 8765 --player-id playtester --moves "1,0" "0,1" --fire
   ```
4. Want to see how it behaves with a full lobby? Spawn bots for load testing:
   ```bash
   shiz-load-test --port 8765 --clients 16
   ```

## Nightly builds
We ship builds automatically. The GitHub Actions workflow `.github/workflows/nightly.yml` makes debug-friendly client and server binaries with PyInstaller, runs the tests, and uploads everything (including the changelog and version file) every night.

## Packaging for itch.io / Steam private beta
When you’re ready to share, run `scripts/package_release.py` after `scripts/build_artifacts.py` to bundle the latest build into `releases/<version>-<channel>.zip`. Add `--itch-target` to push with `butler` or `--steam-script` to hand it to `steamcmd`.

## Versioning and changelog
You’ll find the current version in `VERSION` and mirrored in `shizgiggles.__init__.__version__`. Add player-facing notes to `CHANGELOG.md` whenever you ship something new.

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
   The archive lands in `releases/<version>-<channel>.zip` and is ready for itch.io/Steam uploads using the optional flags.

## Discord-ready portable zip (no Python or tools required)
Bundle everything needed to share the game as a single download (usable directly after extracting, no GitHub access or Python installs required):
```bash
python scripts/build_portable_bundle.py --name shiz-and-giggles-discord
```
- The script rebuilds one-file PyInstaller CLIs and Godot exports, then writes a zip in `portable/` with runnable binaries plus a quickstart README.
- Use `--skip-build` if you already have fresh artifacts in `dist/`, `--skip-godot` to ship only the CLIs, or `--omit-tools` to exclude the Python helpers.

## Windows `.exe` releases via GitHub
- Push a tag like `v0.2.0` or trigger the **Windows Release Build** workflow manually.
- The workflow makes one-file PyInstaller executables for `shiz-client` and `shiz-server`, bundles them with the changelog and version metadata, and uploads the zip to a GitHub Release when a tag is present.
- Manual runs without a tag still produce downloadable artifacts; grab them from the workflow run’s artifacts list.

# Performance Tuning Plan

If you like making things buttery smooth, here’s the checklist we use to keep 16-player chaos running well.

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
Shiz-and-giggles is a bright, Quake-inspired arena shooter for 4–16 players. This guide covers how to host and join matches, the default controls, and the basics for contributing new content while keeping the playful feel intact.

## Quickstart

### Hosting a match
1. Launch a dedicated server (swap the map and limits however you like):
   ```bash
   ./shiz-server +map q1dm1 +fraglimit 30 +timelimit 10 +sv_public 1
   ```
2. Open the necessary UDP port on your firewall (default: `27960`).
3. Share your IP/hostname and port with friends. A 4–8 player lobby is great for warmups; it stays wild all the way up to 16.
4. Keep an eye on server logs for players joining and any configuration warnings.

### Joining a match
- From the main menu, choose **Find Server** and pick a lobby.
- Or, enter the server IP/hostname and port directly in the console to hop in.

## Support
For playtest feedback, build issues, or server questions, open an issue on GitHub. Partners can reach the team via the private support channel for escalations.
