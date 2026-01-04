# Shiz-and-Giggles

<div align="center">
  <img src="docs/assets/shiz-and-giggles-logo.svg" alt="Shiz-and-giggles logo" width="520" />
  <p><strong>Official arena shooter release</strong> · <em>Fast, frantic, and unapologetically arcade</em></p>
</div>

## Overview
Shiz-and-Giggles is a stylish, Quake-inspired arena FPS built for high-speed movement, expressive aim duels, and laugh-out-loud chaos. This repository powers the playable build, server tooling, and release packaging used for public playtests and partner drops.

## What’s inside
- **Polished HUD & UI shell** with scoreboards, kill feed, lobby browser, and responsive pause/settings flows.
- **Playable arenas** plus design-ready specs in `docs/arena_specs.md` for immediate blockout and lighting passes.
- **Dedicated server + client harness** (`shizgiggles` package) for smoketesting player movement, weapons, and 16+ client load scenarios.
- **Release automation** for nightly builds, regression tests, and packaged zips targeting itch.io or Steam private betas.

## Key features
- **Movement-first combat:** strafe jumps, rocket jumps, and air control tuned for 60–120 Hz tick rates.
- **Readable combat feedback:** crisp crosshair, hit indicators, kill feed animations, and scoreboard toggles.
- **Competitive-ready servers:** region-aware browser, ready checks, and cosmetic team selection (usable in FFA).
- **Performance-minded builds:** lightmaps and GPU instancing guidance, pooled VFX, and bandwidth-conscious replication.

## Platforms & technology
- **Engine:** Godot (playable client with HUD prototype and arena blockouts).
- **Backend/tooling:** Python-based dedicated server simulation, load testing utilities, and PyInstaller packaging.
- **CI/CD:** GitHub Actions nightly pipeline for builds, tests, and artifact uploads.

## Install & play
1. Clone the repo and create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .[dev]
   ```
2. Launch a dedicated server (default port `8765`):
   ```bash
   shiz-server --port 8765
   ```
3. Connect a client and issue sample moves:
   ```bash
   shiz-client --port 8765 --player-id playtester --moves "1,0" "0,1" --fire
   ```
4. Stress test with synthetic clients:
   ```bash
   shiz-load-test --port 8765 --clients 16
   ```

### Controls (default)
| Action | Key |
| --- | --- |
| Move forward/back | W / S |
| Strafe left/right | A / D |
| Jump | Space |
| Crouch | Ctrl |
| Sprint | Shift |
| Fire / Alt fire | Mouse1 / Mouse2 |
| Use/Interact | E |
| Weapon next/prev | Mouse wheel |
| Scoreboard | Tab |
| Console | ` (backtick) |

## Content & arenas
- Ready-to-build arena layouts, item timing, and lighting notes live in [`docs/arena_specs.md`](docs/arena_specs.md).
- A static HUD + lobby flow prototype is available via [`index.html`](index.html) for UI/UX reviews in a modern browser.

## Build & release pipeline
- **Nightly builds:** `.github/workflows/nightly.yml` compiles debug-friendly client and server binaries, runs regressions, and uploads artifacts (changelog + version file).
- **Packaging for distribution:** run `scripts/build_artifacts.py` followed by `scripts/package_release.py` to bundle `releases/<version>-<channel>.zip`. Use `--itch-target` for `butler` or `--steam-script` for `steamcmd`.
- **Versioning:** the canonical version lives in `VERSION` and mirrors `shizgiggles.__init__.__version__`. Update `CHANGELOG.md` for every user-facing release.

## Performance philosophy
- Frame pacing and tick-rate decoupling tuned for smooth delivery under 16-player chaos.
- Aggressive relevancy culling, priority-based throttling, and MTU-conscious packets for stable online play.
- LOD, baked lighting, instancing, and pooled VFX to keep silhouette readability and FPS high.

## Contributing
- Build maps and weapons that honor arena DNA: clear combat roles, fast traversal, and predictable recoil.
- Submit changes with updated rotations/configs and source assets where licensing allows.
- Validate with the regression suite:
  ```bash
  pytest
  ```

## Support
For playtest feedback, build issues, or server questions, open an issue on GitHub. Partners can reach the team via the private support channel for escalations.
