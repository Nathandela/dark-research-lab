"""Hatch build hook to bundle the pre-built Go binary into the wheel."""
import platform
import shutil
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

ARCH_MAP = {
    "x86_64": "amd64",
    "amd64": "amd64",
    "aarch64": "arm64",
    "arm64": "arm64",
}


class CustomBuildHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version, build_data):
        system = platform.system().lower()
        machine = platform.machine().lower()
        arch = ARCH_MAP.get(machine, machine)

        ext = ".exe" if system == "windows" else ""
        binary_name = f"drl-{system}-{arch}{ext}"

        dist_dir = Path(self.root) / "go" / "dist"
        src = dist_dir / binary_name

        if not src.exists():
            raise FileNotFoundError(
                f"Go binary not found: {src}\n"
                f"Run 'scripts/build.sh' before building the wheel."
            )

        dest = Path(self.root) / "python" / "drl" / f"drl{ext}"
        shutil.copy2(src, dest)
        dest.chmod(0o755)

        build_data["force_include"][str(dest)] = f"drl/drl{ext}"
