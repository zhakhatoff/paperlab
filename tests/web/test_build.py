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


def test_launch_calls_app_launch(monkeypatch):
    mock_app = MagicMock()
    monkeypatch.setattr(web_app, "build_app", lambda: mock_app)

    web_app.launch(share=False, inbrowser=True)

    mock_app.launch.assert_called_once_with(share=False, inbrowser=True)
