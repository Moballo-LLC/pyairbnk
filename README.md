# pyairbnk

`pyairbnk` is the standalone async communication library behind the
[`Airbnk BLE`](https://github.com/Moballo-LLC/airbnk-ble) Home Assistant
integration.

## Disclaimer

`pyairbnk` is an unofficial community-maintained library. It is not made by,
sponsored by, endorsed by, or otherwise affiliated with Airbnk, WeHere, or
their vendors in any way.

Use this library at your own discretion and risk. You are responsible for how
you use it, where you deploy it, and what devices, accounts, or systems you
connect it to.

It provides:

- Airbnk / WeHere cloud onboarding helpers for verification codes, auth, lock
  listing, and battery-profile lookup
- Local BLE protocol helpers for bootstrap decryption, advert parsing, status
  parsing, and operation-code generation
- A generic async BLE command client built on `bleak` and
  `bleak-retry-connector`

## Support Status

`B100` and `M532` have been live-validated on real hardware so far. The
protocol/profile surface also includes `M300`, `M500`, `M510`, `M530`, and
`M531`, but those are currently covered through shared logic and sanitized
fixtures rather than equivalent field testing.

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
2. creates a GitHub release on `v*` tags using the matching `CHANGELOG.md`
   section as the release body
3. publishes to PyPI using Trusted Publishing

To publish a release, merge a PR that updates `pyproject.toml`,
`src/pyairbnk/__init__.py`, and `CHANGELOG.md`, then tag the merged `main`
commit:

```bash
git switch main
git pull --ff-only
git tag v1.1.0
git push origin v1.1.0
```

The workflow validates that the tag matches the package version. For example,
`v1.1.0` must match `[project].version = "1.1.0"`, and `CHANGELOG.md` must
contain a `## 1.1.0` section.

## Credits

This library was built from the local BLE work in `Airbnk BLE` and informed by
the earlier GPLv3 reverse-engineering efforts in
[rospogrigio/airbnk_mqtt](https://github.com/rospogrigio/airbnk_mqtt) and
[rospogrigio/airbnk_cloud](https://github.com/rospogrigio/airbnk_cloud).
