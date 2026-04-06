"""Hatch build hook to bundle pre-built Go binaries into the wheel."""
import os
import shutil
import sys
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

PLATFORMS = [
    ("darwin", "amd64", ""),
    ("darwin", "arm64", ""),
    ("linux", "amd64", ""),
    ("linux", "arm64", ""),
    ("windows", "amd64", ".exe"),
    ("windows", "arm64", ".exe"),
]


class CustomBuildHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version, build_data):
        dist_dir = Path(self.root) / "go" / "dist"
        bin_dir = Path(self.root) / "python" / "drl" / "bin"
        bin_dir.mkdir(exist_ok=True)

        found = 0
        missing = []
        for system, arch, ext in PLATFORMS:
            binary_name = f"drl-{system}-{arch}{ext}"
            src = dist_dir / binary_name
            if not src.exists():
                missing.append(binary_name)
                continue
            dest = bin_dir / binary_name
            shutil.copy2(src, dest)
            if os.name != "nt":
                dest.chmod(0o755)
            build_data["force_include"][str(dest)] = f"drl/bin/{binary_name}"
            found += 1

        if found == 0:
            raise FileNotFoundError(
                f"No Go binaries found in {dist_dir}\n"
                f"Run 'scripts/build.sh' before building the wheel."
            )

        if missing:
            print(
                f"drl: warning: {len(missing)} platform binaries missing: {', '.join(missing)}",
                file=sys.stderr,
            )
