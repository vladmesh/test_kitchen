from __future__ import annotations

from importlib import import_module
from pathlib import Path

__all__ = ["load_model_modules"]


def load_model_modules() -> None:
    """Import every `<module>.models` module so SQLAlchemy metadata stays in sync."""

    package_dir = Path(__file__).resolve().parent

    for child in package_dir.iterdir():
        if not child.is_dir() or child.name.startswith("__"):
            continue

        module_name = f"{__name__}.{child.name}.models"
        try:
            import_module(module_name)
        except ModuleNotFoundError:
            continue
