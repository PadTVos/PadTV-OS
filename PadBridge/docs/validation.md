> Historical 0.1 baseline below. Current implementation: [0.5 boundaries](runtime-0.5.md); current test evidence: [PadTV 0.8 validation](https://github.com/PadTVos/PadTV-OS/blob/main/docs/validation-0.8.md).

# Verification record — PadBridge 0.1, PadTV 0.4

Tests run 2026-11-24 on Debian 13 amd64. Linux build uses Debian rustc 1.85.1,
OpenJDK 21, SDL2 and the pinned Cargo.lock. PadBridge's version does not claim
completion of later roadmap milestones.

- Six Rust unit tests cover bounded metadata input and native input/hierarchy helpers.
- Fourteen signed-APK integration tests execute in a QEMU/KVM PadTV guest as an ordinary
  user with bubblewrap. The tests do not skip or disable the sandbox.
- Original APK bytes and signers, tampering, version rollback, different signer,
  private data preservation, removal, DEX arithmetic, Activity, asset image,
  private storage, D-pad click, denied/granted HTTP network access, host path
  isolation and bounded crash recovery are exercised.
- A Leanback-only launcher is detected and run; native ELF machine/dependencies
  are reported, then native execution is rejected. Corrupt installed metadata
  cannot be used to replace the recorded APK signer.
- A real Wayland window displayed the fixture's text and PNG; virtual keyboard
  Enter invoked the APK's Android OnClickListener and changed the text.
- AudioTrack and MediaCodec fixtures verify explicit unsupported diagnostics;
  they **do not** verify sound or video playback.
- Metadata/parser tools and bytecode conversion run inside the sandbox as well.
- The original WSL chroot could not create a user namespace. The runtime failed
  closed; execution testing moved to the guest instead of removing isolation.

No real YouTube or Netflix APK was obtained from an authorized account for this
run. Their compatibility remains untested; missing APIs/native support/DRM are
known blockers, not evidence of a completed playback test. No physical HDMI,
CEC/Bluetooth remote, ARM host, hardware video, HDCP or DRM test was performed.

The PadTV parent repository records ISO boot and installer verification in
`docs/validation-0.4.md`. Its original 108 tests are retained; additional Store
adapter tests validate separation from Waydroid and app identity.
