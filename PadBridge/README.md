# PadBridge 0.1 — experimental Android compatibility for Linux

PadBridge installs **unmodified, signed standalone APKs** and executes a small
subset of Android applications directly on Linux. Its package manager,
supervisor, diagnostics and native rendering bridge are Rust. Java facades
implement the supported Android API signatures. No Android OS, VM or Waydroid
is started. This release accompanies **PadTV OS 0.4**; the two version numbers
describe different projects.

The first execution backend uses strict **Enjarify DEX 035 → JVM translation and
OpenJDK 21**, not ART. Only the subset in [API compatibility](docs/api.md) is
implemented. It is not a general Android emulator and cannot currently run
YouTube TV or Netflix. Android native `.so` files, ARM translation, Google Play
Services, media playback and DRM are not implemented. See the
[app database](compatibility/apps.json) and [milestones](docs/architecture.md).

## Build and test (Debian 13 amd64)

```sh
sudo apt-get install --no-install-recommends rustc cargo pkg-config \
  libsdl2-dev libsdl2-ttf-dev libsdl2-image-dev openjdk-21-jdk-headless \
  aapt apksigner libsmali-java android-framework-res enjarify bubblewrap \
  fonts-dejavu-core python3 dpkg-dev
bash scripts/build.sh
cargo test --workspace --locked
python3 tests/integration.py
bash scripts/build-deb.sh
sudo apt-get install ./build/padbridge_0.1.0_amd64.deb
```

Integration tests require a real Linux user namespace environment. They fail
when sandboxing is unavailable; there is no insecure fallback and no skipped
isolation test. A chroot is often insufficient. For an uninstalled build set
`PADBRIDGE_RUNTIME_DIR=$PWD/build/runtime` and use `target/release/padbridge`.

```sh
padbridge inspect example.apk
padbridge install example.apk
padbridge permissions org.example.app '["android.permission.INTERNET"]'
padbridge run org.example.app
padbridge diagnose example.apk
padbridge remove org.example.app       # retain private data
padbridge remove org.example.app --delete-data
```

All CLI commands return JSON. `run` keeps a log per app and returns a nonzero
exit status on failure. `--headless` executes lifecycle and exposes a scene
snapshot for tests; it does **not** verify rendered pixels. `--restart-once`
retries an abnormal process exit once; unsupported APIs do not restart-loop.

- [Architecture, backend decision and milestones](docs/architecture.md)
- [Actual API subset](docs/api.md)
- [Source study and license decisions](docs/research.md), [third-party notices](THIRD_PARTY.md)
- [Sandbox and data model](docs/security.md)
- [Secure Media Engine roadmap](docs/secure-media.md)
- [Other distributions](docs/integration.md)
- [Verification record](docs/validation.md)

## PadTV ecosystem

[OS](https://github.com/PadTVos/PadTV-OS) ·
[Updates](https://github.com/PadTVos/PadTV-Updates) ·
[Store](https://github.com/PadTVos/PadTV-Store) ·
[Apps](https://github.com/PadTVos/PadTV-Apps) ·
[Website/docs](https://github.com/PadTVos/PadTV-Website)

Own code: Apache-2.0. Dependencies retain their respective licenses. Test APK
source is included; throwaway signing keys are generated locally and ignored.
