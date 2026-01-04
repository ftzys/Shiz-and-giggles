from __future__ import annotations

import argparse
import datetime
import os
import pathlib
import shutil
import subprocess
import sys
from typing import List

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
RELEASES = ROOT / "releases"
CHANGELOG = ROOT / "CHANGELOG.md"
VERSION_FILE = ROOT / "VERSION"


class ReleasePackager:
    def __init__(self, channel: str, version: str | None = None) -> None:
        self.channel = channel
        self.version = version or self._derive_version()
        self.release_dir = RELEASES / f"{self.version}-{self.channel}"

    def _derive_version(self) -> str:
        if VERSION_FILE.exists():
            return VERSION_FILE.read_text().strip()
        return datetime.datetime.utcnow().strftime("0.1.%Y%m%d%H%M")

    def validate_artifacts(self) -> None:
        if not DIST.exists():
            raise FileNotFoundError("dist directory missing. Run build_artifacts.py first.")
        expected = [
            DIST / "shiz-server",
            DIST / "shiz-client",
            DIST / "godot" / "client",
            DIST / "godot" / "server",
        ]
        missing = [str(path) for path in expected if not path.exists()]
        if missing:
            raise FileNotFoundError(
                f"Expected built artifacts were not found: {', '.join(missing)}. Run scripts/build_artifacts.py."
            )

    def prepare_release_dir(self) -> None:
        if self.release_dir.exists():
            shutil.rmtree(self.release_dir)
        self.release_dir.mkdir(parents=True, exist_ok=True)
        for artifact in DIST.iterdir():
            dest = self.release_dir / artifact.name
            if artifact.is_dir():
                shutil.copytree(artifact, dest)
            else:
                shutil.copy2(artifact, dest)
        if CHANGELOG.exists():
            shutil.copy2(CHANGELOG, self.release_dir / CHANGELOG.name)
        if VERSION_FILE.exists():
            shutil.copy2(VERSION_FILE, self.release_dir / VERSION_FILE.name)

    def zip_release(self) -> pathlib.Path:
        output = self.release_dir.with_suffix(".zip")
        if output.exists():
            output.unlink()
        shutil.make_archive(str(self.release_dir), "zip", root_dir=self.release_dir)
        return output

    def push_itch(self, itch_target: str, zip_path: pathlib.Path) -> None:
        butler = shutil.which("butler")
        if not butler:
            print("Skipping itch.io push (butler not found)")
            return
        subprocess.check_call([butler, "push", str(zip_path), itch_target, "--userversion", self.version])

    def push_steam(self, steam_script: pathlib.Path) -> None:
        steamcmd = shutil.which("steamcmd")
        if not steamcmd:
            print("Skipping Steam push (steamcmd not found)")
            return
        subprocess.check_call([steamcmd, "+login", os.environ.get("STEAM_USER", "anonymous"), "+run_app_build_http", str(steam_script), "+quit"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Package artifacts for itch/Steam beta distribution")
    parser.add_argument("--channel", default="beta")
    parser.add_argument("--version")
    parser.add_argument("--itch-target", help="butler target e.g. user/game:channel", default=None)
    parser.add_argument("--steam-script", type=pathlib.Path, help="Path to Steam app build script", default=None)
    args = parser.parse_args()

    packager = ReleasePackager(channel=args.channel, version=args.version)
    packager.validate_artifacts()
    packager.prepare_release_dir()
    zip_path = packager.zip_release()
    print(f"Prepared release {packager.release_dir} -> {zip_path}")
    if args.itch_target:
        packager.push_itch(args.itch_target, zip_path)
    if args.steam_script:
        packager.push_steam(args.steam_script)


if __name__ == "__main__":
    main()
