"""Project metadata tests."""

from __future__ import annotations

import tomllib
from pathlib import Path

from pyairbnk import MODEL_PROFILE_BY_KEY, MODEL_PROFILES, __version__

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_runtime_version_matches_project_metadata() -> None:
    """The package metadata and runtime version should stay in sync."""

    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
    version = pyproject["project"]["version"]

    assert __version__ == version
    assert f"## {version}" in (PROJECT_ROOT / "CHANGELOG.md").read_text()


def test_only_live_validated_profiles_are_marked_validated() -> None:
    """Only profiles with real hardware validation should be marked validated."""

    live_validated_keys = {"b100", "m532"}

    assert MODEL_PROFILE_BY_KEY["b100"].validated is True
    assert MODEL_PROFILE_BY_KEY["m532"].supports_remote_lock is True
    assert MODEL_PROFILE_BY_KEY["m532"].validated is True

    for profile in MODEL_PROFILES:
        if profile.key not in live_validated_keys:
            assert profile.validated is False
