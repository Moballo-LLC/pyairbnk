"""Generic async BLE client for Airbnk locks."""

from __future__ import annotations

import asyncio
from asyncio import timeout as asyncio_timeout
from collections.abc import Callable
from contextlib import suppress
from typing import TYPE_CHECKING, Any

from bleak.exc import BleakError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from .const import AIRBNK_STATUS_CHARACTERISTIC_UUID, AIRBNK_WRITE_CHARACTERISTIC_UUID
from .exceptions import AirbnkBleError, AirbnkProtocolError
from .models import AirbnkBleOperationResult, BootstrapData, StatusResponseData
from .protocol import (
    generate_operation_code,
    parse_status_response,
    split_operation_frames,
)

if TYPE_CHECKING:
    from bleak.backends.device import BLEDevice

READ_STATUS_RETRY_DELAY_SECONDS = 0.1


class AirbnkBleClient:
    """Execute Airbnk BLE commands using a provided BLE device callback."""

    def __init__(
        self,
        ble_device_callback: Callable[[], BLEDevice | None],
        *,
        name: str,
    ) -> None:
        self._ble_device_callback = ble_device_callback
        self._name = name

    async def async_send_operation(
        self,
        *,
        operation: int,
        current_lock_events: int,
        bootstrap: BootstrapData,
        command_timeout: float,
        status_update_callback: Callable[[StatusResponseData, str], None] | None = None,
    ) -> AirbnkBleOperationResult:
        ble_device = self._current_ble_device()
        operation_code = generate_operation_code(
            operation,
            current_lock_events,
            bootstrap,
        )
        frame_one, frame_two = split_operation_frames(operation_code)
        client = await self._async_connect(ble_device)

        try:
            async with asyncio_timeout(command_timeout):
                await client.write_gatt_char(
                    AIRBNK_WRITE_CHARACTERISTIC_UUID,
                    frame_one,
                    response=True,
                )
                await client.write_gatt_char(
                    AIRBNK_WRITE_CHARACTERISTIC_UUID,
                    frame_two,
                    response=True,
                )
                return await self._async_read_status_until_valid(
                    client,
                    command_timeout=command_timeout,
                    status_update_callback=status_update_callback,
                )
        except TimeoutError as err:
            raise AirbnkBleError(
                f"Timed out waiting for an Airbnk response from {self._name}"
            ) from err
        except BleakError as err:
            raise AirbnkBleError(
                f"Bluetooth error while commanding {self._name}: {err}"
            ) from err
        finally:
            if getattr(client, "is_connected", False):
                with suppress(BleakError):
                    await client.disconnect()

    async def async_probe_connectivity(self, *, command_timeout: float) -> None:
        ble_device = self._current_ble_device()
        client = None
        try:
            async with asyncio_timeout(command_timeout):
                client = await self._async_connect(ble_device)
        except TimeoutError as err:
            raise AirbnkBleError(f"Timed out connecting to {self._name}") from err
        except BleakError as err:
            raise AirbnkBleError(
                f"Bluetooth error while probing {self._name}: {err}"
            ) from err
        finally:
            if client is not None and getattr(client, "is_connected", False):
                with suppress(BleakError):
                    await client.disconnect()

    async def _async_connect(self, ble_device: BLEDevice) -> Any:
        return await establish_connection(
            BleakClientWithServiceCache,
            ble_device,
            self._name,
            max_attempts=1,
            ble_device_callback=self._current_ble_device,
        )

    async def _async_read_status_until_valid(
        self,
        client: Any,
        *,
        command_timeout: float,
        status_update_callback: Callable[[StatusResponseData, str], None] | None = None,
    ) -> AirbnkBleOperationResult:
        deadline = asyncio.get_running_loop().time() + command_timeout
        last_payload_hex: str | None = None
        last_error: Exception | None = None

        while asyncio.get_running_loop().time() < deadline:
            payload = bytes(
                await client.read_gatt_char(AIRBNK_STATUS_CHARACTERISTIC_UUID)
            )
            if payload:
                last_payload_hex = payload.hex().upper()
                try:
                    parsed = parse_status_response(payload)
                except AirbnkProtocolError as err:
                    last_error = err
                else:
                    if status_update_callback is not None:
                        status_update_callback(parsed, last_payload_hex)
                    if self._status_response_is_transient(parsed):
                        last_error = AirbnkProtocolError(
                            "Transient Airbnk status response "
                            f"(state={parsed.state_byte:02X}, "
                            f"tail={parsed.trailing_byte:02X})"
                        )
                    else:
                        return AirbnkBleOperationResult(
                            status=parsed,
                            status_payload_hex=last_payload_hex,
                        )
            await asyncio.sleep(READ_STATUS_RETRY_DELAY_SECONDS)

        detail = ""
        if last_payload_hex:
            detail = f" Last payload: {last_payload_hex}."
        if last_error:
            detail += f" Last parse error: {last_error}."
        raise AirbnkBleError(
            f"Timed out waiting for a valid Airbnk status response.{detail}"
        )

    def _current_ble_device(self) -> BLEDevice:
        ble_device = self._ble_device_callback()
        if ble_device is None:
            raise AirbnkBleError(
                f"No connectable Bluetooth device available for {self._name}"
            )
        return ble_device

    @staticmethod
    def _status_response_is_transient(parsed: StatusResponseData) -> bool:
        return parsed.trailing_byte == 0x00
