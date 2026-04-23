"""Protocol tests for pyairbnk."""

from __future__ import annotations

from pyairbnk import (
    AirbnkProtocolError,
    BatteryBreakpoint,
    battery_profile_from_legacy_thresholds,
    battery_profile_from_voltage_points,
    calculate_battery_percentage,
    decrypt_bootstrap,
    extract_manufacturer_payload,
    generate_operation_code,
    parse_advertisement_data,
    parse_status_response,
    serial_numbers_match,
)

from .common import (
    build_advertisement_payload,
    build_bootstrap_fixture,
    build_status_payload,
)


def test_battery_percentage_uses_piecewise_profile() -> None:
    """Interpolate battery values against an arbitrary profile."""

    profile = (
        BatteryBreakpoint(2.3, 0.0),
        BatteryBreakpoint(2.5, 20.0),
        BatteryBreakpoint(2.7, 75.0),
        BatteryBreakpoint(2.9, 100.0),
    )

    assert calculate_battery_percentage(2.2, profile) == 0.0
    assert calculate_battery_percentage(2.6, profile) == 47.5
    assert calculate_battery_percentage(2.95, profile) == 100.0


def test_battery_profile_from_voltage_points_spreads_evenly() -> None:
    """Cloud voltage points should become evenly spaced percentages."""

    profile = battery_profile_from_voltage_points([2.4, 2.6, 2.8, 3.0])

    assert profile == (
        BatteryBreakpoint(2.4, 0.0),
        BatteryBreakpoint(2.6, 33.3),
        BatteryBreakpoint(2.8, 66.7),
        BatteryBreakpoint(3.0, 100.0),
    )


def test_bootstrap_can_be_decrypted() -> None:
    """Decrypted bootstrap data should recover the runtime keys."""

    fixture = build_bootstrap_fixture()
    bootstrap = decrypt_bootstrap(
        fixture["lock_sn"],
        fixture["new_sninfo"],
        fixture["app_key"],
    )

    assert bootstrap.lock_sn == fixture["lock_sn"]
    assert bootstrap.lock_model == fixture["lock_model"]
    assert bootstrap.manufacturer_key == fixture["manufacturer_key"]
    assert bootstrap.binding_key == fixture["binding_key"]


def test_operation_code_generation_is_stable() -> None:
    """Generate a raw operation frame from a valid bootstrap."""

    fixture = build_bootstrap_fixture()
    bootstrap = decrypt_bootstrap(
        fixture["lock_sn"],
        fixture["new_sninfo"],
        fixture["app_key"],
    )

    operation = generate_operation_code(1, 42, bootstrap, timestamp=1_700_000_000)

    assert len(operation) == 36
    assert operation[:3] == b"\xaa\x10\x1a"


def test_legacy_thresholds_preserve_three_point_curve() -> None:
    """Legacy voltage thresholds should translate into 0/50/100 points."""

    profile = battery_profile_from_legacy_thresholds([2.5, 2.6, 2.9])

    assert profile == (
        BatteryBreakpoint(2.5, 0.0),
        BatteryBreakpoint(2.6, 50.0),
        BatteryBreakpoint(2.9, 100.0),
    )
    assert calculate_battery_percentage(2.55, profile) == 25.0


def test_parsers_decode_advert_and_status_frames() -> None:
    """Parse synthetic advert and status frames."""

    advert = build_advertisement_payload()
    parsed_advert = parse_advertisement_data(advert)
    assert parsed_advert.serial_number == "B100LOCK0"
    assert parsed_advert.voltage == 3.0

    status = build_status_payload()
    parsed_status = parse_status_response(status)
    assert parsed_status.lock_events == 1
    assert parsed_status.voltage == 3.0


def test_advertisement_matching_accepts_shorter_serial_fragment() -> None:
    """A BLE advert fragment should still match the configured full serial."""

    advert = build_advertisement_payload(serial_fragment="B100LOCK0")
    parsed_advert = parse_advertisement_data(
        advert,
        expected_lock_sn="B100LOCK00000001",
    )

    assert parsed_advert.serial_number == "B100LOCK0"
    assert serial_numbers_match("B100LOCK00000001", parsed_advert.serial_number)


def test_extract_manufacturer_payload_accepts_vendor_and_prefixed_records() -> None:
    """Manufacturer data should be recognized in either known wire format."""

    payload = build_advertisement_payload()
    assert extract_manufacturer_payload({0xBABA: payload[2:]}) == payload[2:]
    assert extract_manufacturer_payload({0x004C: payload}) == payload


def test_decrypt_bootstrap_rejects_unknown_models() -> None:
    """Unsupported lock models should fail closed."""

    fixture = build_bootstrap_fixture(lock_model="Z999")

    try:
        decrypt_bootstrap(
            fixture["lock_sn"],
            fixture["new_sninfo"],
            fixture["app_key"],
        )
    except AirbnkProtocolError as err:
        assert "Unsupported Airbnk lock model" in str(err)
    else:
        raise AssertionError("unsupported model should raise")

