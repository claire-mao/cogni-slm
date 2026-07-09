"""Backward-compatible CLI wrapper for module src.data.ingest_raw_essays."""

from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path
from typing import Any

_MODULE_PATH = "src.data.ingest_raw_essays"

try:
    _IMPL = import_module(_MODULE_PATH)
except ModuleNotFoundError:
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    _IMPL = import_module(_MODULE_PATH)


def _sync_overrides() -> None:
    reserved = {
        "sys",
        "import_module",
        "Path",
        "Any",
        "_MODULE_PATH",
        "_IMPL",
        "_sync_overrides",
        "main",
        "__getattr__",
        "__dir__",
    }
    for name, value in list(globals().items()):
        if name.startswith("__") or name in reserved:
            continue
        setattr(_IMPL, name, value)


def main() -> Any:
    _sync_overrides()
    return _IMPL.main()


def __getattr__(name: str) -> Any:
    return getattr(_IMPL, name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(dir(_IMPL)))


if __name__ == "__main__":
    main()
