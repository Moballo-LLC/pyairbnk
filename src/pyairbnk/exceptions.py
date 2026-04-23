"""Exception types for pyairbnk."""

from __future__ import annotations


class AirbnkError(Exception):
    """Base exception for pyairbnk."""


class AirbnkProtocolError(AirbnkError, ValueError):
    """Raised when Airbnk data cannot be parsed or validated."""


class AirbnkCloudError(AirbnkError):
    """Raised when the Airbnk cloud flow cannot proceed."""


class AirbnkBleError(AirbnkError):
    """Raised when a BLE command or probe cannot be completed."""

