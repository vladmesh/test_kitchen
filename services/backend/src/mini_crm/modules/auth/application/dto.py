from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TokenPairDTO:
    """DTO for token pair."""

    access_token: str
    refresh_token: str
