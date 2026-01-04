from __future__ import annotations

import argparse
import pathlib
import sys
import shutil
import textwrap

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_artifacts


DIST = ROOT / "dist"
PORTABLE_ROOT = ROOT / "portable"
VERSION_FILE = ROOT / "VERSION"


def build_binaries(skip_build: bool, skip_godot: bool, godot_bin: str | None) -> None:
    if skip_build:
        return
    print("Building binaries (one-file PyInstaller + Godot exports)...")
    build_artifacts.build(skip_godot=skip_godot, godot_bin=godot_bin, onefile=True)


def expected_artifacts(include_godot: bool) -> list[pathlib.Path]:
    required = [DIST / "shiz-client", DIST / "shiz-server"]
    if include_godot:
        required.extend(
            [
                DIST / "godot" / "client" / "ShizAndGiggles.x86_64",
                DIST / "godot" / "server" / "ShizAndGigglesServer.x86_64",
            ]
        )
    return required


def verify_artifacts(include_godot: bool) -> None:
    missing = [path for path in expected_artifacts(include_godot) if not path.exists()]
    if missing:
        joined = "\n - " + "\n - ".join(str(path) for path in missing)
        raise FileNotFoundError(f"Missing artifacts. Build first or disable Godot exports:\n{joined}")


def derive_version() -> str:
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text().strip()
    return "dev"


def write_portable_readme(bundle_dir: pathlib.Path, version: str, include_tools: bool) -> None:
    instructions = textwrap.dedent(
        f"""
        Shiz-and-Giggles portable build
        Version: {version}

        This bundle is ready to drop into a Discord post—no Python or extra tooling needed by players.

        How to run (Linux):
        1) Extract the zip.
        2) Double-click client/ShizAndGiggles.x86_64 or run `chmod +x client/ShizAndGiggles.x86_64` then `./client/ShizAndGiggles.x86_64` from a terminal.
        3) To host a match locally, run `chmod +x server/ShizAndGigglesServer.x86_64` and then `./server/ShizAndGigglesServer.x86_64`.
        {"4) CLI helpers: ./tools/shiz-server to start the Python dedicated server and ./tools/shiz-client to connect from a terminal." if include_tools else ""}

        Notes:
        - Everything in this bundle is self contained. Players do not need Python, Godot, or Git installed.
        - If you regenerate this bundle on another machine, keep the folder structure so the shortcuts above stay valid.
        """
    ).strip()
    (bundle_dir / "README-PORTABLE.txt").write_text(instructions)


def copy_artifact(src: pathlib.Path, dest: pathlib.Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def build_portable_bundle(name: str, include_godot: bool, include_tools: bool) -> pathlib.Path:
    version = derive_version()
    bundle_dir = PORTABLE_ROOT / f"{name}-{version}"
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True)

    if include_godot:
        copy_artifact(DIST / "godot" / "client" / "ShizAndGiggles.x86_64", bundle_dir / "client" / "ShizAndGiggles.x86_64")
        copy_artifact(DIST / "godot" / "server" / "ShizAndGigglesServer.x86_64", bundle_dir / "server" / "ShizAndGigglesServer.x86_64")

    if include_tools:
        copy_artifact(DIST / "shiz-client", bundle_dir / "tools" / "shiz-client")
        copy_artifact(DIST / "shiz-server", bundle_dir / "tools" / "shiz-server")

    write_portable_readme(bundle_dir, version, include_tools)
    zip_path = bundle_dir.with_suffix(".zip")
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(str(bundle_dir), "zip", root_dir=bundle_dir)
    return zip_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Discord-ready portable zip containing self-contained binaries")
    parser.add_argument("--name", default="shiz-and-giggles-portable", help="Folder/zip name prefix for the portable bundle")
    parser.add_argument("--skip-build", action="store_true", help="Skip rebuilding artifacts and reuse whatever is already in dist/")
    parser.add_argument("--skip-godot", action="store_true", help="Allow building a portable zip without the Godot client/server exports")
    parser.add_argument("--godot-bin", help="Optional path to a Godot executable when rebuilding exports")
    parser.add_argument("--omit-tools", action="store_true", help="Skip bundling the PyInstaller shiz-server/shiz-client helpers to keep the zip smaller")
    args = parser.parse_args()

    include_godot = not args.skip_godot
    include_tools = not args.omit_tools

    build_binaries(skip_build=args.skip_build, skip_godot=args.skip_godot, godot_bin=args.godot_bin)
    verify_artifacts(include_godot=include_godot)
    zip_path = build_portable_bundle(args.name, include_godot=include_godot, include_tools=include_tools)
    print(f"Portable bundle ready: {zip_path}")


if __name__ == "__main__":
    main()
