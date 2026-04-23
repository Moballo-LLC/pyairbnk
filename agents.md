# Repository Guidance

## Product Intent

- This repository publishes the standalone async Airbnk / WeHere communication
  library used by `Airbnk BLE`.
- It should stay free of Home Assistant-specific imports so it remains suitable
  for a future Home Assistant core integration.

## Security Boundaries

- Never commit real account emails, verification codes, tokens, `appKey`,
  `newSninfo`, MAC addresses, serial numbers, or captured payloads from a live
  home environment.
- Tests and fixtures must stay synthetic or heavily redacted.

## Hardware Support

- `B100` is the only live-validated model today.
- Other declared model profiles should be described as logic-tested rather than
  equally field-tested.

## Implementation Preferences

- Keep the library async-first.
- Accept injected `aiohttp` sessions instead of creating framework-specific
  global clients inside the package.
- Keep protocol code separate from higher-level config-entry concerns.
- Preserve the existing BLE command behavior that already works on the
  `B100`; avoid speculative rewrites.

## Repo Workflow

- Keep CI, typing, and packaging green.
- Keep release automation ready for PyPI Trusted Publishing, but never hard-code
  secrets into workflows or config files.
- Prefer small commits when it helps keep the extraction reviewable.

