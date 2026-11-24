# Source study and reuse decisions (2026-11-24)

This is a focused architecture/source review, not a full audit or verification
of the projects' advertised app compatibility. The following concrete source
files were inspected before selecting the initial backend. No upstream source
was renamed as PadBridge.

| Project / source inspected | Finding and decision |
|---|---|
| [ART dalvikvm.cc](https://android.googlesource.com/platform/art/+/refs/heads/main/dalvikvm/dalvikvm.cc), blob `ebdcef17750af79a2f388c3e1e9e38ed82684854` | JNI invocation alone is not an Android framework. Boot classpath, native library namespaces and runtime dependencies need a proper port. Apache-2.0 source; retain as future backend. |
| [Android Activity.java](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/core/java/android/app/Activity.java), blob `03ef669c067520b6d7841cb97a21d4ddac5a5f4c` | Lifecycle dispatch and View ownership inform a small own facade. Full Activity depends on services and resource machinery. Apache-2.0; no implementation copied. |
| [Binder IPCThreadState.cpp](https://android.googlesource.com/platform/frameworks/native/+/refs/heads/main/libs/binder/IPCThreadState.cpp), blob `f7e0915f15c862313b6db8493ce4a8ead9398bc3` | Identity, handles and transactions need a real transport; planned broker must not be a success-returning stub. Apache-2.0. |
| [Bionic maintainer README](https://android.googlesource.com/platform/bionic/+/refs/heads/main/README.md) | libc, pthread and dynamic linker ABI are separate from Java APIs; Android native libraries cannot simply be loaded into glibc. BSD-style and component-specific licenses require per-file review. |
| [ATL meson.build](https://gitlab.com/android_translation_layer/android_translation_layer/-/raw/master/meson.build), [build instructions](https://gitlab.com/android_translation_layer/android_translation_layer/-/raw/master/doc/Build.md) | Real API/JNI/GTK separation, standalone ART and Bionic bridge; useful architecture, not a drop-in Rust runtime. No ATL code incorporated. Root LICENSE/COPYING URLs could not be verified; any future reuse must resolve exact component licenses first. |
| [ATL art_standalone Makefile](https://gitlab.com/android_translation_layer/art_standalone/-/raw/master/Makefile), [Bionic bridge meson.build](https://gitlab.com/android_translation_layer/bionic_translation/-/raw/master/meson.build) | Reduced AOSP tree and separate libc/dl wrappers plus custom dependencies. Integrating this is a dedicated backend project, not adding a single binary. |
| [reveny ACL setup-host.sh](https://raw.githubusercontent.com/reveny/Android-Compatibility-Layer/main/tools/setup-host.sh), [README](https://github.com/reveny/Android-Compatibility-Layer), [license](https://raw.githubusercontent.com/reveny/Android-Compatibility-Layer/main/LICENSE) | Host ART/AOSP build, LLVM and graphics dependencies. MIT permits reuse with notices, but README claims are not test evidence. No code incorporated. This is distinct from historical commercial OpenMobile ACL, for which no reusable open source implementation was established. |
| [Wine Unix loader](https://raw.githubusercontent.com/wine-mirror/wine/master/dlls/ntdll/unix/loader.c) | Preserve application format while translating APIs across a host boundary; separate loader from service implementations. LGPL-2.1-or-later; architectural reference only. |
| [Proton launcher](https://raw.githubusercontent.com/ValveSoftware/Proton/proton_11.0/proton) | Versioned runtime environments, per-app state and process setup are independent concerns. Proton includes multiple licenses; no code copied. |
| [Android TV app structure](https://developer.android.com/training/tv/get-started/create) | Leanback launcher metadata and D-pad navigation do not implement AndroidX Leanback widgets, Google services or TV certification. PadBridge recognizes metadata, implements only basic keyboard navigation. |
| [Enjarify main.py](https://raw.githubusercontent.com/google/enjarify/master/enjarify/main.py) | Existing Apache-2.0 DEX conversion. Default mode may produce partial classes; our adapter disables error tolerance, checks class collisions and rejects framework replacement. Debian package is reused unmodified. |

The resulting design keeps package management, diagnostics and sandbox
independent from the execution backend. A future ART/Bionic implementation can
replace Enjarify/OpenJDK without changing the Store protocol or user data.
Enjarify is an old conversion tool with known fidelity limits, not evidence of
full Android compatibility. Tests define the supported subset.
