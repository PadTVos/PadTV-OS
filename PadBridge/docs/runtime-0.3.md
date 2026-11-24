# PadBridge 0.3 / PadTV 0.6 — tested boundaries

This release keeps Enjarify/OpenJDK and the existing manager, grants, data and
Wayland host. It does not start Android. It is an experimental compatibility
subset, not general Android TV support.

## Real third-party APK

Screen Test 4K 1.0.1 (`com.chucktech.sceentest`) from
[LuoJuly's repository](https://github.com/LuoJuly/TV_Screen_4K_Calibration_TEST),
commit `ddf6367504568834b0ba70beef561bc6ac5081d6`, SHA-256
`a68b762262f57ae77ba0faead7499e1907093329b58752bd957b18284446752e`.
The original signed APK bytes are retained. Neither the APK nor its code is
modified. No package-specific framework behavior was added.

Verified: signature/install, original DEX execution, fullscreen SDL/Wayland
window at 1600×900, green pattern 4/35 and 2-pixel checkerboard 13/35, D-pad
navigation. Automated tests additionally inspect real Canvas PNG pixels and
confirm that the center button hides the application's controls. Waydroid is
stopped during these tests. Remaining patterns, physical remote controls,
4K rendering, color calibration and hardware acceleration are not certified.
Third-party APKs are fetched for private testing and are not redistributed.

## Framework and rendering

Actual Window content/callback dispatch, fullscreen and keep-awake flags,
Display/DisplayMetrics, focus listeners, visibility, lifecycle attachment,
SparseArray, TextView size/color, invalidation and Looper-driven callbacks.
Canvas/Paint implement shapes, lines, text, transforms, clipping, bitmap
textures and linear gradients through Java2D. The resulting PNG textures are
presented by SDL2 on Wayland; cached textures avoid decoding unchanged PNGs
every frame. This is CPU Canvas rendering, not Android Skia/GLES acceleration.
Bitmap dimensions are checked before decoding and allocation is bounded.

FrameLayout/LinearLayout and the previous XML resource path remain. Full
AppCompat, FragmentManager, AndroidX/Leanback, themes/styles, animations,
RelativeLayout, ConstraintLayout, RecyclerView, SurfaceView/TextureView and
Android EGL/GLES are unfinished. Empty substitute classes are not supplied.
Binder remains process-local; there is no kernel Binder interoperability.

## Native path

An original APK can call `System.loadLibrary`, JNI_OnLoad and JNI methods in a
**freestanding little-endian x86-64 ET_DYN** library compiled for Android.
The first implementation preflights ELF, selects x86-64 variants and binds
the libraries read-only into the app sandbox. Linux's dynamic loader performs
the relocations. Libraries with DT_NEEDED, undefined symbols, an interpreter
or PT_TLS are rejected before execution. This is not the Android dynamic
linker or a Bionic libc implementation. Calling-convention compatibility in
this limited subset does not imply compatibility with arbitrary NDK code.

The native fixture verifies original DEX → JNI → native arithmetic/string
return and raw Linux syscall isolation. `/tmp` host files, `/etc/shadow` and
another app's host path are unavailable. Read-only runtime/native bindings,
private `/data`, namespaces and grants remain mandatory; there is no fallback
outside bubblewrap. Syscall/API sandbox hardening beyond the existing namespace
boundary remains future work. Native code still shares its own JVM process.

ARM64/ARMv7/32-bit x86 execution is unavailable. QEMU user-mode translation is
a research candidate, not an integrated backend. FEX translates x86 to ARM64
and does not solve the required opposite direction. Bionic/TLS behavior needs
a dedicated ABI environment and tests before these restrictions can be lifted.
[AOSP linker changes](https://android.googlesource.com/platform/bionic/+/refs/heads/android15-tests-release/android-changes-for-ndk-developers.md),
[AOSP ELF TLS](https://android.googlesource.com/platform/bionic/+/HEAD/docs/elf-tls.md),
[QEMU user emulation](https://www.qemu.org/docs/master/user/main.html).

## ART, WebView and multimedia — incomplete

`scripts/probe-art.py` tests Debian 13's actual android-libart 14.0.0+r15-4+b1
shared-library dependencies. Loading base/log/sigchain is not DEX execution.
The probe encounters an unresolved tinyxml2 XMLPrinter vtable after preloading
the Debian Android support libraries. A matching host ART/libcore boot class
path, JNI/ICU libraries, VM creation and direct DEX tests are still required.
`aosp-art` remains explicitly unavailable and never silently falls back.
Modern invoke-custom/invoke-polymorphic/const-method-handle instructions and
DEX 041 containers are diagnosed, not claimed to execute.
[DEX format](https://source.android.com/docs/core/runtime/dex-format).

Android WebView has not been connected to Chromium. TVBro is not replaced by a
web shortcut. Its immediate failure is Enjarify output rejected by the JVM:
`tp.onRetainNonConfigurationInstance()` constructs `qp` but directly invokes
`Object.<init>`; `qp` has no constructor in the translated JAR. The translator
needs a general, verified implementation of Android constructor semantics.
Disabling JVM verification is not a solution. AppCompat/resources and WebView
remain further requirements after this blocker.

Launch on Boot progresses beyond its former missing focus listener and
SparseArray; the next observed failure is `android.view.animation.Animation`
inside support FragmentHostCallback. A real animation/resource/AppCompat
implementation is needed, not a stub for this APK.

Existing FFmpeg probe/single-frame software decode remains tested. Android
MediaPlayer, AudioTrack, AudioManager, MediaCodec, continuous audio/video,
PipeWire routing from Android, VA-API and 4K playback are **not implemented or
verified** in this release. DRM/Widevine has no licensed provider; GMS and
device certification are not provided.

## Analyzer and Store

`padbridge analyze app.apk --html report.html` verifies signatures and performs
bounded static DEX analysis in a separate no-network sandbox. It handles APKM
and selected split sets, reports missing classes and exact method descriptors,
modern instructions with method/offset, ELF architectures/dependencies/symbols,
and static GMS/DRM references. Methods are resolved against actual framework
and OpenJDK base signatures, including inheritance and APK-defined classes.
Static references include dormant bundled libraries. Reflection, dynamically
loaded code and behavioral equivalence cannot be inferred from these tables.
Observed exceptions are separate and only attached when the installed build
hash matches. HTML escapes all APK/report text; no APK HTML/scripts execute.

The PadTV Store downloads first-party Runtime Probe from a real GitHub Release.
The bundled catalog pins HTTPS URL, exact size, SHA-256 and APK signer. Only
GitHub asset redirects are allowed. Installation rechecks package identity,
signature and inventory. Uninstall keeps app data. The release is an explicit
test fixture; Screen Test provides independent third-party compatibility proof.
User-supplied YouTube/Netflix packages are tested privately, never uploaded.
