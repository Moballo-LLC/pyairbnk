# pyairbnk

`pyairbnk` is the standalone async communication library behind the
[`Airbnk BLE`](https://github.com/Moballo-LLC/airbnk-ble) Home Assistant
integration.

It provides:

- Airbnk / WeHere cloud onboarding helpers for verification codes, auth, lock
  listing, and battery-profile lookup
- Local BLE protocol helpers for bootstrap decryption, advert parsing, status
  parsing, and operation-code generation
- A generic async BLE command client built on `bleak` and
  `bleak-retry-connector`

## Support Status

`B100` is the only model that has been live-validated end to end on real
hardware so far. The protocol/profile surface also includes `M300`, `M500`,
`M510`, `M530`, and `M531`, but those are currently covered through shared
logic and sanitized fixtures rather than equivalent field testing.

## Installation

```bash
pip install pyairbnk
```

For local development:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
```

## Design Notes

- The library is async-first so it can be consumed cleanly by Home Assistant.
- HTTP clients accept injected `aiohttp` sessions, which matches Home
  Assistant's dependency guidance.
- No Home Assistant imports are used anywhere in the package.

## Releasing

The repository includes a GitHub Actions release workflow that:

1. builds the sdist and wheel
2. creates a GitHub release on `v*` tags
3. publishes to PyPI using Trusted Publishing

One manual setup step is still required on PyPI: add
`Moballo-LLC/pyairbnk` as a Trusted Publisher for the
`.github/workflows/release.yml` workflow. PyPI documents that setup here:
[Adding a Trusted Publisher](https://docs.pypi.org/trusted-publishers/adding-a-publisher/).

After that PyPI-side setup is complete, enable the repository variable
`PYPI_PUBLISH_ENABLED=true` so tagged releases also publish to PyPI.

## Credits

This library was built from the local BLE work in `Airbnk BLE` and informed by
the earlier GPLv3 reverse-engineering efforts in
[rospogrigio/airbnk_mqtt](https://github.com/rospogrigio/airbnk_mqtt) and
[rospogrigio/airbnk_cloud](https://github.com/rospogrigio/airbnk_cloud).
