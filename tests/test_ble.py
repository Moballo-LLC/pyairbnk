"""BLE transport tests for pyairbnk."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from pyairbnk import AirbnkBleClient, AirbnkBleError, decrypt_bootstrap

from .common import build_bootstrap_fixture, build_status_payload


class _FakeBleClient:
    """Minimal BLE client stub for operation tests."""

    def __init__(self, responses: list[bytes]) -> None:
        self._responses = list(responses)
        self.write_gatt_char = AsyncMock()
        self.disconnect = AsyncMock()
        self.is_connected = True

    async def read_gatt_char(self, _uuid):
        return self._responses.pop(0)


async def test_ble_client_writes_frames_and_returns_final_status() -> None:
    """Operation client should keep polling until the final payload arrives."""

    fixture = build_bootstrap_fixture()
    bootstrap = decrypt_bootstrap(
        fixture["lock_sn"],
        fixture["new_sninfo"],
        fixture["app_key"],
    )
    fake_client = _FakeBleClient(
        [
            build_status_payload(trailing_byte=0x00),
            build_status_payload(trailing_byte=0x01),
        ]
    )
    status_updates: list[str] = []

    with patch(
        "pyairbnk.ble.establish_connection",
        AsyncMock(return_value=fake_client),
    ):
        client = AirbnkBleClient(
            lambda: SimpleNamespace(address="AA:BB:CC:DD:EE:FF"),
            name="Front Gate",
        )
        result = await client.async_send_operation(
            operation=1,
            current_lock_events=42,
            bootstrap=bootstrap,
            command_timeout=5,
            status_update_callback=lambda _status, payload_hex: status_updates.append(
                payload_hex
            ),
        )

    assert fake_client.write_gatt_char.await_count == 2
    assert result.status.lock_events == 1
    assert status_updates[-1] == result.status_payload_hex
    fake_client.disconnect.assert_awaited_once()


async def test_ble_client_probe_connects_and_disconnects() -> None:
    """Connectivity probes should only connect and disconnect."""

    fake_client = _FakeBleClient([build_status_payload()])

    with patch(
        "pyairbnk.ble.establish_connection",
        AsyncMock(return_value=fake_client),
    ):
        client = AirbnkBleClient(
            lambda: SimpleNamespace(address="AA:BB:CC:DD:EE:FF"),
            name="Front Gate",
        )
        await client.async_probe_connectivity(command_timeout=5)

    fake_client.disconnect.assert_awaited_once()


async def test_ble_client_raises_when_no_device_is_available() -> None:
    """Missing BLE devices should fail cleanly."""

    client = AirbnkBleClient(lambda: None, name="Front Gate")

    with pytest.raises(AirbnkBleError, match="No connectable Bluetooth device"):
        await client.async_probe_connectivity(command_timeout=5)
