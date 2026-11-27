# PadBridge 0.5: ART integration and remaining boundaries

This release executes original DEX on a real AOSP ART Linux host build. It does
**not** make Jellyfin Android TV, YouTube TV or Netflix fully compatible.
The successful VM and fixture tests are separate from those application results.

## Runtime and provenance

`padbridge setup-art` fetches the R8 project's pinned AOSP ART 16 host test bundle,
validates all 591,238,194 bytes against SHA-256
`375302f225cfd66c066b243fcda3fe8535693ccbb205937e3d8a858a1b9ab713`, and extracts only
the x86-64 host executables, libraries, boot DEX, ICU and timezone data. It never
extracts a device system image. No Android emulator, Waydroid, Android init,
system_server or zygote is started.

Provenance is pinned to [R8 commit f8ff923](https://r8.googlesource.com/r8/+/f8ff923130e5da6265c9e246ba0be5b7acd2396d/tools/linux/README.art-versions).
`build_spec.xml` in the verified upstream archive records its source revisions.
The AOSP `master-art` source checkout was investigated, but a fresh source build
was **not** completed for this release. We use the upstream host build, not an
independently built or certified Android distribution. The upstream binary archive
is not mirrored in PadTV releases; the setup command downloads it directly.

The matching boot classpath is core-oj, core-libart, okhttp, bouncycastle,
apache-xml, core-icu4j and conscrypt. Sandboxed `dex2oat64` builds an x86-64 boot
image with the verify compiler filter. Activation then calls the real
`JNI_CreateJavaVM`, executes our original probe DEX, and destroys the VM.
The result must be **0**, with actual reflection, exception and threaded code
execution, before an installation is marked ready. Every launch rechecks the
installed component hashes. The former Debian ART probe's `-1` came from an
incomplete/mismatched boot environment; loading `libart` alone was insufficient.
The old probe is retained as historical research, not the backend readiness check.

```sh
padbridge setup-art                 # Linux x86-64; internet and ~2 GB free space
padbridge backends
padbridge run org.example.app --backend aosp-art
padbridge run org.example.app --backend enjarify-openjdk
```

The default installation is `~/.local/share/padbridge-runtimes/art-16.0.0` (or
XDG_DATA_HOME). `PADBRIDGE_ART_ROOT` selects an explicit installation.
`setup-art --archive /path/to/archive.tar.gz` supports an offline **identical**
pinned archive. Setup still verifies its digest and executes the sandboxed probe.
The previous backend remains the default. PadTV's app management dialog offers
per-app selection and download; refreshing the catalog retains that selection.

ART reads the original installed APK and split APKs directly. Only a separate
resource/XML cache is derived; original DEX is not translated or patched.
The PadBridge Java framework itself is compiled to a separate DEX archive by D8.
SDK API jars are build-time inputs, never runtime implementations or shipped stubs.
DEX metadata versions 035–040 are accepted; 041 containers remain unsupported.
JIT is disabled in this first integrated backend. This is not a performance claim.

## Framework changes

- Actual global-layout, pre-draw cancellation, draw, scroll, focus, attachment,
  touch-mode and window-focus events; layout callbacks carry real bounds.
- MarginLayoutParams with directional margins, parent-specific Linear/Frame
  layout parameters, padding and scroll coordinates. The existing simplified
  native layout engine remains; full Android measure/layout is not implemented.
- Compiled style bags, parent inheritance, typed values and TypedArray/Theme
  lookup. Full configuration selection, framework system resources and all XML
  style precedence are not implemented.
- BaseBundle typed data/copy semantics, Parcelable contracts and float/double
  Parcel encoding. This is not cross-process Android Binder wire compatibility.
- Same-process ContentProvider startup before Application.onCreate, initOrder,
  typed manifest metadata, ProviderInfo, authority aliases and one instance per
  provider. Disabled and other-process providers are not started. There is no
  remote provider/Binder service substitution.
- Context.getMainLooper, real context menus and D-pad key down/up consumption.
- Bounded private Trace records with monotonic timestamps, nested/async events
  and counters when explicitly enabled with `padbridge.trace=true`.
- Log priority/exception APIs use the real per-app stderr log.
- Shared XML parsing works with OpenJDK and libcore, rejects DTD/entities and
  external resolution, and bounds input size; unsupported parser-specific flags
  do not disable the provider-independent protections.
- Original AOSP TypedValue, MathUtils, FontScaleConverter, Size, SizeF,
  TvContentRating and selected TextUtils/Preconditions methods are reused with
  provenance and Apache-2.0 notices. See `third_party/aosp-utilities.json`.

Build metadata identifies **PadBridge on Linux**, exposes only x86-64 as a
supported native ABI, and does not expose host serials or claim a device
fingerprint/security patch certification. SDK_INT=34 is the chosen Android 14
**behaviour profile**, not proof of all API 34 methods. VERSION.RELEASE identifies
PadBridge. An API-level check cannot replace capability or execution testing.

## Why a complete AOSP framework is not a drop-in jar

ART/libcore is now executable, but Android's full framework also depends on native
Android runtime methods, Binder services, package/resource services, graphics
buffers and Android-specific process state. The [AOSP module build](https://android.googlesource.com/platform/art/+/refs/heads/main/build/README.md)
does not provide those services merely by creating a Java VM. This release reuses
portable AOSP implementations instead of shipping SDK jars whose methods throw
`Stub!`. Complete AndroidX, Compose and Leanback remain unsupported.

## Backend-specific limits

Enjarify retains the existing tested Java2D Canvas, SQLite JDBC, FFmpeg,
restricted playback broker, EGL/GLES and Chromium WebView components.
ART has verified original Java/Kotlin execution, multidex/split loading, native
widget rendering on Wayland and D-pad input. **The Java2D Canvas/Bitmap path and
SQLite JDBC are not ported to ART/libcore.** Their OpenJDK tests do not establish
ART media playback. ART-specific media, WebView, HTTPS/CA management and device
integration still require implementation/verification; no fallback player is
used to conceal those limitations.

The existing restricted x86-64 scalar/memory/JNI ABI remains. ART's host JNI
libraries are glibc builds, not a complete Bionic dynamic linker for APK libraries.
Android TLS, symbol versions, full native dependencies and ANativeWindow/gralloc
are not supported. x86-32 needs a separate 32-bit VM, framework JNI binaries and
loader environment; a 64-bit process cannot load it. ARMv7/ARM64 translation is
not implemented. No DRM, Widevine, GMS or device certification is added.

## Diagnosis and next milestone

The supervisor writes `<package>.startup.json` with package identity, backend,
integrity, DEX/native preparation, sandbox and exit stages. Java lifecycle markers
are reported separately as **untrusted application output**, not attestations.
An unsupported API exits with an error; it never silently selects another backend.

Continue from the exact original-APK failure records in
`compatibility/reports-0.5/`. Jellyfin still needs system-service adapters,
AndroidX initialization, complete resource/theme/layout handling, ART-compatible
graphics and its native media dependencies. Only then can its original UI,
real server connection, video/audio, pause, seek and subtitles be evaluated.
Long 1080p playback in Jellyfin has **not** been demonstrated.
