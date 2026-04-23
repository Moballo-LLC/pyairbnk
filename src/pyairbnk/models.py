"""Shared dataclasses for pyairbnk."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BatteryBreakpoint:
    """One battery interpolation point."""

    voltage: float
    percent: float


@dataclass(frozen=True, slots=True)
class ModelProfile:
    """Describe one supported Airbnk lock family."""

    key: str
    models: tuple[str, ...]
    default_battery_profile: tuple[BatteryBreakpoint, ...]
    supports_remote_lock: bool = False
    validated: bool = False


@dataclass(frozen=True, slots=True)
class BootstrapData:
    """Derived Airbnk bootstrap data used at runtime."""

    lock_sn: str
    lock_model: str
    profile: str
    manufacturer_key: bytes
    binding_key: bytes


@dataclass(frozen=True, slots=True)
class AdvertisementData:
    """Decoded Airbnk advertisement payload."""

    serial_number: str
    board_model: int
    firmware_version: str
    voltage: float
    lock_events: int
    lock_state: int
    raw_state_bits: int
    raw_state_label: str
    opens_clockwise: bool
    is_low_battery: bool
    state_flags: int
    battery_flags: int


@dataclass(frozen=True, slots=True)
class StatusResponseData:
    """Decoded Airbnk command status payload."""

    lock_events: int
    voltage: float
    lock_state: int
    raw_state_nibble: int
    raw_state_label: str
    state_byte: int
    trailing_byte: int


@dataclass(frozen=True, slots=True)
class AirbnkCloudSession:
    """Authenticated cloud session details."""

    email: str
    user_id: str
    token: str


@dataclass(frozen=True, slots=True)
class AirbnkCloudLock:
    """Lock details returned from the Airbnk cloud."""

    serial_number: str
    device_name: str
    lock_model: str
    hardware_version: str
    app_key: str
    new_sninfo: str


@dataclass(frozen=True, slots=True)
class AirbnkBleOperationResult:
    """Final result from an active BLE lock operation."""

    status: StatusResponseData
    status_payload_hex: str

