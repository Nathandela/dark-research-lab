"""Smoke tests for the drl CLI binary.

These tests build and exercise the actual Go binary to verify
end-to-end behavior matches the verification contract.
"""
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
GO_DIR = REPO_ROOT / "go"


@pytest.fixture(scope="session")
def drl_binary():
    """Build the drl binary once for all tests."""
    binary = GO_DIR / "drl"
    subprocess.run(
        ["go", "build", "-o", str(binary), "./cmd/drl/"],
        cwd=str(GO_DIR),
        check=True,
        capture_output=True,
    )
    assert binary.is_file()
    return binary


def run_drl(binary, args, cwd=None, env=None):
    """Helper to run drl with args and return result."""
    result = subprocess.run(
        [str(binary)] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    return result


def make_temp_repo(tmpdir, existing=False):
    """Init a git repo in tmpdir. If existing, pre-create .claude/."""
    subprocess.run(
        ["git", "init"], cwd=tmpdir, capture_output=True, check=True
    )
    if existing:
        claude_dir = Path(tmpdir) / ".claude"
        claude_dir.mkdir()
        (claude_dir / "CLAUDE.md").write_text("# Existing\n")


class TestVersion:
    """AC-1: drl --version/version prints version string."""

    def test_version_command(self, drl_binary):
        result = run_drl(drl_binary, ["version"])
        assert result.returncode == 0
        assert len(result.stdout.strip()) > 0

    def test_binary_name(self, drl_binary):
        """AC-2: Binary is named 'drl'."""
        assert drl_binary.name == "drl"


class TestHelp:
    """Verify help output shows drl, not ca."""

    def test_help_shows_drl(self, drl_binary):
        result = run_drl(drl_binary, ["--help"])
        assert result.returncode == 0
        assert "drl" in result.stdout
        assert "ca " not in result.stdout

    def test_help_shows_setup_command(self, drl_binary):
        result = run_drl(drl_binary, ["--help"])
        assert "setup" in result.stdout

    def test_setup_help_shows_tier_flags(self, drl_binary):
        result = run_drl(drl_binary, ["setup", "--help"])
        assert result.returncode == 0
        assert "--core-skill" in result.stdout
        assert "--all-skill" in result.stdout


class TestSetupEmptyRepo:
    """AC-4: drl setup in empty dir creates all tier files."""

    def test_creates_claude_dir(self, drl_binary):
        with tempfile.TemporaryDirectory() as tmpdir:
            make_temp_repo(tmpdir)
            result = run_drl(
                drl_binary,
                ["setup", "--skip-hooks", "--repo-root", tmpdir],
            )
            assert result.returncode == 0
            assert (Path(tmpdir) / ".claude").is_dir()

    def test_creates_skills(self, drl_binary):
        with tempfile.TemporaryDirectory() as tmpdir:
            make_temp_repo(tmpdir)
            run_drl(
                drl_binary,
                ["setup", "--skip-hooks", "--repo-root", tmpdir],
            )
            skills_dir = Path(tmpdir) / ".claude" / "skills" / "drl"
            assert skills_dir.is_dir()
            skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
            assert len(skill_dirs) > 0

    def test_creates_agents(self, drl_binary):
        with tempfile.TemporaryDirectory() as tmpdir:
            make_temp_repo(tmpdir)
            run_drl(
                drl_binary,
                ["setup", "--skip-hooks", "--repo-root", tmpdir],
            )
            agents_dir = Path(tmpdir) / ".claude" / "agents" / "drl"
            assert agents_dir.is_dir()
            agent_files = list(agents_dir.glob("*.md"))
            assert len(agent_files) > 0


class TestSetupExistingRepo:
    """AC-5: drl setup in existing repo installs infrastructure only."""

    def test_skips_skills_in_existing_repo(self, drl_binary):
        with tempfile.TemporaryDirectory() as tmpdir:
            make_temp_repo(tmpdir, existing=True)
            result = run_drl(
                drl_binary,
                ["setup", "--skip-hooks", "--repo-root", tmpdir],
            )
            assert result.returncode == 0

            # Skills dir may exist but should contain no skill subdirectories
            skills_dir = Path(tmpdir) / ".claude" / "skills" / "drl"
            if skills_dir.exists():
                skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
                assert len(skill_dirs) == 0, (
                    "Skills should not be installed in existing repo"
                )


class TestSetupCoreSkill:
    """AC-6: --core-skill installs infrastructure + core, skips role skills."""

    def test_core_skill_installs_skills(self, drl_binary):
        with tempfile.TemporaryDirectory() as tmpdir:
            make_temp_repo(tmpdir, existing=True)
            result = run_drl(
                drl_binary,
                ["setup", "--skip-hooks", "--core-skill", "--repo-root", tmpdir],
            )
            assert result.returncode == 0

            skills_dir = Path(tmpdir) / ".claude" / "skills" / "drl"
            assert skills_dir.is_dir()
            skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
            assert len(skill_dirs) > 0

    def test_core_skill_skips_role_skills(self, drl_binary):
        with tempfile.TemporaryDirectory() as tmpdir:
            make_temp_repo(tmpdir, existing=True)
            result = run_drl(
                drl_binary,
                ["setup", "--skip-hooks", "--core-skill", "--repo-root", tmpdir],
            )
            assert result.returncode == 0

            # Role skills live under .claude/skills/drl/agents/
            role_skills = (
                Path(tmpdir) / ".claude" / "skills" / "drl" / "agents"
            )
            assert not role_skills.exists(), (
                "Role skills (agents/) should not be installed with --core-skill"
            )


class TestSetupAllSkill:
    """AC-7: --all-skill installs all tiers."""

    def test_all_skill_installs_everything(self, drl_binary):
        with tempfile.TemporaryDirectory() as tmpdir:
            make_temp_repo(tmpdir, existing=True)
            result = run_drl(
                drl_binary,
                ["setup", "--skip-hooks", "--all-skill", "--repo-root", tmpdir],
            )
            assert result.returncode == 0

            skills_dir = Path(tmpdir) / ".claude" / "skills" / "drl"
            assert skills_dir.is_dir()
            agents_dir = Path(tmpdir) / ".claude" / "agents" / "drl"
            assert agents_dir.is_dir()

    def test_all_skill_includes_role_skills(self, drl_binary):
        with tempfile.TemporaryDirectory() as tmpdir:
            make_temp_repo(tmpdir, existing=True)
            run_drl(
                drl_binary,
                ["setup", "--skip-hooks", "--all-skill", "--repo-root", tmpdir],
            )

            role_skills = (
                Path(tmpdir) / ".claude" / "skills" / "drl" / "agents"
            )
            assert role_skills.is_dir(), (
                "--all-skill should install role skills under agents/"
            )
            role_files = list(role_skills.iterdir())
            assert len(role_files) > 0


class TestCrossCompile:
    """AC-10: Build script produces binaries for target platforms."""

    def test_build_script_exists(self):
        build_script = REPO_ROOT / "scripts" / "build.sh"
        assert build_script.is_file()
        assert os.access(build_script, os.X_OK)

    def test_native_build_works(self, drl_binary):
        """Verify at least the native platform binary works."""
        result = run_drl(drl_binary, ["version"])
        assert result.returncode == 0


class TestPythonWrapper:
    """AC-8, AC-9: Python wrapper locates and executes Go binary."""

    def test_pyproject_has_entry_point(self):
        pyproject = REPO_ROOT / "pyproject.toml"
        content = pyproject.read_text()
        assert "[project.scripts]" in content
        assert 'drl = "drl:main"' in content

    def test_wrapper_finds_dev_binary(self, drl_binary):
        """Wrapper finds go/drl when DRL_BINARY_PATH is set."""
        import sys

        sys.path.insert(0, str(REPO_ROOT / "python"))
        try:
            from drl import _find_binary

            os.environ["DRL_BINARY_PATH"] = str(drl_binary)
            try:
                found = _find_binary()
                assert found is not None
                assert found.is_file()
            finally:
                del os.environ["DRL_BINARY_PATH"]
        finally:
            sys.path.pop(0)
