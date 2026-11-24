# PadBridge 0.2: implementation boundaries

PadBridge is still an experimental Android compatibility layer. A successful APK
installation is **not** evidence that its UI or playback works. Original signed
APKs remain unchanged; generated classes and decoded resource metadata are caches.

## Runtime and packaging

`padbridge backends` reports Enjarify/OpenJDK and the unavailable AOSP ART backend.
`run PACKAGE --backend aosp-art` fails explicitly, without falling back. DEX
035/037/038/039/040 metadata can be inspected. Strict Enjarify translation remains
the execution path; newer DEX headers do not imply support for invoke-custom,
invoke-polymorphic, method handles or DEX 041 containers.

`install-set base.apk feature.apk`, `inspect-set ...` and `install bundle.apks`
support a **selected** split set. Exactly one base, unique split names and matching
package/version/signers are mandatory. APK bytes are copied into private staging
before inspection. Sets are committed atomically; app data and explicit network
grants survive updates. All installed APK hashes are checked before launch.
Bundletool archives containing several alternative device variants must first be
reduced to the applicable set; PadBridge does not guess CPU/density/language splits.
Configuration-resource selection is limited: base resource values take precedence.

## Implemented framework subsets

- JVM class loading, reflection, exceptions and threads execute translated APK code.
- Basic compiled resource tables, strings/IDs/raw files and XML inflation; custom
  inflater factories, horizontal/vertical LinearLayout and FrameLayout. Resource
  bags/styles, sparse tables, complex themes and full configuration matching are
  incomplete. Explicitly unsupported data produces errors when requested.
- Handler, Looper, Message and HandlerThread dispatch queued work on the owning
  thread. Main-loop work is pumped by the native UI loop. This is not the complete
  Android MessageQueue/Choreographer implementation.
- SharedPreferences privately persists typed values using an atomic file replace;
  apply currently performs its disk commit synchronously. No world-readable modes.
- SQLiteDatabase/OpenHelper use Debian's Xerial SQLite JDBC driver: bound SQL,
  cursors, real transactions/rollback and schema versions. Nested transactions,
  custom cursor factories and the full Android SQLite API are not implemented.
- Explicit same-package Activity navigation, declared started Services, dynamically
  registered local broadcasts and declared same-process ContentProviders. No
  background restart, remote binding, system broadcasts or cross-package routing.
- PackageManager describes the current sandboxed package; ActivityManager describes
  its process. They do not expose a fake global Android package/process inventory.
- Binder/Parcel implements bounded synchronous **local** dispatch and basic typed
  values. It does not implement kernel Binder, remote handles, full modern Parcel
  wire compatibility, one-way queues, death notifications or Android system IPC.

## Graphics, native code and media

Existing JNI -> Rust -> SDL2 -> Wayland rendering remains. It renders actual APK
views and dispatches real click/D-pad callbacks. SDL selects its available renderer;
Android GLES/EGL, SurfaceView/TextureView, RelativeLayout, ConstraintLayout,
RecyclerView, full AndroidX and Leanback widgets are not implemented. Packaged
AndroidX and legacy android.support classes are treated as application code, not
automatically missing framework implementations.

ELF diagnostics identify x86-64/ARM64/ARM, dependencies and undefined symbols.
Execution is still rejected: Bionic ABI, Android linker namespaces/TLS/relocations,
JNI_OnLoad registration and ARM64 translation are not implemented. Host JNI is
working, but this does not mean arbitrary Android JNI libraries work.

`media-probe FILE` and `media-decode FILE` use FFprobe/FFmpeg inside the mandatory
sandbox without network access. The latter really decodes one unprotected video
frame and returns its checksum. These commands are the first Media Engine module,
not Android MediaPlayer/MediaCodec/AudioTrack or a finished video player. PipeWire
audio routing, VA-API decode, audio/video synchronization and 4K playback still
require implementation and hardware testing. No DRM provider or GMS is bundled.

## Next implementation gates

1. Build a pinned AOSP host ART/libcore/boot image and ICU set; run DEX fixtures
   inside the existing sandbox with the same storage/security/lifecycle contracts.
2. Implement framework resources/themes, ContextWrapper/Window/AppCompat contracts
   required by the recorded real-app launch traces. Preserve generic Android API
   behavior; do not substitute app-specific scenes.
3. Add proper Android surfaces, GPU fences and media/audio permission boundaries
   before wiring FFmpeg/PipeWire into Android media APIs.
4. Implement the Bionic linker/JNI contract and test x86-64 Android NDK libraries
   before exposing any ARM translation backend.
5. Implement an authenticated cross-process service broker and Binder semantics;
   local Binder tests do not justify advertising Android IPC compatibility.

See [the application evidence](../compatibility/apps.json) and the PadTV release
validation for actual results; unsupported modules above are not release claims.
