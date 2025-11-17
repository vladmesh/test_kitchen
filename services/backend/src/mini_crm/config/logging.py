from __future__ import annotations

import logging
from typing import Any

import structlog

from mini_crm.config.settings import Settings


def configure_logging(settings: Settings, *, force: bool | None = None) -> None:
    """Configure stdlib + structlog logging once per process."""

    if getattr(configure_logging, "_configured", False) and not force:
        return

    processors: list[structlog.types.Processor] = [
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, settings.log_level.upper(), logging.INFO)),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(level=settings.log_level.upper())
    configure_logging._configured = True  # type: ignore[attr-defined]
