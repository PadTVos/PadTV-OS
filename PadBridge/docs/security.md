# Isolation and package integrity

The runtime, APK signer/parser tools and translator require bubblewrap Linux
namespaces. They cannot fall back to unconfined execution. Environment variables
are cleared. The app sees read-only system libraries/fonts/certificates, its
read-only package, private `/data`, a new `/tmp`, isolated PID/IPC/UTS namespaces
and minimal `/dev`. Only the selected Wayland socket is passed. No host home,
system bus, PipeWire socket or other app directory is mounted. INTERNET grants
share the host network namespace; otherwise networking stays isolated.

This is a prototype containment model, **not a hardened adversarial sandbox**.
Granted networking includes localhost and the LAN. The host kernel, JVM,
Wayland compositor and file/image parsers remain attack surfaces. Resource
consumption of the app process is not yet fully constrained by per-app cgroups
or syscall filtering. Do not run untrusted APKs on a machine with sensitive
data. Planned work: seccomp, cgroup limits, dedicated portal brokers and
network policy, filesystem symlink adversarial tests and security review.

APKs are bounded by size, file count and expanded entry size; traversal,
duplicate paths and archive symlinks are rejected. AOSP apksigner verifies the
archive before metadata is accepted. Updates require the same signer set and
a greater versionCode (identical reinstall is allowed); key rotation is not
supported. Copying to staging before verification avoids source-file changes
between inspection and installation. `current.json` is replaced atomically.
Global/package file locks prevent concurrent mutation of a running package.

Data defaults to `$XDG_DATA_HOME/padbridge` or `~/.local/share/padbridge`:
`packages/<package>/<sha256>/original.apk`, derived cache and icon;
`data/<package>/`; `permissions/<package>.json`; `logs/<package>.log`.
Uninstall offers preserving or deleting data. No Waydroid directory is touched.
`PADBRIDGE_DATA_HOME` supports isolated host/test instances. Host users can
modify their own files; these checks are not a defense against a compromised
host account or administrator. APK signer identity is not an assertion that an
app is trustworthy, published by Google, or certified.
