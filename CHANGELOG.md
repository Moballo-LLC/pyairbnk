# Changelog

## 1.2.0

- Added provisional `M521` model support and a generic fallback profile for
  newly observed Airbnk lock models

## 1.1.0

- Added a live-validated `M532` model profile with remote-lock support
- Restored CI type checking for the mutable BLE operation checksum buffer
- Updated release automation to publish the matching `CHANGELOG.md` section as
  the GitHub release body
- Added release guidance and version consistency checks for future release prep

## 1.0.1

- Published the first PyPI-backed release using GitHub Actions Trusted
  Publishing
- Added explicit public README disclaimers that the project is unofficial and
  unaffiliated with Airbnk and WeHere

## 1.0.0

- Initial standalone release of the extracted Airbnk / WeHere communication
  library
- Added async cloud onboarding client with session injection and IPv4 fallback
  support
- Added BLE command client for active lock operations and connectivity probes
- Added protocol helpers for bootstrap decryption, advert parsing, status
  parsing, and battery profile handling
