"""Async Airbnk cloud helpers."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout

from .const import AIRBNK_CLOUD_URL, AIRBNK_HEADERS, AIRBNK_LANGUAGE, AIRBNK_VERSION
from .exceptions import AirbnkCloudError, AirbnkProtocolError
from .models import AirbnkCloudLock, AirbnkCloudSession
from .protocol import battery_profile_from_voltage_points

AIRBNK_RETRY_ATTEMPTS = 2
AIRBNK_TIMEOUT = ClientTimeout(total=45, connect=20, sock_connect=20, sock_read=30)


class AirbnkCloudClient:
    """Fetch bootstrap data from the Airbnk cloud."""

    def __init__(
        self,
        session: ClientSession,
        *,
        ipv4_session: ClientSession | None = None,
        cloud_url: str = AIRBNK_CLOUD_URL,
        app_version: str = AIRBNK_VERSION,
    ) -> None:
        self._session = session
        self._ipv4_session = ipv4_session
        self._cloud_url = cloud_url.rstrip("/")
        self._app_version = app_version

    async def async_request_verification_code(self, email: str) -> None:
        await self._async_call(
            "POST",
            "/api/lock/sms",
            {
                "loginAcct": email,
                "language": AIRBNK_LANGUAGE,
                "version": self._app_version,
                "mark": "10",
                "userId": "",
            },
            expect_data=False,
        )

    async def async_authenticate(self, email: str, code: str) -> AirbnkCloudSession:
        payload = await self._async_call(
            "GET",
            "/api/lock/loginByAuthcode",
            {
                "loginAcct": email,
                "authCode": code,
                "systemCode": "Android",
                "language": AIRBNK_LANGUAGE,
                "version": self._app_version,
                "deviceID": "123456789012345",
                "mark": "1",
            },
        )

        try:
            data = payload["data"]
            return AirbnkCloudSession(
                email=str(data["email"]),
                user_id=str(data["userId"]),
                token=str(data["token"]),
            )
        except (KeyError, TypeError) as err:
            raise AirbnkCloudError(
                "The Airbnk login response was missing required fields"
            ) from err

    async def async_get_locks(
        self, session: AirbnkCloudSession
    ) -> list[AirbnkCloudLock]:
        payload = await self._async_call(
            "GET",
            "/api/v2/lock/getAllDevicesNew",
            {
                "language": AIRBNK_LANGUAGE,
                "userId": session.user_id,
                "version": self._app_version,
                "token": session.token,
            },
        )

        locks: list[AirbnkCloudLock] = []
        for raw_lock in payload.get("data") or []:
            try:
                lock = AirbnkCloudLock(
                    serial_number=str(raw_lock["sn"]),
                    device_name=str(raw_lock.get("deviceName") or raw_lock["sn"]),
                    lock_model=str(raw_lock["deviceType"]),
                    hardware_version=str(raw_lock.get("hardwareVersion") or ""),
                    app_key=str(raw_lock["appKey"]),
                    new_sninfo=str(raw_lock["newSninfo"]),
                )
            except (KeyError, TypeError):
                continue
            if lock.lock_model.startswith(("W", "F")):
                continue
            locks.append(lock)
        return locks

    async def async_get_battery_profile(
        self,
        session: AirbnkCloudSession,
        *,
        lock_model: str,
        hardware_version: str,
    ) -> list[dict[str, float]] | None:
        payload = await self._async_call(
            "GET",
            "/api/lock/getAllInfo1",
            {
                "language": AIRBNK_LANGUAGE,
                "userId": session.user_id,
                "version": self._app_version,
                "token": session.token,
            },
        )

        voltage_configs = (payload.get("data") or {}).get("voltageCfg") or []
        for raw_profile in voltage_configs:
            if (
                str(raw_profile.get("fdeviceType")) != lock_model
                or str(raw_profile.get("fhardwareVersion")) != hardware_version
            ):
                continue
            try:
                profile = battery_profile_from_voltage_points(
                    [
                        float(raw_profile[f"fvoltage{index}"])
                        for index in range(1, 5)
                        if raw_profile.get(f"fvoltage{index}") is not None
                    ]
                )
            except (AirbnkProtocolError, ValueError, TypeError):
                return None
            return [
                {"voltage": point.voltage, "percent": point.percent}
                for point in profile
            ]

        return None

    async def _async_call(
        self,
        method: str,
        path: str,
        params: dict[str, str],
        *,
        expect_data: bool = True,
    ) -> dict[str, Any]:
        payload = await self._async_request(method, path, params)

        if payload.get("code") != 200:
            raise AirbnkCloudError(
                str(
                    payload.get("info")
                    or payload.get("msg")
                    or payload.get("message")
                    or "Airbnk cloud rejected the request"
                )
            )
        if expect_data and "data" not in payload:
            raise AirbnkCloudError("Airbnk cloud response did not include any data")
        return payload

    async def _async_request(
        self,
        method: str,
        path: str,
        params: dict[str, str],
    ) -> dict[str, Any]:
        last_err: Exception | None = None
        endpoint = f"{self._cloud_url}{path}"

        sessions: list[ClientSession] = [self._session]
        if self._ipv4_session is not None:
            sessions.append(self._ipv4_session)

        for session_index, session in enumerate(sessions):
            for attempt in range(1, AIRBNK_RETRY_ATTEMPTS + 1):
                try:
                    async with session.request(
                        method,
                        endpoint,
                        headers=AIRBNK_HEADERS,
                        params=params,
                        timeout=AIRBNK_TIMEOUT,
                    ) as response:
                        if response.status != 200:
                            raise AirbnkCloudError(
                                "Airbnk cloud request failed with HTTP "
                                f"{response.status}"
                            )
                        try:
                            return await response.json(content_type=None)
                        except ValueError as err:
                            raise AirbnkCloudError(
                                "Airbnk cloud returned invalid JSON"
                            ) from err
                except (TimeoutError, ClientError) as err:
                    last_err = err
                    if attempt == AIRBNK_RETRY_ATTEMPTS:
                        break
            if not isinstance(last_err, TimeoutError):
                break
            if session_index == len(sessions) - 1:
                break

        raise AirbnkCloudError(
            f"Could not reach the Airbnk cloud: {_describe_transport_error(last_err)}"
        ) from last_err


def _describe_transport_error(err: Exception | None) -> str:
    if err is None:
        return "Request failed"
    if isinstance(err, TimeoutError):
        return "Connection timeout"
    if isinstance(err, ClientError):
        return "Connection error"
    return type(err).__name__

