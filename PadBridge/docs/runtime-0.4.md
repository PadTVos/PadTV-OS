# PadBridge 0.4 — implemented behavior and boundaries

This is an experimental Linux compatibility runtime, not Android. Original,
signed APK/split/APKM bytes are preserved. Derived JVM caches can change; APKs
cannot replace host framework classes. No Waydroid, Android VM or web replacement
was used for the Android compatibility results. PadTV's older independent web
apps and Waydroid option remain available without being counted as APK support.

## Implemented and exercised

| Module | Actual implementation | Verified boundary |
|---|---|---|
| DEX | Strict Enjarify → OpenJDK 21, multidex/splits; exception handler at DEX address zero; conservative constructor-elision repair through absent constructors in the ancestor chain using ASM | Original SDK/smali APKs execute class identity, constructor arguments, side effects, exception flow. JVM verification stays enabled. Derived synthetic constructors can be visible through JVM reflection; exact ART reflection equivalence is not claimed. DEX 035/037–040 metadata is accepted; unsupported opcodes still fail. |
| Application | Original manifest Application, attached ContextWrapper and Activity lifecycle callbacks | Context identity, creation before Activity, full callback order and Base64 behavior |
| Resources | UTF-8/CESU-8/MUTF-8, sparse and 16-bit offsets, compact entries | Valid supplementary characters and binary entries, rejection of truncation/malformed data. Complex themes/configuration selection remain incomplete. |
| Native | JNI RegisterNatives and conservative unversioned x86-64 memory/scalar ABI; generation-checked JNI media/GL handles | Original Android-target ELF calls allocation, memory/string functions and JNI. Unsupported optional libraries are diagnosed and not staged; actual loading fails. |
| MediaExtractor | libavformat local/HTTP(S) demux, track metadata/CSD, Android Annex-B AVC/HEVC samples, PTS, keyframes, EOS and previous/next sync seek | H.264 + AAC test container, including verified HTTPS. Closest-keyframe search and arbitrary HTTP headers unsupported. |
| MediaCodec | Synchronous libavcodec software decoding; swscale RGBA and swresample PCM16; ownership/flush/EOS and Surface output | Full 30-frame H.264 video byte-compared to FFmpeg, AAC output and timestamps checked. Encoder, secure decoding, async callbacks and dynamic codec-config buffers unsupported. |
| AudioTrack | Streaming PCM16 mono/stereo through a separate bounded playback-only SDL broker to PulseAudio/PipeWire-pulse | Real server monitor captures 440 Hz PCM, pause freezes playback queue. No microphone/socket/device selection API is exposed. Physical HDMI audio not tested. |
| MediaPlayer | Worker demux/decode, Surface presentation, PCM audio, clock, listeners, pause/resume/seek/replay/EOS | APK calls the Android APIs; test checks completion, images, real server audio and pause/seek/replay. Test clip is 160×90, not a 4K certification. |
| Surface / SurfaceView | Surface lifecycle, Canvas posting and decoded RGBA uploaded into the existing SDL Wayland scene | Actual pixels and surface callbacks. CPU image copying; no Android BufferQueue/gralloc/ANativeWindow ABI. |
| EGL / GLES | Mesa surfaceless EGL and real GLES2 shaders, pbuffer, vertex buffers and pixel readback; window Surface receives copied RGBA | Real red triangle over blue pixels. CPU/Mesa path verified; hardware acceleration, direct scanout and full GLES API not verified. |
| WebView | Actual Chromium inside the app sandbox; DevTools pipes, HTML/HTTP(S), optional JS, screenshots and D-pad key forwarding | Original APK JS changes real DOM and actual green page pixels. Chromium sandbox remains enabled. No Android Chromium JNI, CookieManager, complete settings, WebView audio/DRM or full embedding API. |
| HTTPS / certificates | OpenJDK networking and FFmpeg TLS validation; explicit per-app public CA import/revoke; integrity checked read-only trust stores | No INTERNET → denied; untrusted CA → rejected; explicit CA → success; wrong hostname/revoked CA → rejected. Private keys rejected. Custom app trust currently applies to JVM/FFmpeg, not Chromium. |

Codec availability is determined by the installed FFmpeg decoders. MIME adapters
exist for H.264, HEVC, VP8/VP9, AV1, MPEG-4, AAC, MP3, Opus, Vorbis, FLAC and PCM;
that is **not** a per-codec, hardware or 4K verification claim. VA-API zero-copy,
HDR, AV sync under load, multichannel audio and hardware HDMI need separate work.

## Experimental or unsupported

The native ABI is **not full Bionic**. TLS, versioned Bionic symbols, pthread/FILE
structure ABIs, Android dynamic linker namespaces, ARM32/ARM64 translation and
32-bit x86 ELF are rejected. An unsupported unused native library no longer
prevents Java code from running, but calling it still fails. No native dependency
is silently replaced by a successful stub.

ART research progressed to loading Debian's host libart and invoking
`JNI_CreateJavaVM`; it returned `-1` with an empty boot classpath. Matching libcore
boot DEX/image and Android runtime/framework integration are absent. The backend
remains unavailable and Enjarify remains selected. Next: build a matching AOSP
ART+libcore host target, prove original DEX execution and JNI, then integrate the
same mandatory sandbox before exposing it. The reproducible probe is
`python3 scripts/probe-art.py --create-vm-probe`.

Complete ActionBar/AppCompat themes, AndroidX/Leanback/Compose, RecyclerView,
ConstraintLayout, TextureView, cross-process Android Binder, Google Play Services,
Widevine, secure video paths, HDCP and device certification are not implemented.
Existing small framework components were retained; class presence does not
mean every method is supported. Static class/method/ELF diagnostics and actual
observed runtime failures remain separate in JSON and HTML reports.

Jellyfin playback is **not achieved in this release**. See the exact original
APK results in `compatibility/apps.json` and PadTV `docs/validation-0.7.md`.
New API fixtures demonstrate infrastructure, not compatibility of those apps.

## Sources and next steps

- [AOSP ART build instructions](https://android.googlesource.com/platform/art/+/refs/heads/main/build/README.md): host ART must be built with matching dependencies.
- [Android MediaCodec contract](https://developer.android.com/reference/android/media/MediaCodec) and [MediaExtractor](https://developer.android.com/reference/android/media/MediaExtractor): buffer ownership, CSD, sample format and lifecycle.
- [FFmpeg send/receive API](https://ffmpeg.org/doxygen/trunk/group__lavc__encdec.html): actual packet/frame decoding and EOS.

Priorities after the recorded app blockers: implement general Android framework
semantics and matching resource/theme behavior, complete DEX opcode/verifier
compatibility, then test the original Jellyfin UI, server authentication and
non-DRM video/audio end-to-end. Do not replace its player with a separate native
or web app and call that success.
