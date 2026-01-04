from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"


PYINSTALLER_BASE = [
    sys.executable,
    "-m",
    "PyInstaller",
    "--clean",
    "--noconfirm",
    "--log-level=INFO",
    "--debug=all",
]


def build() -> None:
    DIST.mkdir(exist_ok=True)
    server_spec = [
        *PYINSTALLER_BASE,
        "--name",
        "shiz-server",
        str(ROOT / "shizgiggles" / "server.py"),
    ]
    client_spec = [
        *PYINSTALLER_BASE,
        "--name",
        "shiz-client",
        str(ROOT / "shizgiggles" / "client.py"),
    ]
    subprocess.check_call(server_spec)
    subprocess.check_call(client_spec)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build client and dedicated server binaries with debug symbols")
    parser.parse_args()
    build()


if __name__ == "__main__":
    main()
