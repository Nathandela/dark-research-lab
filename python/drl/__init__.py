"""DRL - Dark Research Lab CLI wrapper.

Locates and executes the Go binary bundled in the wheel.
"""
import os
import platform
import subprocess
import sys
from pathlib import Path

ARCH_MAP = {
    "x86_64": "amd64",
    "amd64": "amd64",
    "aarch64": "arm64",
    "arm64": "arm64",
}

SUPPORTED_SYSTEMS = {"darwin", "linux", "windows"}


def _platform_binary_name() -> str | None:
    system = platform.system().lower()
    machine = platform.machine().lower()
    arch = ARCH_MAP.get(machine)
    if system not in SUPPORTED_SYSTEMS or arch is None:
        return None
    ext = ".exe" if system == "windows" else ""
    return f"drl-{system}-{arch}{ext}"


def _find_binary() -> Path | None:
    """Locate the drl Go binary.

    Resolution order:
    1. DRL_BINARY_PATH env override
    2. Platform-matched binary in bin/ subdirectory (wheel-installed)
    3. Local dev build at go/dist/
    """
    # 1. Env override
    env_path = os.environ.get("DRL_BINARY_PATH")
    if env_path:
        p = Path(env_path)
        if p.is_file():
            return p
        print(f"drl: warning: DRL_BINARY_PATH={env_path} is not a valid file, trying fallbacks", file=sys.stderr)

    binary_name = _platform_binary_name()
    if binary_name is None:
        return None

    # 2. Bundled binary (multi-platform wheel)
    pkg_dir = Path(__file__).parent
    bundled = pkg_dir / "bin" / binary_name
    if bundled.is_file():
        return bundled

    # 3. Dev build (assumes repo layout: python/drl/ -> repo_root)
    repo_root = pkg_dir.parent.parent
    dev_build = repo_root / "go" / "dist" / binary_name
    if dev_build.is_file():
        return dev_build

    return None


def main():
    """Entry point for the drl command."""
    binary = _find_binary()
    if binary is None:
        system = platform.system()
        machine = platform.machine()
        name = _platform_binary_name()
        if name is None:
            print(f"drl: unsupported platform: {system}/{machine}", file=sys.stderr)
        elif (Path(__file__).parent / "bin").is_dir():
            print(f"drl: binary not found in wheel for {system}/{machine}", file=sys.stderr)
            print(f"  Expected: {name}", file=sys.stderr)
            print("  Set DRL_BINARY_PATH to override", file=sys.stderr)
        else:
            print("drl: Go binary not found.", file=sys.stderr)
            print("  Run: cd go && make build", file=sys.stderr)
        sys.exit(1)

    try:
        result = subprocess.run(
            [str(binary)] + sys.argv[1:],
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        sys.exit(result.returncode)
    except OSError as e:
        print(f"drl: failed to execute binary: {e}", file=sys.stderr)
        print(f"  Binary: {binary}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
