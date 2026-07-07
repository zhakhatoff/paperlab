"""paperlab — multi-agent LLM tool for critically reading biomedical research papers."""

try:
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as _v

    __version__ = _v("paperlab")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"
