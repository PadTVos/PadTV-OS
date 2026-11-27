# PadBridge 0.5 — experimental Android compatibility for Linux

PadBridge installs **unmodified, signed APKs and verified split APK sets** and executes a small
subset of Android applications directly on Linux. Its package manager,
supervisor, diagnostics and native rendering bridge are Rust. Java facades
implement the supported Android API signatures. No virtual Android device, Android OS or Waydroid
is started. This release accompanies **PadTV OS 0.8**; the two version numbers
describe different projects.

Two explicit backends are available: the existing **Enjarify / OpenJDK 21**
backend and a new **AOSP ART / matched libcore** host runtime. ART executes original
DEX, including Java/Kotlin, multidex and split APKs, inside the mandatory sandbox.
JNI_CreateJavaVM succeeds with the matched boot classpath and generated boot image.
Original fixture APKs render native widgets on Wayland and respond to D-pad input.

**Jellyfin, YouTube TV and Netflix remain blocked.** The ART VM is functional;
complete Android framework and native/media compatibility are not. Existing
Enjarify Canvas/media/WebView/HTTPS functionality is preserved. Those tests are
not evidence that the corresponding ART paths or streaming apps work.
Read the [0.5 implementation boundaries](docs/runtime-0.5.md) and
[application records](compatibility/apps.json) before testing.

## Build and test (Debian 13 amd64)

```sh
sudo apt-get install --no-install-recommends rustc cargo pkg-config \
  libsdl2-dev libsdl2-ttf-dev libsdl2-image-dev openjdk-21-jdk-headless \
  aapt apksigner libsmali-java android-framework-res enjarify bubblewrap \
  fonts-dejavu-core python3 python3-pil dpkg-dev kotlin libxerial-sqlite-jdbc-java ffmpeg clang lld libavformat-dev libavcodec-dev libavutil-dev \
  libswscale-dev libswresample-dev libegl-dev libgles-dev libegl-mesa0 \
  libgl1-mesa-dri libasm-java chromium openssl pulseaudio-utils
bash scripts/build.sh
cargo test --workspace --locked
python3 tests/build_fixtures.py
python3 tests/integration.py
python3 scripts/fetch-test-tools.py
python3 tests/build_runtime_fixtures.py
python3 tests/runtime05.py
python3 tests/build_native_fixtures.py
python3 tests/analyzer_unit.py
python3 tests/runtime06.py
python3 tests/thirdparty06.py
python3 tests/build_media_fixtures.py
python3 tests/resources07.py
python3 tests/audio_broker07.py
python3 tests/runtime07.py
python3 tests/media07.py # needs a running real PulseAudio or PipeWire-pulse server
python3 tests/build_framework_fixtures.py
python3 tests/resources08.py
python3 tests/framework08.py
python3 tests/build_art_fixtures.py
PADBRIDGE_RUNTIME_DIR=$PWD/build/runtime target/release/padbridge setup-art
python3 tests/art08.py
bash scripts/build-deb.sh
sudo apt-get install ./build/padbridge_0.5.0_amd64.deb
```

Run the original runtime05 unavailable-backend test before installing ART, or set
`PADBRIDGE_ART_ROOT` to a nonexistent directory for that suite. ART integration
tests require a successfully activated installation and must not be skipped for a release.

Integration tests require a real Linux user namespace environment. They fail
when sandboxing is unavailable; there is no insecure fallback and no skipped
isolation test. A chroot is often insufficient. For an uninstalled build set
`PADBRIDGE_RUNTIME_DIR=$PWD/build/runtime` and use `target/release/padbridge`.

```sh
padbridge backends
padbridge setup-art  # optional pinned download; real JNI/DEX activation test
padbridge run org.example.app --backend aosp-art
padbridge certificates org.example.app
padbridge trust-certificate org.example.app public-ca.pem
padbridge untrust-certificate org.example.app CERTIFICATE_SHA256
padbridge install-set base.apk feature.apk
padbridge inspect-set selected-bundle.apks
padbridge media-probe unprotected-video.mkv
padbridge media-decode unprotected-video.mkv
padbridge inspect example.apk
padbridge install example.apk
padbridge permissions org.example.app '["android.permission.INTERNET"]'
padbridge run org.example.app
padbridge diagnose example.apk
padbridge analyze example.apk --html report.html
padbridge remove org.example.app       # retain private data
padbridge remove org.example.app --delete-data
```

All CLI commands return JSON. `run` keeps a log per app and returns a nonzero
exit status on failure. `--headless` executes lifecycle and exposes a scene
snapshot and actual Canvas PNGs in private application data for pixel tests.
It does not verify compositor presentation or physical display hardware. `--restart-once`
retries an abnormal process exit once; unsupported APIs do not restart-loop.

- [Architecture, backend decision and milestones](docs/architecture.md)
- [Current 0.5 implementation and remaining modules](docs/runtime-0.5.md)
- [ART integration research](docs/art-0.2-research.md)
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
