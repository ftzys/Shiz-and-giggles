from __future__ import annotations

import argparse
import os
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
GODOT_EXPORTS = {
    "client": {
        "preset": "Linux/X11",
        "output": DIST / "godot" / "client" / "ShizAndGiggles.x86_64",
    },
    "server": {
        "preset": "Linux Server",
        "output": DIST / "godot" / "server" / "ShizAndGigglesServer.x86_64",
    },
}


PYINSTALLER_BASE = [
    sys.executable,
    "-m",
    "PyInstaller",
    "--clean",
    "--noconfirm",
]


def pyinstaller_args(onefile: bool) -> list[str]:
    build_dir = ROOT / "build" / "pyinstaller"
    build_dir.mkdir(parents=True, exist_ok=True)
    args = [
        *PYINSTALLER_BASE,
        "--strip",
        "--optimize=2",
        "--log-level=WARN",
        "--distpath",
        str(DIST),
        "--workpath",
        str(build_dir),
        "--specpath",
        str(build_dir),
    ]
    if onefile:
        args.append("--onefile")
    return args


def build_pyinstaller(onefile: bool = True) -> None:
    DIST.mkdir(exist_ok=True)
    base_args = pyinstaller_args(onefile)
    server_spec = [
        *base_args,
        "--name",
        "shiz-server",
        str(ROOT / "shizgiggles" / "server.py"),
    ]
    client_spec = [
        *base_args,
        "--name",
        "shiz-client",
        str(ROOT / "shizgiggles" / "client.py"),
    ]
    subprocess.check_call(server_spec)
    subprocess.check_call(client_spec)


def get_godot_binary(explicit_bin: str | None = None) -> str:
    candidate = explicit_bin or os.environ.get("GODOT_BIN") or "godot"
    located = shutil.which(candidate)
    if not located:
        raise FileNotFoundError(
            f"Godot binary '{candidate}' not found. Set GODOT_BIN or pass --godot-bin to point at your Godot 4 executable."
        )
    return located


def export_godot_builds(godot_bin: str) -> None:
    for name, export in GODOT_EXPORTS.items():
        output_path = export["output"]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            godot_bin,
            "--headless",
            "--path",
            str(ROOT),
            "--export-release",
            export["preset"],
            str(output_path),
        ]
        print(f"Exporting Godot {name} build -> {output_path}")
        subprocess.check_call(cmd)
        output_path.chmod(0o755)


def build(skip_godot: bool = False, godot_bin: str | None = None, onefile: bool = True) -> None:
    DIST.mkdir(exist_ok=True)
    build_pyinstaller(onefile=onefile)
    if skip_godot:
        print("Skipping Godot exports")
        return
    located_bin = get_godot_binary(godot_bin)
    export_godot_builds(located_bin)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build client and dedicated server binaries (PyInstaller + Godot exports)")
    parser.add_argument(
        "--skip-godot",
        action="store_true",
        help="Skip exporting the Godot client/server builds (useful when Godot is unavailable on the host).",
    )
    parser.add_argument(
        "--onefile",
        action="store_true",
        default=True,
        help="Bundle PyInstaller outputs as single-file executables for easier distribution.",
    )
    parser.add_argument(
        "--no-onefile",
        dest="onefile",
        action="store_false",
        help="Keep PyInstaller outputs in their default directory layout (useful for debugging).",
    )
    parser.add_argument("--godot-bin", help="Path to the Godot 4.x executable to use for exports.", default=None)
    args = parser.parse_args()
    build(skip_godot=args.skip_godot, godot_bin=args.godot_bin, onefile=args.onefile)


if __name__ == "__main__":
    main()
