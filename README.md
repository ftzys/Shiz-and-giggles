# NetReady Godot Starter

Starter project using **Godot 4** with **Godot Multiplayer (ENet)** to support client and dedicated server builds. The repository is set up with export presets and CI to build both targets headlessly.

## Engine choice
- **Godot 4** is lightweight, fast to iterate on, and works well in bandwidth-constrained environments.
- Built-in ENet-based multiplayer keeps dependencies minimal and stable.

## Project layout
- `project.godot`: Project configuration targeting Godot 4.2.
- `scenes/main.tscn`: Entry scene bound to the network manager.
- `scripts/network_manager.gd`: Minimal server/client bootstrap with a broadcastable ping RPC.
- `export_presets.cfg`: Exports for Linux desktop client and Linux dedicated server (headless feature flag).
- `.github/workflows/ci.yml`: CI pipeline exporting both targets and publishing artifacts.

## Running locally
- Client (editor or desktop build):
  ```bash
  godot4 --path .
  ```
- Dedicated server (headless build or with `--headless`):
  ```bash
  godot4 --headless --path .
  ```
  The server listens on port `8910` by default.
- Connect a client instance by running the scene and executing in the Godot console:
  ```gdscript
  get_tree().root.get_node("/root/Main").connect_to_server("127.0.0.1")
  ```

## Continuous Integration
GitHub Actions exports Linux client and dedicated server builds on each push/PR. Artifacts are uploaded for download.
