# PadBridge development

Keep the runtime independent of Waydroid and of PadTV's Python UI. Do not remove
existing application data. Use structured errors for unsupported APIs; never
report successful playback, installation, certification or isolation without a
real implementation and recorded tests. Preserve original APK bytes and verify
signatures. Never weaken the mandatory Linux sandbox to make a test pass.

Build on Debian 13 with `scripts/build.sh`, run `cargo test --workspace --locked`
and `python3 tests/integration.py`. Keep API and compatibility documentation
consistent with the tested implementation. No signing keys or third-party APKs
belong in this repository. Changes to DRM may not bypass licensing or access
controls. Keep source provenance and dependency licenses documented.
