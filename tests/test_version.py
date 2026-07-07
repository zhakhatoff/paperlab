"""Tests for __version__ synchronisation with pyproject.toml."""

import tomllib
from pathlib import Path

from paperlab import __version__


def test_version_is_string() -> None:
    assert isinstance(__version__, str)


def test_version_starts_with_digit_or_unknown() -> None:
    assert __version__[0].isdigit() or __version__ == "0.0.0+unknown"


def test_version_matches_pyproject() -> None:
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    with pyproject.open("rb") as fh:
        data = tomllib.load(fh)
    declared = data["project"]["version"]
    # Allow the fallback when the package is not installed in the environment.
    assert __version__ in (declared, "0.0.0+unknown")
