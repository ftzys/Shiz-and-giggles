# Shiz and Giggles Build + Test Harness

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
