# Integration outside PadTV

PadBridge uses ordinary Linux processes, Wayland and user data directories. It
does not import PadTV Python modules, contact PadTV servers, require Waydroid,
or require Android system images. A different shell can call the JSON CLI and
render its package inventory itself.

The supported build target is currently Debian 13 amd64 with glibc 2.41. Other
distributions are **not tested**. Build from source against local libraries;
do not copy the Debian binary onto an older glibc. The runtime currently expects
Debian's Java 21 paths, Enjarify Python package, AOSP `aapt`/`apksigner`, bubblewrap
and DejaVu font path. These paths in `runtime.rs`/the renderer must be adapted
and integration tests rerun before claiming support elsewhere.

Install the binary as `/usr/bin/padbridge`, framework JAR, native shared library
and translator under `/usr/lib/padbridge`; package-owned files must not be
writable by apps. `PADBRIDGE_RUNTIME_DIR` is a developer override. Integrators
must provide working user namespaces and a real Wayland socket; execution on
Windows is unsupported. Windows PadTV development preview remains a separate
UI function. ARM Linux builds and Android ARM APK execution are distinct tasks,
neither is verified in this release.
