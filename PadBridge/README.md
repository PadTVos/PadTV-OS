# PadBridge 0.4 — experimental Android compatibility for Linux

PadBridge installs **unmodified, signed APKs and verified split APK sets** and executes a small
subset of Android applications directly on Linux. Its package manager,
supervisor, diagnostics and native rendering bridge are Rust. Java facades
implement the supported Android API signatures. No Android OS, VM or Waydroid
is started. This release accompanies **PadTV OS 0.7**; the two version numbers
describe different projects.

The first execution backend uses strict **Enjarify DEX → JVM translation and
OpenJDK 21**, not ART. Only the subset in [0.4 implementation boundaries](docs/runtime-0.4.md) is
implemented. It is not a general Android emulator and cannot currently run
YouTube TV or Netflix. **Screen Test 4K 1.0.1**, an unmodified third-party TV APK,
renders through Canvas/Wayland and responds to D-pad input with Waydroid stopped.
The 0.4 release adds real FFmpeg demux/decode, PCM playback through a restricted
Linux broker, MediaPlayer/SurfaceView, Mesa EGL/GLES2 rendering, Chromium WebView,
per-app HTTPS trust and a bounded x86-64 scalar/memory ABI bridge. Their SDK-built
APK integration tests exercise original DEX code, not a replacement player.
**Jellyfin, YouTube and Netflix remain blocked.** ART execution, full Bionic and
the Android linker, ARM translation, complete AndroidX/Leanback/Compose, GMS,
DRM and certified playback are unavailable. See the [app database](compatibility/apps.json).

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
bash scripts/build-deb.sh
sudo apt-get install ./build/padbridge_0.4.0_amd64.deb
```

Integration tests require a real Linux user namespace environment. They fail
when sandboxing is unavailable; there is no insecure fallback and no skipped
isolation test. A chroot is often insufficient. For an uninstalled build set
`PADBRIDGE_RUNTIME_DIR=$PWD/build/runtime` and use `target/release/padbridge`.

```sh
padbridge backends
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
- [Current 0.4 API subset and remaining modules](docs/runtime-0.4.md)
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
