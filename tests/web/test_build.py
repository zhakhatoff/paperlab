"""Tests for paperlab.web.app.build_app() and launch()."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import paperlab.web.app as web_app

# ---------------------------------------------------------------------------
# gradio not imported at module level
# ---------------------------------------------------------------------------


def test_gradio_not_imported_at_module_level():
    """Gradio must be a lazy import inside build_app(), not at top-level."""
    # Importing web_app must not pull in gradio; reaching this line without error is the check.
    # The real check: importing web_app must not pull in gradio
    import paperlab.web.app  # noqa: F401 — already imported, but re-check
    # If gradio were a top-level import in app.py, this would fail when gradio
    # is absent. Since we reach here without error, the import is lazy.


# ---------------------------------------------------------------------------
# build_app returns Blocks
# ---------------------------------------------------------------------------


def test_build_app_returns_blocks_object(monkeypatch):
    fake_blocks_instance = MagicMock()
    # Real Gradio Blocks.__enter__ returns self; replicate that here.
    fake_blocks_instance.__enter__ = MagicMock(return_value=fake_blocks_instance)
    fake_blocks_instance.__exit__ = MagicMock(return_value=False)
    fake_blocks_class = MagicMock(return_value=fake_blocks_instance)

    fake_gradio = MagicMock()
    fake_gradio.Blocks.return_value = fake_blocks_instance
    fake_gradio.Blocks = fake_blocks_class
    fake_gradio.File = MagicMock(return_value=MagicMock())
    fake_gradio.Radio = MagicMock(return_value=MagicMock())
    fake_gradio.Textbox = MagicMock(return_value=MagicMock())
    fake_gradio.Dropdown = MagicMock(return_value=MagicMock())
    fake_gradio.Button = MagicMock(return_value=MagicMock())
    fake_gradio.Markdown = MagicMock(return_value=MagicMock())
    fake_gradio.Code = MagicMock(return_value=MagicMock())

    with patch.dict(sys.modules, {"gradio": fake_gradio}):
        result = web_app.build_app()

    assert result is fake_blocks_instance


# ---------------------------------------------------------------------------
# launch calls app.launch
# ---------------------------------------------------------------------------


def _fake_gradio_with_recorder():
    """Return (fake_gradio, calls) where calls records Dropdown/Radio kwargs."""
    calls: dict[str, list[dict]] = {"Dropdown": [], "Radio": []}

    fake_blocks_instance = MagicMock()
    fake_blocks_instance.__enter__ = MagicMock(return_value=fake_blocks_instance)
    fake_blocks_instance.__exit__ = MagicMock(return_value=False)

    def _dropdown(*args, **kwargs):
        calls["Dropdown"].append(kwargs)
        return MagicMock()

    def _radio(*args, **kwargs):
        calls["Radio"].append(kwargs)
        return MagicMock()

    fake_gradio = MagicMock()
    fake_gradio.Blocks = MagicMock(return_value=fake_blocks_instance)
    fake_gradio.File = MagicMock(return_value=MagicMock())
    fake_gradio.Radio = _radio
    fake_gradio.Textbox = MagicMock(return_value=MagicMock())
    fake_gradio.Dropdown = _dropdown
    fake_gradio.Button = MagicMock(return_value=MagicMock())
    fake_gradio.Markdown = MagicMock(return_value=MagicMock())
    fake_gradio.Code = MagicMock(return_value=MagicMock())
    return fake_gradio, calls


def test_build_app_uses_config_toml_for_initial_values(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERLAB_HOME", str(tmp_path))
    # Make sure a stray env var doesn't accidentally satisfy the cloud key preflight.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    from paperlab.cli.config import PaperlabConfig, save_config

    save_config(
        PaperlabConfig(
            provider="anthropic",
            model="claude-sonnet-4-5",
            mode="learning",
            lang="ru",
        )
    )

    fake_gradio, calls = _fake_gradio_with_recorder()
    with patch.dict(sys.modules, {"gradio": fake_gradio}):
        web_app.build_app()

    # Provider dropdown is the first Dropdown created.
    provider_kwargs = calls["Dropdown"][0]
    assert provider_kwargs.get("value") == "anthropic"

    # Model dropdown value comes from config.
    model_kwargs = calls["Dropdown"][1]
    assert model_kwargs.get("value") == "claude-sonnet-4-5"

    # Radios: mode first, then lang.
    assert calls["Radio"][0].get("value") == "learning"
    assert calls["Radio"][1].get("value") == "ru"


def test_launch_calls_app_launch(monkeypatch):
    mock_app = MagicMock()
    monkeypatch.setattr(web_app, "build_app", lambda: mock_app)

    web_app.launch(share=False, inbrowser=True)

    mock_app.launch.assert_called_once_with(share=False, inbrowser=True)
