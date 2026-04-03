"""DRL - Dark Research Lab CLI wrapper.

Locates and executes the Go binary bundled in the wheel.
"""
import os
import platform
import subprocess
import sys
from pathlib import Path


def _find_binary() -> Path | None:
    """Locate the drl Go binary.

    Resolution order:
    1. DRL_BINARY_PATH env override
    2. Binary in this package's directory (wheel-installed)
    3. Local dev build at go/dist/drl
    """
    # 1. Env override
    env_path = os.environ.get("DRL_BINARY_PATH")
    if env_path:
        p = Path(env_path)
        if p.is_file():
            return p
        print(f"drl: warning: DRL_BINARY_PATH={env_path} is not a valid file, trying fallbacks", file=sys.stderr)

    # 2. Bundled binary (platform-specific wheel)
    ext = ".exe" if platform.system() == "Windows" else ""
    pkg_dir = Path(__file__).parent
    bundled = pkg_dir / f"drl{ext}"
    if bundled.is_file():
        return bundled

    # 3. Dev build
    repo_root = Path(__file__).parent.parent.parent
    dev_build = repo_root / "go" / "dist" / f"drl{ext}"
    if dev_build.is_file():
        return dev_build

    # 4. Check if drl is on PATH (go build ./cmd/drl output)
    dev_local = repo_root / "go" / f"drl{ext}"
    if dev_local.is_file():
        return dev_local

    return None


def main():
    """Entry point for the drl command."""
    binary = _find_binary()
    if binary is None:
        print("drl: Go binary not found.", file=sys.stderr)
        print("  Set DRL_BINARY_PATH or run: cd go && make build", file=sys.stderr)
        sys.exit(1)

    result = subprocess.run(
        [str(binary)] + sys.argv[1:],
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    sys.exit(result.returncode)
