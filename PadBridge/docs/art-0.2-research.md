# Host ART integration review

Reviewed 2026-11-24. ART is an Android runtime plus a matching managed boot class
library, native libcore/JNI implementation, boot image and platform assumptions.
Replacing the `java` command with `dalvikvm` cannot run this JVM framework.jar:
the framework must also be compiled to DEX, and native class-library integration
and boot-class-path ordering must be implemented and validated.

Primary references:

- [AOSP DEX specification](https://source.android.com/docs/core/runtime/dex-format)
  distinguishes version extensions (including newer instructions and the 041
  container format). Accepting a header alone is not an implementation of them.
- [AOSP ART source](https://android.googlesource.com/platform/art/)
  and [master-art manifest](https://android.googlesource.com/platform/manifest/+/refs/heads/master-art/)
  are the upstream route to a Linux host ART build.
- [ACL host setup](https://github.com/reveny/Android-Compatibility-Layer/blob/main/tools/setup-host.sh)
  uses a reduced master-art checkout and separate host ART/ICU/SDK steps. Its
  framework/native implementation is a separate project, not a drop-in PadBridge
  dependency. README claims were not treated as independently verified results.
- [Android Translation Layer ART standalone](https://gitlab.com/android_translation_layer/art_standalone)
  uses a different extracted runtime/Bionic compatibility approach; it also needs
  boot libraries and JNI adaptation, not merely an executable copied into /usr/bin.
- [D8](https://developer.android.com/tools/d8) is used in the new integration
  fixtures to compile original Java/Kotlin classes to real DEX before execution.

No complete AOSP host build or ART execution was achieved in this release.
The ART backend is explicitly unavailable. A subsequent backend must provide a
versioned manifest of libart/libcore/ICU/boot artifacts, verified provenance and
licenses, DEX framework generation, JNI loading, class-loading tests and the same
mandatory bubblewrap/network isolation. Enjarify remains the usable backend until
those tests pass; there is no automatic Waydroid fallback inside PadBridge.
